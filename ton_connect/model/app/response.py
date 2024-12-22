from typing import Any, Optional

from ton_connect.model.app.error import (
    AppResponseError,
    DisconnectErrorCode,
    SignDataErrorCode,
    TransactionErrorCode,
)
from ton_connect.model.response import ResponseError, ResponseSuccess
from ton_connect.model.wallet.response import SignDataSuccessResponse

SendTransactionResponseError = AppResponseError[
    ResponseError[TransactionErrorCode, str, Optional[Any]]
]

SendTransactionSuccess = ResponseSuccess[str]
DisconnectResponseError = AppResponseError[ResponseError[DisconnectErrorCode, str, Optional[Any]]]
SignDataResponseError = AppResponseError[ResponseError[SignDataErrorCode, str, Optional[Any]]]
SignDataSuccess = ResponseSuccess[SignDataSuccessResponse]

AppResponses = (
    SendTransactionResponseError
    | SendTransactionSuccess
    | DisconnectResponseError
    | SignDataResponseError
    | SignDataSuccess
)
