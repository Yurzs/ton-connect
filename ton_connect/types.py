from typing import Annotated

from pydantic import BeforeValidator


def validated_hex_string(v: str | bytes) -> bytes:
    if isinstance(v, bytes):
        return v

    return bytes.fromhex(v)


HexBytes = Annotated[bytes, BeforeValidator(validated_hex_string)]
