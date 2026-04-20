from __future__ import annotations

import unittest
from datetime import date, datetime

from apps.fishgoo_mcp.automation import day_label_for_date, render_feedback_markdown, summarize_payload


class AutomationTests(unittest.TestCase):
    def test_day_label_for_date_matches_known_day(self) -> None:
        self.assertEqual(day_label_for_date(date(2026, 4, 20)), "Day26")

    def test_summarize_payload_sums_yesterday_rows(self) -> None:
        payload = {
            "account_today": [{"metrics.impressions": 10, "metrics.clicks": 2, "metrics.cost_micros": 1230000}],
            "campaigns_today": [{"campaign.status": "ENABLED"}],
            "campaigns_yesterday": [
                {"metrics.impressions": 5, "metrics.clicks": 1, "metrics.cost_micros": 1000000, "metrics.conversions": 1},
                {"metrics.impressions": 7, "metrics.clicks": 2, "metrics.cost_micros": 2500000, "metrics.conversions": 0.5},
            ],
            "campaigns_last_7d": [],
        }
        summary = summarize_payload(payload)
        self.assertEqual(summary["yesterday"]["impressions"], 12)
        self.assertEqual(summary["yesterday"]["clicks"], 3)
        self.assertEqual(summary["yesterday"]["cost_usd"], 3.5)

    def test_render_feedback_markdown_contains_current_metrics(self) -> None:
        payload = {
            "account_today": [{"metrics.impressions": 10, "metrics.clicks": 2, "metrics.cost_micros": 1230000, "metrics.conversions": 0}],
            "campaigns_today": [
                {
                    "campaign.name": "Pmax-",
                    "campaign.status": "ENABLED",
                    "campaign.advertising_channel_type": "PERFORMANCE_MAX",
                    "campaign.primary_status": "LIMITED",
                    "campaign_budget.amount_micros": 40700000,
                }
            ],
            "campaigns_yesterday": [],
            "campaigns_last_7d": [],
            "conversion_actions": [],
            "campaign_goals": [],
        }
        markdown = render_feedback_markdown(payload, date(2026, 4, 20), datetime(2026, 4, 20, 10, 0, 0))
        self.assertIn("Day26", markdown)
        self.assertIn("`10`", markdown)
        self.assertIn("$1.23", markdown)


if __name__ == "__main__":
    unittest.main()
