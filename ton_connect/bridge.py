import asyncio
import logging
import re
from functools import cached_property
from typing import Annotated, Any, Awaitable, Callable, Literal
from urllib.parse import quote_plus

import httpx
import httpx_sse
import pydantic
from httpx_sse import ServerSentEvent
from nacl.exceptions import CryptoError
from pydantic import AnyUrl, Base64Bytes, Field, HttpUrl, ValidationError

from ton_connect.crypto import SessionCrypto
from ton_connect.misc import encode_telegram_url_parameters
from ton_connect.model.app.request import AppRequest, ConnectRequest
from ton_connect.model.app.response import AppResponses
from ton_connect.model.model import BaseModel
from ton_connect.model.wallet.event import ConnectEventType, WalletEventType
from ton_connect.types import HexBytes

LOG = logging.getLogger(__name__)


class Session(BaseModel):
    private_key: HexBytes = Field(..., description="Session private key")
    wallet_key: HexBytes | None = Field(None, description="Wallet public key")
    bridge_url: str = Field(..., description="Bridge URL")


class Connection(BaseModel):
    session: Session = Field(..., description="Session")
    source: str = Field(..., description="Source of the connection")
    next_rpc_request_id: int = Field(0, description="Next RPC request ID")
    next_event_id: int | None = Field(None, description="Next event ID")
    last_wallet_event_id: int | None = Field(None, description="Last wallet event ID")
    last_rpc_event_id: int | None = Field(None, description="Last RPC event ID")
    connect_event: ConnectEventType | None = Field(None, description="Connect event")


class WalletMessageEvent(BaseModel):
    sender: HexBytes = Field(..., description="Sender public key", alias="from")
    message: Base64Bytes = Field(..., description="Encrypted message")


class BridgeMessage(BaseModel):
    event: Literal["heartbeat", "stopped"] | WalletEventType | AppResponses = Field(
        ..., description="Wallet event"
    )
    app_name: str = Field(..., description="Wallet app name")
    source: HexBytes = Field(..., description="Source of the message")


class Bridge:
    VERSION: int = 2
    """Bridge API version."""

    UNIVERSAL_URL: str = "tc://"
    """Universal URL for the bridge."""

    TIMEOUT: int = 600
    """Timeout for the connection."""

    PATH_MESSAGE: str = "message"
    """Path to the message endpoint."""

    PATH_EVENTS: str = "events"
    """Path to the events endpoint."""

    TTL: int = 300
    """Time to live for the request."""

    @property
    def request_headers(self) -> dict[str, str]:
        """Request headers for the bridge."""

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def __init__(
        self,
        app_name: str,
        queue: asyncio.Queue[BridgeMessage],
        connector_ready: asyncio.Event,
        bridge_url: Annotated[str, HttpUrl] | None = None,
        universal_url: Annotated[str, AnyUrl] | None = None,
        private_key: str | None = None,
        last_rpc_event_id: int | None = None,
    ) -> None:
        self.app_name = app_name
        self.queue = queue
        self.bridge_url = bridge_url
        self.universal_url = universal_url or self.UNIVERSAL_URL
        self.crypto: SessionCrypto = SessionCrypto(private_key=private_key)

        self.connected: asyncio.Event = asyncio.Event()
        self.connector_ready: asyncio.Event = connector_ready
        self.listener: asyncio.Task[Callable[[str], Awaitable[None]]] | None = None

        self.pulse_listener: asyncio.Task[None] | None = None

        self.last_rpc_event_id: str | None = last_rpc_event_id
        self.stop = asyncio.Event()

    @property
    def is_alive(self) -> bool:
        """Check if the bridge is alive."""

        return not self.listener.done() and not self.listener.cancelled()

    @cached_property
    def type_adapter(self) -> pydantic.TypeAdapter:
        return pydantic.TypeAdapter[AppResponses | WalletEventType](AppResponses | WalletEventType)

    def reset_crypto(self) -> None:
        """Reset crypto session."""

        self.crypto = SessionCrypto()

    @staticmethod
    def generate_basic_connect_url(
        request: ConnectRequest,
        session_id: str,
        version: int = VERSION,
        universal_url: str = UNIVERSAL_URL,
    ) -> Annotated[str, AnyUrl]:
        """Generate basic URL for the bridge."""

        params = quote_plus(request.model_dump_json(by_alias=True, exclude_none=True))

        universal_url = universal_url.rstrip("/")
        return f"{universal_url}?v={version}&id={session_id}&r={params}&ret=back"

    @staticmethod
    def convert_to_direct_link(url: str) -> str:
        """Convert universal URL to direct link."""

        if "attach=" in url:
            # remove attach query param and its value from url
            url = re.sub(r"attach=[^&]+", "", url)

            # add /start to url path
            url = re.sub(r"(\?|&)", "/start?", url)

        return url

    def generate_connect_url(
        self,
        request: ConnectRequest,
        session_id: str,
    ) -> Annotated[str, AnyUrl]:
        """Generate URL for the bridge."""

        universal_url = self.universal_url

        telegram_url = r"^(http[s]?://)?t.me/(\w+)"

        if universal_url.startswith("tg://") or re.match(telegram_url, universal_url):
            basic_url = self.generate_basic_connect_url(
                request,
                session_id,
                universal_url="",
            )

            universal_url = self.convert_to_direct_link(self.universal_url)

            params = basic_url.split("?")[1]
            start_command = f"tonconnect-{encode_telegram_url_parameters(params)}"

            if universal_url.endswith("?"):
                return f"{universal_url}startapp={start_command}"

            return f"{universal_url}&startapp={start_command}"

        return self.generate_basic_connect_url(request, session_id, universal_url=universal_url)

    async def connect(self, request: ConnectRequest) -> Annotated[str, AnyUrl]:
        """Send request to connect to the wallet via the bridge."""

        await self.disconnect(send_event=False)
        self.reset_crypto()

        return self.generate_connect_url(request, self.crypto.public_key)

    async def disconnect(self, send_event: bool = True) -> None:
        """DisconnectEvent from the wallet."""

        if self.listener is not None:
            if send_event:
                await self.queue.put(
                    BridgeMessage(
                        event="stopped",
                        app_name=self.app_name,
                        source=b"",
                    )
                )
            self.listener.cancel()

    async def send_request(
        self,
        request: AppRequest,
        wallet_app_key: HexBytes,
        ttl: int | None = None,
        timeout: int = 5,
    ) -> dict[str, Any]:
        """Send request to the wallet."""

        url = (
            f"{self.bridge_url}/{self.PATH_MESSAGE}?"
            f"client_id={self.crypto.public_key}"
            f"&to={wallet_app_key.hex()}"
            f"&ttl={ttl or self.TTL}"
            f"&topic={request.method.value}"
        )

        data = self.crypto.encrypt(
            request.model_dump(
                by_alias=True,
                exclude_none=True,
            ),
            wallet_app_key.hex(),
        )

        async with httpx.AsyncClient(headers=self.request_headers) as client:
            response = await client.post(
                url,
                content=data,
                timeout=timeout,
            )
            LOG.info(
                "Sent request %s to the wallet: %s (%s)",
                request.id,
                request.method,
                request,
            )
            return response.json()

    def parse_message(self, event: ServerSentEvent) -> BridgeMessage | None:
        """Parse message from the wallet bridge."""

        try:
            wallet_message_event = WalletMessageEvent.model_validate_json(event.data, strict=True)
        except ValidationError:
            LOG.error("Wallet message validation error: %s", event.data)
            return None

        try:
            decoded_data = self.crypto.decrypt(
                wallet_message_event.message, wallet_message_event.sender
            )
        except CryptoError:
            LOG.error("Wallet message data decryption error")
            return None

        try:
            wallet_event = self.type_adapter.validate_json(decoded_data)
        except ValidationError as e:
            LOG.error("Wallet event validation error: %s", e)
            LOG.error("Wallet event data: %s", decoded_data)
            return None

        return BridgeMessage(
            event=wallet_event,
            app_name=self.app_name,
            source=wallet_message_event.sender,
        )

    def handle_event(self, event: ServerSentEvent) -> None:
        """Handle event."""

        self.last_rpc_event_id = event.id
        message = self.parse_message(event)

        if message:
            asyncio.create_task(self.queue.put(message))
            LOG.debug("Sent message to the queue: %s", message)

    def handle_error(self, event: ServerSentEvent) -> None:
        LOG.error("Bridge connection error: %s", event)

    async def listen(self) -> None:
        """Listen for events from the bridge SSE."""

        LOG.debug("Starting Bridge listening for events: %s", self.app_name)

        iteration_task: asyncio.Task | None = None

        while not self.stop.is_set():
            async with httpx.AsyncClient(timeout=None) as client:
                try:
                    url = self.generate_url()
                    async with httpx_sse.aconnect_sse(client, "GET", url) as event_source:
                        self.connected.set()
                        LOG.info("Bridge connected: %s", self.app_name)

                        await self.connector_ready.wait()

                        async for message in event_source.aiter_sse():
                            match message.event:
                                case "heartbeat":
                                    await self.queue.put(
                                        BridgeMessage(
                                            event="heartbeat",
                                            app_name=self.app_name,
                                            source=b"",
                                        )
                                    )
                                case "error":
                                    self.handle_error(message)
                                case _:
                                    self.handle_event(message)

                except asyncio.CancelledError:
                    iteration_task.cancel()
                    self.stop.set()
                    LOG.info("Bridge listener for %s is cancelled.", self.app_name)
                    return
                except TimeoutError:
                    LOG.error("Bridge connection timeout")
                except Exception as e:
                    LOG.exception("Bridge connection unhandled error: %s", e)
                finally:
                    self.connected.clear()
                    if not self.stop.is_set():
                        LOG.info("Retrying Bridge connection in 1 second...")
                        await asyncio.sleep(1)

    def generate_url(self) -> str:
        """Generate URL for the bridge."""

        url = f"{self.bridge_url}/{self.PATH_EVENTS}?client_id={self.crypto.public_key}"

        if self.last_rpc_event_id is not None:
            url += f"&last_event_id={self.last_rpc_event_id}"

        return url

    async def register_session(self) -> None:
        """Register session with the bridge."""

        self.listener = asyncio.create_task(self.listen(), name="BridgeListener")
