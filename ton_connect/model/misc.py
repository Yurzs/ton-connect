from enum import IntEnum
from typing import Literal, TypeVar

from typing_extensions import Annotated, TypeAliasType

T = TypeVar("T")

GenericIntEnum = TypeAliasType("GenericIntEnum", Annotated[IntEnum, T], type_params=(T,))
GenericLiteral = TypeAliasType("GenericLiteral", Literal[T], type_params=(T,))  # type:ignore[valid-type]
