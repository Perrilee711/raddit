from __future__ import annotations

import json
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from apps.fishgoo_mcp.bridge.app import FishgooMcpBridgeHandler


class BridgeSmokeTests(unittest.TestCase):
    def test_health_endpoint_returns_ok(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FishgooMcpBridgeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
        conn.request("GET", "/health")
        response = conn.getresponse()
        body = json.loads(response.read().decode("utf-8"))

        server.shutdown()
        server.server_close()
        thread.join(timeout=1)

        self.assertEqual(response.status, 200)
        self.assertTrue(body["ok"])


if __name__ == "__main__":
    unittest.main()
