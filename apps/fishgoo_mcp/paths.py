from __future__ import annotations

from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent.parent
ARCHIVE_ROOT = REPO_ROOT / "FISHGOO_广告成长档案"
MEMORY_ROOT = REPO_ROOT / "memory"
GENERATED_ROOT = REPO_ROOT / "data" / "fishgoo_generated"
GENERATED_DAILY_DIR = GENERATED_ROOT / "daily_feedback"
GENERATED_DAILY_JSON_DIR = GENERATED_ROOT / "daily_payloads"
GENERATED_GA4_DAILY_DIR = GENERATED_ROOT / "ga4_daily"
GENERATED_BOARD_HTML = GENERATED_ROOT / "board" / "fishgoo-ad-board.html"
BOARD_HTML = REPO_ROOT / "fishgoo-ad-board.html"
BOARD_MD = (
    ARCHIVE_ROOT
    / "05_30天广告成长看板"
    / "FISHGOO_广告负责人看板_V3_2026-03-30.md"
)
BOARD_ARCHIVE_HTML = (
    ARCHIVE_ROOT
    / "05_30天广告成长看板"
    / "FISHGOO_广告负责人看板_V3_2026-03-30.html"
)
DAILY_AUDIT_SCRIPT = REPO_ROOT / "scripts" / "google_ads_daily_audit.py"
CHANGE_HISTORY_SCRIPT = REPO_ROOT / "scripts" / "google_ads_change_history.py"
FOLLOW_UP_DIR = ARCHIVE_ROOT / "03_后续观测计划"
ACTIVE_LEARNING_DIR = ARCHIVE_ROOT / "04_主动学习手册"
SPECS_DIR = REPO_ROOT / "docs" / "superpowers" / "specs"
PLANS_DIR = REPO_ROOT / "docs" / "superpowers" / "plans"
