import logging
from enum import Enum, IntEnum
from typing import Optional

from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey
from pydantic import Base64Bytes, BaseModel, Field

from ton_connect.types import HexBytes

LOG = logging.getLogger(__name__)


class Chain(IntEnum):
    MAINNET = "-239"
    TESTNET = "-3"


class Address(str):
    """TON wallet address."""

    @property
    def work_chain(self) -> str:
        return self.split(":", 1)[-1]

    @property
    def hash(self) -> str:
        return self.split(":", 2)[-1]


class Account(BaseModel):
    """User's wallet account."""

    address: str = Field(..., description="User's address. Format: <wc>:<hex>")
    chain: Chain = Field(..., description="Network chain", alias="network")
    wallet_state_init: str = Field(
        ...,
        description="Wallet contract state_init",
        alias="walletStateInit",
    )
    public_key: Optional[HexBytes] = Field(
        None,
        description="Public private_key of the user's account",
        alias="publicKey",
    )


class Provider(str, Enum):
    HTTP = "http"


class Wallet(BaseModel):
    """Information about user's wallet."""

    provider: Provider = Field(..., description="Type of the provider")
    account: Account = Field(..., description="User's account", alias="ton_addr")


class TonProofDomain(BaseModel):
    len: int = Field(..., description="Length of the domain", alias="lengthBytes")
    val: str = Field(..., description="Value of the domain", alias="value")


class TonProof(BaseModel):
    timestamp: int = Field(..., description="Timestamp of the proof")
    domain: TonProofDomain = Field(..., description="Domain of the proof")
    payload: str = Field(..., description="Payload of the proof")
    signature: Base64Bytes = Field(..., description="Signature of the proof")

    def verify(self, public_key: bytes) -> bool:
        """Verify proof signature."""

        try:
            verify_key = VerifyKey(public_key, encoder=HexEncoder)
            verify_key.verify(
                f"{self.timestamp}{self.domain.len}{self.domain.val}{self.payload}".encode(),
                self.signature,
            )
            return True
        except Exception as e:
            LOG.error("Failed to verify proof signature: %s", e)
            return False
