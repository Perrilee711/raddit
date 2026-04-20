from __future__ import annotations

import json
import os
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest import mock

from apps.fishgoo_mcp.bridge.app import FishgooMcpBridgeHandler


TEST_TOKEN = "test-token-abc123"


class BridgeAuthTests(unittest.TestCase):
    """Verify Bearer auth enforcement on the HTTP bridge."""

    def setUp(self) -> None:
        self._env_patch = mock.patch.dict(os.environ, {"FISHGOO_MCP_AUTH_TOKEN": TEST_TOKEN})
        self._env_patch.start()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FishgooMcpBridgeHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.1)
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
        self._env_patch.stop()

    def _request(self, path: str, headers: dict | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", path, headers=headers or {})
        response = conn.getresponse()
        raw = response.read()
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            body = {}
        return response.status, body

    def test_health_is_public_without_token(self) -> None:
        status, body = self._request("/health")
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))

    def test_memory_overview_requires_bearer(self) -> None:
        status, body = self._request("/memory/overview")
        self.assertEqual(status, 401)
        self.assertEqual(body.get("message"), "missing_bearer")

    def test_memory_overview_rejects_wrong_token(self) -> None:
        status, body = self._request(
            "/memory/overview",
            headers={"Authorization": "Bearer wrong-token"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(body.get("message"), "invalid_token")

    def test_memory_overview_accepts_correct_token(self) -> None:
        status, _body = self._request(
            "/memory/overview",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        # 200 if memory projection exists; any 2xx counts as "passed auth".
        self.assertLess(status, 400, msg=f"Expected 2xx after auth, got {status}")


class BridgeAuthDisabledTests(unittest.TestCase):
    """When FISHGOO_MCP_AUTH_TOKEN is empty, bridge stays open (dev mode)."""

    def setUp(self) -> None:
        self._env_patch = mock.patch.dict(os.environ, {"FISHGOO_MCP_AUTH_TOKEN": ""})
        self._env_patch.start()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FishgooMcpBridgeHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.1)
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
        self._env_patch.stop()

    def test_memory_overview_open_without_token_when_auth_disabled(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", "/memory/overview")
        response = conn.getresponse()
        response.read()
        self.assertLess(response.status, 400)


if __name__ == "__main__":
    unittest.main()
