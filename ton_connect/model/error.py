from typing import Generic, TypeVar

from pydantic import Field

from ton_connect.model.misc import GenericIntEnum
from ton_connect.model.model import BaseModel

_IntEnumGeneric = TypeVar("_IntEnumGeneric", bound=GenericIntEnum)
_MessageType = TypeVar("_MessageType")


class Error(BaseModel, Generic[_IntEnumGeneric, _MessageType]):
    """Base class for error items."""

    code: _IntEnumGeneric = Field(..., description="Error code")
    message: _MessageType = Field(None, description="Error message")
