from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    host: str = os.environ.get("FISHGOO_MCP_HOST", "0.0.0.0")
    port: int = int(os.environ.get("FISHGOO_MCP_PORT", "8766"))
    http_bridge_port: int = int(os.environ.get("FISHGOO_MCP_HTTP_PORT", "8767"))
    customer_id: str = os.environ.get("FISHGOO_GOOGLE_ADS_CUSTOMER_ID", "1573113113")
    python_bin: str = os.environ.get("FISHGOO_PYTHON_BIN", "/usr/bin/python3")
    ads_vendor_path: str = os.environ.get("FISHGOO_ADS_VENDOR_PATH", "")
    enable_publish: bool = _bool_env("FISHGOO_MCP_ENABLE_PUBLISH", False)
    log_level: str = os.environ.get("FISHGOO_MCP_LOG_LEVEL", "INFO")
    auth_token: str = os.environ.get("FISHGOO_MCP_AUTH_TOKEN", "")


def get_settings() -> Settings:
    return Settings()
