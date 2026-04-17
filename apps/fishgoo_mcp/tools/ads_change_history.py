from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from apps.fishgoo_mcp.config import get_settings
from apps.fishgoo_mcp.paths import CHANGE_HISTORY_SCRIPT


def _script_env() -> dict[str, str]:
    settings = get_settings()
    env = os.environ.copy()
    if settings.ads_vendor_path:
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{settings.ads_vendor_path}{os.pathsep}{existing}" if existing else settings.ads_vendor_path
        )
    return env


def run_change_history(
    from_datetime: str,
    to_datetime: str,
    customer_id: str | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    cmd = [
        settings.python_bin,
        str(CHANGE_HISTORY_SCRIPT),
        "--customer-id",
        customer_id or settings.customer_id,
        "--from-datetime",
        from_datetime,
        "--to-datetime",
        to_datetime,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        env=_script_env(),
    )
    return json.loads(proc.stdout)


def summarize_change_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    users = sorted({row.get("change_event.user_email", "") for row in rows if row.get("change_event.user_email")})
    resource_types = sorted(
        {row.get("change_event.change_resource_type", "") for row in rows if row.get("change_event.change_resource_type")}
    )
    return {
        "count": len(rows),
        "users": users,
        "resource_types": resource_types,
        "latest_change_time": rows[0].get("change_event.change_date_time") if rows else None,
    }
