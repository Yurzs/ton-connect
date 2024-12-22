from enum import IntEnum


class ConnectErrorCodes(IntEnum):
    UNKNOWN_ERROR = 0
    BAD_REQUEST_ERROR = 1
    MANIFEST_NOT_FOUND_ERROR = 2
    MANIFEST_CONTENT_ERROR = 3
    UNKNOWN_APP_ERROR = 100
    USER_REJECTS_ERROR = 300
    METHOD_NOT_SUPPORTED = 400


class ConnectItemErrorCodes(IntEnum):
    UNKNOWN_ERROR = 0
    METHOD_NOT_SUPPORTED = 400
