from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from ton_connect.model.response import ResponseError

_GenericResponseError = TypeVar("_GenericResponseError", bound=ResponseError)


class TransactionErrorCode(IntEnum):
    UNKNOWN_ERROR = 0
    BAD_REQUEST_ERROR = 1
    UNKNOWN_APP_ERROR = 100
    USER_REJECTS_ERROR = 300
    METHOD_NOT_SUPPORTED = 400


class DisconnectErrorCode(IntEnum):
    UNKNOWN_ERROR = 0
    BAD_REQUEST_ERROR = 1
    UNKNOWN_APP_ERROR = 100
    METHOD_NOT_SUPPORTED = 400


class SignDataErrorCode(IntEnum):
    UNKNOWN_ERROR = 0
    BAD_REQUEST_ERROR = 1
    UNKNOWN_APP_ERROR = 100
    USER_REJECTS_ERROR = 300
    METHOD_NOT_SUPPORTED = 400


class AppResponseError(BaseModel, Generic[_GenericResponseError]):
    id: str = Field(..., description="Event ID")
    error: _GenericResponseError = Field(..., description="Error message")
