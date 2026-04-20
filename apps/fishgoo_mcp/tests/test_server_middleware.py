from __future__ import annotations

import os
import unittest
from unittest import mock

try:
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient
    _STARLETTE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _STARLETTE_AVAILABLE = False


TEST_TOKEN = "server-test-token-xyz"


def _dummy_endpoint(request):
    return JSONResponse({"ok": True})


def _make_app_with_bearer(token: str):
    """Build a minimal Starlette app with our BearerAuthMiddleware attached.

    We don't import `build_app` because that instantiates FastMCP which boots
    a full session manager and isn't needed to verify middleware behaviour.
    """
    from apps.fishgoo_mcp.server import BearerAuthMiddleware

    app = Starlette(routes=[Route("/mcp", _dummy_endpoint, methods=["GET"])])
    app.add_middleware(BearerAuthMiddleware, token=token)
    return app


@unittest.skipUnless(_STARLETTE_AVAILABLE, "starlette not installed")
class ServerBearerMiddlewareTests(unittest.TestCase):
    def test_missing_bearer_returns_401(self) -> None:
        app = _make_app_with_bearer(TEST_TOKEN)
        client = TestClient(app)
        response = client.get("/mcp")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "missing_bearer")

    def test_wrong_token_returns_401(self) -> None:
        app = _make_app_with_bearer(TEST_TOKEN)
        client = TestClient(app)
        response = client.get("/mcp", headers={"Authorization": "Bearer nope"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "invalid_token")

    def test_correct_token_passes(self) -> None:
        app = _make_app_with_bearer(TEST_TOKEN)
        client = TestClient(app)
        response = client.get("/mcp", headers={"Authorization": f"Bearer {TEST_TOKEN}"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("ok"))

    def test_bearer_case_insensitive(self) -> None:
        app = _make_app_with_bearer(TEST_TOKEN)
        client = TestClient(app)
        response = client.get("/mcp", headers={"Authorization": f"bearer {TEST_TOKEN}"})
        self.assertEqual(response.status_code, 200)


@unittest.skipUnless(_STARLETTE_AVAILABLE, "starlette not installed")
class BuildAppAttachesMiddlewareWhenTokenSet(unittest.TestCase):
    """build_app() should add BearerAuthMiddleware only when a token is configured."""

    def test_token_set_attaches_middleware(self) -> None:
        with mock.patch.dict(os.environ, {"FISHGOO_MCP_AUTH_TOKEN": "abc"}):
            # Re-import server so it picks up the env at import time via settings.
            import importlib

            from apps.fishgoo_mcp import server as srv

            importlib.reload(srv)
            app = srv.build_app()
            names = [m.cls.__name__ for m in app.user_middleware]
            self.assertIn("BearerAuthMiddleware", names)

    def test_token_empty_skips_middleware(self) -> None:
        with mock.patch.dict(os.environ, {"FISHGOO_MCP_AUTH_TOKEN": ""}):
            import importlib

            from apps.fishgoo_mcp import server as srv

            importlib.reload(srv)
            app = srv.build_app()
            names = [m.cls.__name__ for m in app.user_middleware]
            self.assertNotIn("BearerAuthMiddleware", names)


if __name__ == "__main__":
    unittest.main()
