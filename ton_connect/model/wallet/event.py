from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar, Union

from pydantic import Field
from typing_extensions import Literal

from ton_connect.model.error import Error
from ton_connect.model.misc import GenericIntEnum, GenericLiteral
from ton_connect.model.model import BaseModel
from ton_connect.model.wallet.device import Device
from ton_connect.model.wallet.error import ConnectErrorCodes, ConnectItemErrorCodes
from ton_connect.model.wallet.wallet import Account, TonProof

_ReplyItemGeneric = TypeVar("_ReplyItemGeneric", bound="ReplyItem")
_IntEnumGeneric = TypeVar("_IntEnumGeneric", bound=GenericIntEnum)
_MessageType = TypeVar("_MessageType")
_LiteralGeneric = TypeVar("_LiteralGeneric")
_PayloadGeneric = TypeVar("_PayloadGeneric", bound="Payload")


class ConnectReplyItems(str, Enum):
    TON_ADDR = "ton_addr"
    TON_PROOF = "ton_proof"


class WalletEventName(str, Enum):
    CONNECT = "connect"
    CONNECT_ERROR = "connect_error"
    DISCONNECT = "disconnect"


class ReplyItem(BaseModel, Generic[_LiteralGeneric]):
    """Base class for reply items."""

    name: GenericLiteral[_LiteralGeneric] = Field(..., description="Name of the item")


class Payload(BaseModel, Generic[_ReplyItemGeneric]):
    items: List[_ReplyItemGeneric] = Field(..., description="List of reply items")

    def find_item_by_type(self, item_type: type[_ReplyItemGeneric]) -> Optional[_ReplyItemGeneric]:
        """Find item by type."""

        for item in self.items:
            if isinstance(item, item_type):
                return item

        return None


class Event(BaseModel, Generic[_LiteralGeneric, _PayloadGeneric]):
    name: _LiteralGeneric = Field(..., description="Event name", alias="event")
    id: int | None = Field(None, description="Event ID")
    payload: _PayloadGeneric = Field(..., description="Event payload")


ConnectItemError = Error[ConnectItemErrorCodes, Optional[str]]
ConnectEventError = Error[ConnectErrorCodes, str]


class ItemErrorReply(BaseModel):
    error: ConnectItemError = Field(..., description="Error item")


class TonAddressItem(ReplyItem[Literal[ConnectReplyItems.TON_ADDR]], Account):
    pass


class TonProofSuccessItem(ReplyItem[Literal[ConnectReplyItems.TON_PROOF]]):
    proof: TonProof = Field(..., description="Proof of the user's account")


class TonProofFailureItem(ReplyItem[Literal[ConnectReplyItems.TON_PROOF]], ItemErrorReply):
    pass


TonProofItemsType = Union[TonProofSuccessItem, TonProofFailureItem]
ConnectItemsType = Union[TonAddressItem, TonProofItemsType]


class ConnectSuccessPayload(Payload[ConnectItemsType]):
    device: Device = Field(..., description="User's device info")


ConnectSuccessEvent = Event[Literal[WalletEventName.CONNECT], ConnectSuccessPayload]
ConnectErrorEvent = Event[Literal[WalletEventName.CONNECT_ERROR], ConnectEventError]
DisconnectEvent = Event[Literal[WalletEventName.DISCONNECT], dict[str, Any]]

WalletEventType = ConnectSuccessEvent | ConnectErrorEvent | DisconnectEvent
ConnectEventType = ConnectSuccessEvent | ConnectErrorEvent
