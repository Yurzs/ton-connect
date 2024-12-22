import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from ton_connect.model.response import ResponseError

_GenericResponseError = TypeVar("_GenericResponseError", bound=ResponseError)
_DataType = TypeVar("_DataType")
_ResultGeneric = TypeVar("_ResultGeneric")


class Action(str, Enum):
    SEND_TRANSACTION = "send_transaction"
    SIGN_DATA = "sign_data"
    DISCONNECT = "disconnect"


class WalletResponseError(BaseModel, Generic[_GenericResponseError]):
    id: str = Field(..., description="Event ID")
    error: _GenericResponseError = Field(..., description="Error message")


class SignDataSuccessResponse(BaseModel):
    signature: str = Field(..., description="Signature of the data")
    timestamp: datetime.datetime = Field(..., description="Timestamp of the signature")
