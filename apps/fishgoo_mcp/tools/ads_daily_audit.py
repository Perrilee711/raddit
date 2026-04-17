from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from apps.fishgoo_mcp.config import get_settings
from apps.fishgoo_mcp.paths import DAILY_AUDIT_SCRIPT


def _script_env() -> dict[str, str]:
    settings = get_settings()
    env = os.environ.copy()
    if settings.ads_vendor_path:
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{settings.ads_vendor_path}{os.pathsep}{existing}" if existing else settings.ads_vendor_path
        )
    return env


def run_daily_audit(date: str, customer_id: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    cmd = [
        settings.python_bin,
        str(DAILY_AUDIT_SCRIPT),
        "--date",
        date,
        "--customer-id",
        customer_id or settings.customer_id,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        env=_script_env(),
    )
    return json.loads(proc.stdout)


def summarize_account_totals(payload: dict[str, Any]) -> dict[str, Any]:
    account = (payload.get("account_today") or [{}])[0]
    return {
        "date": payload.get("date"),
        "customer_id": payload.get("customer_id"),
        "impressions": account.get("metrics.impressions", 0),
        "clicks": account.get("metrics.clicks", 0),
        "cost_micros": account.get("metrics.cost_micros", 0),
        "conversions": account.get("metrics.conversions", 0),
    }
