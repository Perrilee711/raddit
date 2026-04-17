from __future__ import annotations

import unittest

from apps.fishgoo_mcp.memory.builder import build_audit_timeline, list_day_feedback_files


class MemoryBuilderTests(unittest.TestCase):
    def test_list_day_feedback_files_contains_latest_day(self) -> None:
        files = list_day_feedback_files()
        self.assertTrue(any("Day23反馈_2026-04-17.md" in str(item) for item in files))

    def test_build_audit_timeline_has_day23_row(self) -> None:
        rows = build_audit_timeline()
        self.assertTrue(any(row["day"] == "Day23" for row in rows))


if __name__ == "__main__":
    unittest.main()
