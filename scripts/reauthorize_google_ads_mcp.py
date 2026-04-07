#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import subprocess
import shutil
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPE = "https://www.googleapis.com/auth/adwords"


def load_claude_config() -> tuple[Path, dict]:
    path = Path.home() / ".claude.json"
    return path, json.loads(path.read_text())


def load_mcp_env() -> dict:
    _, cfg = load_claude_config()
    return cfg["mcpServers"]["google-ads-mcp"]["env"]


def backup_file(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-google-ads-reauth-{stamp}")
    shutil.copy2(path, backup)
    return backup


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def open_in_chrome(url: str) -> None:
    subprocess.run(
        ["/usr/bin/open", "-a", "Google Chrome", url],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_auth_code(port: int) -> str:
    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        code: str | None = None
        error: str | None = None

        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            OAuthCallbackHandler.code = params.get("code", [None])[0]
            OAuthCallbackHandler.error = params.get("error", [None])[0]

            if OAuthCallbackHandler.code:
                body = (
                    "<html><body><h1>Google Ads MCP 已重新授权</h1>"
                    "<p>可以关闭这个窗口并回到 Codex。</p></body></html>"
                )
                self.send_response(200)
            else:
                body = (
                    "<html><body><h1>授权未完成</h1>"
                    "<p>请回到 Codex 查看错误提示。</p></body></html>"
                )
                self.send_response(400)

            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

        def log_message(self, format, *args):  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
    server.handle_request()

    if OAuthCallbackHandler.error:
        raise SystemExit(f"Google 授权返回错误: {OAuthCallbackHandler.error}")
    if not OAuthCallbackHandler.code:
        raise SystemExit("没有收到授权 code，请重新运行授权。")
    return OAuthCallbackHandler.code


def run_oauth_flow(client_id: str, client_secret: str):
    port = find_free_port()
    redirect_uri = f"http://127.0.0.1:{port}/"
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=[SCOPE],
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    print("Google Ads MCP 重新授权即将开始。")
    print("浏览器会自动打开；如果没有自动打开，请复制下面链接到 Chrome：")
    print(auth_url)
    open_in_chrome(auth_url)
    code = wait_for_auth_code(port)
    flow.fetch_token(code=code)
    return flow.credentials


def update_claude_config(refresh_token: str) -> tuple[Path, Path]:
    path, cfg = load_claude_config()
    backup = backup_file(path)
    cfg["mcpServers"]["google-ads-mcp"]["env"]["GOOGLE_ADS_REFRESH_TOKEN"] = refresh_token
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    return path, backup


def update_credentials_file(refresh_token: str, client_id: str, client_secret: str) -> tuple[Path, Path]:
    path = Path.home() / ".config/google-ads-mcp/credentials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_file(path) if path.exists() else None
    payload = {
        "type": "authorized_user",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return path, backup


def main() -> int:
    env = load_mcp_env()
    creds = run_oauth_flow(
        client_id=env["GOOGLE_ADS_CLIENT_ID"],
        client_secret=env["GOOGLE_ADS_CLIENT_SECRET"],
    )

    if not creds.refresh_token:
        raise SystemExit(
            "OAuth 授权已完成，但没有拿到新的 refresh token。"
            "请确认授权页使用了 consent 模式，并且 Google 账号有 Ads 权限。"
        )

    claude_path, claude_backup = update_claude_config(creds.refresh_token)
    credentials_path, credentials_backup = update_credentials_file(
        refresh_token=creds.refresh_token,
        client_id=env["GOOGLE_ADS_CLIENT_ID"],
        client_secret=env["GOOGLE_ADS_CLIENT_SECRET"],
    )

    print("Google Ads MCP 重新授权成功。")
    print(f"已更新: {claude_path}")
    print(f"备份: {claude_backup}")
    print(f"已更新: {credentials_path}")
    if credentials_backup:
        print(f"备份: {credentials_backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
