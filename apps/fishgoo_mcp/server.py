from __future__ import annotations

import json
import logging

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

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "The 'starlette' package is required. It ships with 'mcp', "
        "but ensure apps/fishgoo_mcp/requirements.txt is installed."
    ) from exc


logger = logging.getLogger(__name__)
settings = get_settings()
mcp = FastMCP(
    "Fishgoo Ads OS MCP",
    host=settings.host,
    port=settings.port,
    streamable_http_path="/mcp",
    stateless_http=True,
    log_level=settings.log_level,
)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Require ``Authorization: Bearer <token>`` on every request."""

    def __init__(self, app, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next):
        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            return JSONResponse({"ok": False, "error": "missing_bearer"}, status_code=401)
        presented = header.split(" ", 1)[1].strip()
        if presented != self._token:
            return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=401)
        return await call_next(request)


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


def build_app():
    """Return the Starlette ASGI app with Bearer auth attached when configured."""
    app = mcp.streamable_http_app()
    if settings.auth_token:
        app.add_middleware(BearerAuthMiddleware, token=settings.auth_token)
    else:
        logger.warning(
            "FISHGOO_MCP_AUTH_TOKEN is empty - MCP server starting WITHOUT auth. "
            "Do not expose to the public network in this mode."
        )
    return app


def main() -> None:
    import uvicorn

    uvicorn.run(
        build_app(),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
