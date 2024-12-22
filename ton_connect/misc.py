import ssl
from typing import AsyncIterator, TypeVar

import certifi
from aiohttp import ClientConnectionError

R = TypeVar("R")

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def encode_telegram_url_parameters(parameters: str) -> str:
    """Format bot command url."""

    return (
        parameters.replace(".", "%2E")
        .replace("-", "%2D")
        .replace("_", "%5F")
        .replace("&", "-")
        .replace("=", "__")
        .replace("%", "--")
        .replace("+", "")
    )


async def iterate_event_source(iterator: AsyncIterator) -> None:
    try:
        async for _ in iterator:
            pass
    except ClientConnectionError:
        pass
