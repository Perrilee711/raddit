from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from apps.fishgoo_mcp.config import get_settings
from apps.fishgoo_mcp.memory.readers import read_audit_timeline, read_current_truth, read_overview
from apps.fishgoo_mcp.schemas import ToolResult
from apps.fishgoo_mcp.tools.ads_daily_audit import run_daily_audit, summarize_account_totals


class FishgooMcpBridgeHandler(BaseHTTPRequestHandler):
    server_version = "FishgooMcpBridge/0.1"

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/health":
            self._send(HTTPStatus.OK, {"ok": True, "service": "fishgoo-mcp-bridge"})
            return

        if parsed.path == "/memory/overview":
            self._send(HTTPStatus.OK, read_overview())
            return

        if parsed.path == "/memory/current-truth":
            self._send(HTTPStatus.OK, read_current_truth())
            return

        if parsed.path == "/memory/audit-timeline":
            self._send(HTTPStatus.OK, {"rows": read_audit_timeline()})
            return

        if parsed.path == "/tools/ads-daily-audit":
            date = query.get("date", [""])[0]
            if not date:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    ToolResult(ok=False, message="Missing required query parameter: date").to_dict(),
                )
                return
            payload = run_daily_audit(date)
            result = ToolResult(
                ok=True,
                message=f"Loaded Google Ads daily audit for {date}",
                data={
                    "summary": summarize_account_totals(payload),
                    "raw": payload,
                },
            )
            self._send(HTTPStatus.OK, result.to_dict())
            return

        self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Route not found"})


def main() -> None:
    settings = get_settings()
    server = ThreadingHTTPServer((settings.host, settings.http_bridge_port), FishgooMcpBridgeHandler)
    print(f"Fishgoo MCP bridge listening on http://{settings.host}:{settings.http_bridge_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
