from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class BridgeType(str, Enum):
    SSE = "sse"
    JS = "js"


class WalletBridge(BaseModel):
    type: BridgeType = Field(description="Type of the bridge")
    url: Optional[str] = Field(None, description="URL to the bridge. Present if type is SSE")
    key: Optional[str] = Field(None, description="Key to the bridge. Present if type is JS")

    @field_validator("url", mode="before")
    @classmethod
    def validate_sse_url(cls, v: str, validation_info: ValidationInfo) -> str:
        if validation_info.data["type"] == BridgeType.SSE and not v:
            raise ValueError("URL is required for SSE bridge")
        return v

    @field_validator("key", mode="before")
    @classmethod
    def validate_js_key(cls, v: str, validation_info: ValidationInfo) -> str:
        if validation_info.data["type"] == BridgeType.JS and not v:
            raise ValueError("Key is required for JS bridge")
        return v


class WalletApp(BaseModel):
    app_name: str = Field(description="Internal name of the wallet")
    name: str = Field(description="Name of the wallet")
    image: str = Field(description="Image of the wallet logo")
    dns: Optional[str] = Field(None, description="TON DNS of the wallet", alias="tondns")
    about_url: str = Field(description="URL to the wallet description")
    universal_url: Optional[str] = Field(None, description="URL to the wallet app")
    bridge: List[WalletBridge] = Field(description="List of bridges")
    deep_link: Optional[str] = Field(None, description="Deep link to the wallet", alias="deepLink")
    platforms: List[str] = Field(default_factory=list, description="List of supported platforms")

    @property
    def bridge_url(self) -> Optional[str]:
        """Gets SSE bridge url if available."""

        for bridge in self.bridge:
            if bridge.type == BridgeType.SSE:
                return bridge.url

        return None

    @property
    def is_supported(self) -> bool:
        """Check if wallet is supported."""

        return self.universal_url is not None or self.bridge_url is not None
