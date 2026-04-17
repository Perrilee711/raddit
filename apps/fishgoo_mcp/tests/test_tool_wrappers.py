from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from apps.fishgoo_mcp.tools.ads_change_history import run_change_history, summarize_change_events
from apps.fishgoo_mcp.tools.ads_daily_audit import run_daily_audit, summarize_account_totals


class ToolWrapperTests(unittest.TestCase):
    @patch("apps.fishgoo_mcp.tools.ads_daily_audit.subprocess.run")
    def test_run_daily_audit_parses_json(self, run_mock) -> None:
        run_mock.return_value.stdout = json.dumps({"date": "2026-04-17", "account_today": [{}]})
        payload = run_daily_audit("2026-04-17")
        self.assertEqual(payload["date"], "2026-04-17")

    def test_summarize_account_totals_defaults_to_zero(self) -> None:
        summary = summarize_account_totals({"date": "2026-04-17", "customer_id": "1", "account_today": [{}]})
        self.assertEqual(summary["clicks"], 0)

    @patch("apps.fishgoo_mcp.tools.ads_change_history.subprocess.run")
    def test_run_change_history_parses_json(self, run_mock) -> None:
        run_mock.return_value.stdout = json.dumps([{"change_event.user_email": "test@example.com"}])
        rows = run_change_history("2026-04-17 00:00:00", "2026-04-17 23:59:59")
        self.assertEqual(rows[0]["change_event.user_email"], "test@example.com")

    def test_summarize_change_events_extracts_users(self) -> None:
        summary = summarize_change_events(
            [
                {
                    "change_event.user_email": "test@example.com",
                    "change_event.change_resource_type": "CAMPAIGN",
                    "change_event.change_date_time": "2026-04-17 10:00:00",
                }
            ]
        )
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["users"], ["test@example.com"])


if __name__ == "__main__":
    unittest.main()
