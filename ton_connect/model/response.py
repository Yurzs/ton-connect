from typing import Generic, TypeVar

from pydantic import Field

from ton_connect.model.error import Error, _IntEnumGeneric, _MessageType
from ton_connect.model.model import BaseModel

_GenericResponseError = TypeVar("_GenericResponseError", bound="ResponseError")
_DataType = TypeVar("_DataType")
_ResultGeneric = TypeVar("_ResultGeneric")


class ResponseSuccess(BaseModel, Generic[_ResultGeneric]):
    id: int = Field(..., description="Event ID")
    result: _ResultGeneric = Field(..., description="Result of the action")


class ResponseError(
    Error[_IntEnumGeneric, _MessageType],
    Generic[_IntEnumGeneric, _MessageType, _DataType],
):
    data: _DataType = Field(None, description="Error data")
