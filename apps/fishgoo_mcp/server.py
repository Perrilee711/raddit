from __future__ import annotations

import json

from apps.fishgoo_mcp.config import get_settings
from apps.fishgoo_mcp.memory.readers import read_audit_timeline, read_current_truth, read_overview
from apps.fishgoo_mcp.tools.ads_change_history import run_change_history, summarize_change_events
from apps.fishgoo_mcp.tools.ads_daily_audit import run_daily_audit, summarize_account_totals

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - runtime dependency path
    raise RuntimeError(
        "The 'mcp' Python package is required to run apps/fishgoo_mcp/server.py. "
        "Install apps/fishgoo_mcp/requirements.txt first."
    ) from exc


settings = get_settings()
mcp = FastMCP("Fishgoo Ads OS MCP")


@mcp.tool(name="ads_daily_audit")
def ads_daily_audit(date: str, customer_id: str | None = None) -> dict:
    payload = run_daily_audit(date, customer_id=customer_id)
    return {
        "summary": summarize_account_totals(payload),
        "raw": payload,
    }


@mcp.tool(name="ads_change_history")
def ads_change_history(
    from_datetime: str,
    to_datetime: str,
    customer_id: str | None = None,
) -> dict:
    rows = run_change_history(from_datetime, to_datetime, customer_id=customer_id)
    return {
        "summary": summarize_change_events(rows),
        "rows": rows,
    }


@mcp.resource("project://overview")
def project_overview() -> str:
    return json.dumps(read_overview(), ensure_ascii=False, indent=2)


@mcp.resource("project://current-truth")
def current_truth() -> str:
    return json.dumps(read_current_truth(), ensure_ascii=False, indent=2)


@mcp.resource("project://audit-timeline")
def audit_timeline() -> str:
    return json.dumps({"rows": read_audit_timeline()}, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
