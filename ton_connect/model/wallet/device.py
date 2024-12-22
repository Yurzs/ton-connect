from typing import Generic, List, Literal, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from ton_connect.model.misc import GenericLiteral

_FeatureName = TypeVar("_FeatureName")


class Feature(BaseModel, Generic[_FeatureName]):
    model_config = ConfigDict(extra="allow")

    name: GenericLiteral[_FeatureName] = Field(..., description="Name of the feature")


class SendTransactionFeature(Feature[Literal["SendTransaction"]]):
    max_messages: PositiveInt = Field(
        ..., description="Max number of messages", alias="maxMessages"
    )


SignDataFeature = Feature[Literal["SignData"]]

FeatureType = Union[SendTransactionFeature, SignDataFeature, str]


class Device(BaseModel):
    """User's device info."""

    platform: str = Field(..., description="Platform of the user's device")
    app_name: str = Field(..., description="Name of the user's wallet app", alias="appName")
    app_version: str = Field(
        ..., description="Version of the user's wallet app", alias="appVersion"
    )
    max_protocol_version: int = Field(
        ...,
        description="Max protocol version of the user's wallet app",
        alias="maxProtocolVersion",
    )
    features: List[FeatureType] = Field(
        ..., description="List of features of the user's wallet app"
    )
