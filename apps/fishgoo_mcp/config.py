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
    host: str
    port: int
    http_bridge_port: int
    customer_id: str
    python_bin: str
    ads_vendor_path: str
    enable_publish: bool
    log_level: str
    auth_token: str

    @property
    def require_auth(self) -> bool:
        return bool(self.auth_token)


def get_settings() -> Settings:
    """Return a Settings instance freshly derived from the current environment.

    Reading env inside this function (rather than via dataclass defaults) lets
    tests patch `os.environ` and also makes token rotation visible to the bridge
    without a process restart (systemd still reloads EnvironmentFile at restart).
    """
    return Settings(
        host=os.environ.get("FISHGOO_MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("FISHGOO_MCP_PORT", "8766")),
        http_bridge_port=int(os.environ.get("FISHGOO_MCP_HTTP_PORT", "8767")),
        customer_id=os.environ.get("FISHGOO_GOOGLE_ADS_CUSTOMER_ID", "1573113113"),
        python_bin=os.environ.get("FISHGOO_PYTHON_BIN", "/usr/bin/python3"),
        ads_vendor_path=os.environ.get("FISHGOO_ADS_VENDOR_PATH", ""),
        enable_publish=_bool_env("FISHGOO_MCP_ENABLE_PUBLISH", False),
        log_level=os.environ.get("FISHGOO_MCP_LOG_LEVEL", "INFO"),
        auth_token=os.environ.get("FISHGOO_MCP_AUTH_TOKEN", ""),
    )
