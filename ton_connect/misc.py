from typing import TypeVar

R = TypeVar("R")


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
