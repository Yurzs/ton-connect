from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, ClassVar, Generic, List, Literal, TypeVar

from pydantic import Field, computed_field, Base64Str
from pydantic.main import IncEx

from ton_connect.model.model import BaseModel

_Method = TypeVar("_Method")


class Method(str, Enum):
    SEND_TRANSACTION = "sendTransaction"
    SIGN_DATA = "signData"
    DISCONNECT = "disconnect"


class AppRequest(BaseModel, Generic[_Method]):
    """Base class for request items."""

    PARAMETERS: ClassVar[list[str]] = []

    method: _Method = Field(..., description="Method name")
    id: int | None = Field(None, description="Event ID")

    @computed_field
    def params(self) -> List[str]:
        return [
            super().model_dump_json(
                include={param for param in self.PARAMETERS},
                by_alias=True,
                exclude_none=True,
            )
        ]

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: dict[str, Any] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        return super().model_dump(
            mode=mode,
            include={"id", "method", "params"},
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            exclude_unset=exclude_unset,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )


class SignDataParams(BaseModel):
    schema_crc: int = Field(..., description="Schema version", alias="schema_crc")
    cell: str = Field(..., description="Cell to sign")


class SendTransactionMessage(BaseModel):
    address: str = Field(..., description="Address")
    amount: str = Field(..., description="Amount")
    payload: Base64Str | None = Field(None, description="Payload")


class SendTransactionRequest(AppRequest[Literal[Method.SEND_TRANSACTION]]):
    PARAMETERS = ["valid_until", "address", "network", "messages"]

    method: Literal[Method.SEND_TRANSACTION] = Method.SEND_TRANSACTION
    valid_until: int = Field(
        default_factory=lambda: int((datetime.now() + timedelta(minutes=30)).timestamp()),
        description="Request expiration time",
    )
    address: str = Field(..., description="Address", alias="from")
    network: int = Field(..., description="Network id")
    messages: List[SendTransactionMessage] = Field(..., description="List of messages")


class SignDataRequest(AppRequest[Literal[Method.SIGN_DATA]]):
    method: Literal[Method.SIGN_DATA] = Method.SIGN_DATA


class DisconnectRequest(AppRequest[Literal[Method.DISCONNECT]]):
    method: Literal[Method.DISCONNECT] = Method.DISCONNECT


class TonAddressRequestItem(BaseModel):
    name: Literal["ton_addr"] = Field("ton_addr", description="Name of the item", init=False)


class TonProofRequestItem(BaseModel):
    name: Literal["ton_proof"] = Field(
        "ton_proof",
        description="Name of the item",
        init=False,
    )
    payload: str = Field(..., description="TON proof payload")


class ConnectRequest(BaseModel):
    method: ClassVar[str] = "connect"

    manifest_url: Annotated[
        str,
        Field(..., description="URL to manifest", alias="manifestUrl"),
    ]
    items: list[TonAddressRequestItem | TonProofRequestItem] = Field(
        default_factory=list,
        description="List of items",
    )


AppRequestType = DisconnectRequest | SendTransactionRequest | SignDataRequest
