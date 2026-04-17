from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.fishgoo_mcp.paths import MEMORY_ROOT


def ensure_memory_root() -> None:
    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)


def write_json_document(filename: str, payload: dict[str, Any]) -> Path:
    ensure_memory_root()
    path = MEMORY_ROOT / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl_document(filename: str, rows: list[dict[str, Any]]) -> Path:
    ensure_memory_root()
    path = MEMORY_ROOT / filename
    content = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")
    return path
