from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.fishgoo_mcp.paths import MEMORY_ROOT


def read_json_document(filename: str) -> dict[str, Any]:
    path = MEMORY_ROOT / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_document(filename: str) -> list[dict[str, Any]]:
    path = MEMORY_ROOT / filename
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def read_current_truth() -> dict[str, Any]:
    return read_json_document("current_truth.json")


def read_overview() -> dict[str, Any]:
    return read_json_document("overview.json")


def read_audit_timeline() -> list[dict[str, Any]]:
    return read_jsonl_document("audit_timeline.jsonl")


def read_business_reports_index() -> dict[str, Any]:
    return read_json_document("business_reports_index.json")
