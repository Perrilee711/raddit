from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from apps.fishgoo_mcp.paths import ARCHIVE_ROOT, BOARD_MD, FOLLOW_UP_DIR, MEMORY_ROOT
from apps.fishgoo_mcp.memory.writers import write_json_document, write_jsonl_document


DAY_PATTERN = re.compile(r"^(Day\d+)反馈_(\d{4}-\d{2}-\d{2})\.md$")


def list_day_feedback_files(archive_root: Path = ARCHIVE_ROOT) -> list[Path]:
    feedback_dir = archive_root / "03_后续观测计划"
    return sorted(feedback_dir.glob("Day*反馈_*.md"))


def extract_section_lines(markdown: str, header: str) -> list[str]:
    lines = markdown.splitlines()
    capture = False
    captured: list[str] = []
    for line in lines:
        if line.strip() == header:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    return [line for line in captured if line.strip()]


def build_overview() -> dict[str, Any]:
    readme_path = ARCHIVE_ROOT / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    return {
        "project": "FISHGOO 广告成长档案",
        "summary": "Google Ads 审计、学习成长、业务诊断与看板系统",
        "source_path": str(readme_path.relative_to(ARCHIVE_ROOT.parent)),
        "highlights": [
            "集中管理历史广告诊断与每轮账户变化",
            "持续追踪调整前后发生了什么",
            "帮助用户成长为能独立管理 Google Ads 的负责人",
        ],
        "raw_excerpt": text.splitlines()[:20],
    }


def build_current_truth() -> dict[str, Any]:
    board_text = BOARD_MD.read_text(encoding="utf-8")
    current_judgment = extract_section_lines(board_text, "### 当前总判断")
    next_actions = extract_section_lines(board_text, "### 今日动作建议")
    return {
        "updated_from": str(BOARD_MD.relative_to(ARCHIVE_ROOT.parent)),
        "current_judgment": current_judgment[:12],
        "next_actions_excerpt": next_actions[:12],
    }


def build_audit_timeline() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in list_day_feedback_files():
        match = DAY_PATTERN.match(path.name)
        if not match:
            continue
        day_label, day_date = match.groups()
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        rows.append(
            {
                "day": day_label,
                "date": day_date,
                "title": title,
                "path": str(path.relative_to(ARCHIVE_ROOT.parent)),
            }
        )
    return rows


def build_business_reports_index() -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    for path in sorted(FOLLOW_UP_DIR.glob("业务侧效果分析_*.md")):
        reports.append(
            {
                "path": str(path.relative_to(ARCHIVE_ROOT.parent)),
                "label": path.stem.replace("_", " "),
                "type": "business_analysis",
            }
        )
    return {"reports": reports}


def build_learning_progress() -> dict[str, Any]:
    timeline = build_audit_timeline()
    latest = timeline[-1] if timeline else None
    return {
        "current_phase": latest["day"] if latest else None,
        "latest_audit_date": latest["date"] if latest else None,
        "archive_count": len(timeline),
        "focus": [
            "先看 measurement，再看流量",
            "把平台指标和真实业务结果分开看",
            "逐步形成自己的负责人判断模板",
        ],
    }


def build_open_questions() -> dict[str, Any]:
    return {
        "questions": [
            "远程服务器部署在哪台机器上",
            "Google Ads 凭证如何从本机迁移到远程",
            "Gemini 是否优先走 HTTP bridge",
            "业务报表 ingest 是否需要统一模板",
        ]
    }


def build_decision_log() -> list[dict[str, Any]]:
    timeline = build_audit_timeline()
    rows: list[dict[str, Any]] = []
    if timeline:
        latest = timeline[-1]
        rows.append(
            {
                "date": latest["date"],
                "type": "current_focus",
                "decision": "优先建设远程 Fishgoo Ads OS MCP + Project Memory System",
                "source": latest["path"],
            }
        )
    return rows


def write_memory_projection() -> dict[str, Any]:
    outputs = {
        "overview": write_json_document("overview.json", build_overview()),
        "current_truth": write_json_document("current_truth.json", build_current_truth()),
        "business_reports_index": write_json_document(
            "business_reports_index.json", build_business_reports_index()
        ),
        "learning_progress": write_json_document("learning_progress.json", build_learning_progress()),
        "open_questions": write_json_document("open_questions.json", build_open_questions()),
        "audit_timeline": write_jsonl_document("audit_timeline.jsonl", build_audit_timeline()),
        "decision_log": write_jsonl_document("decision_log.jsonl", build_decision_log()),
    }
    return {key: str(path) for key, path in outputs.items()}


def main() -> None:
    result = write_memory_projection()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
