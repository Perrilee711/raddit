# Fishgoo Ads OS MCP MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first remote-accessible Fishgoo Ads OS MCP MVP with read-only Google Ads audit tools, project memory resources, and a lightweight HTTP bridge.

**Architecture:** Create an isolated Python app under `apps/fishgoo_mcp/` that wraps the existing Google Ads audit scripts, projects structured project memory from the archive docs into machine-readable JSON, and exposes both MCP-ready server entrypoints and a thin HTTP bridge for compatibility. Keep all Google Ads behavior read-only and write only to the Fishgoo archive, generated memory files, and board artifacts.

**Tech Stack:** Python 3, existing local audit scripts, JSON/Markdown project memory, minimal app-local configuration, optional FastMCP dependency, standard-library fallback helpers.

---

### Task 1: Scaffold The Isolated App Shell

**Files:**
- Create: `apps/fishgoo_mcp/__init__.py`
- Create: `apps/fishgoo_mcp/config.py`
- Create: `apps/fishgoo_mcp/paths.py`
- Create: `apps/fishgoo_mcp/schemas.py`
- Create: `apps/fishgoo_mcp/README.md`
- Create: `apps/fishgoo_mcp/requirements.txt`

- [ ] **Step 1: Create the package skeleton**

Create the package directory and empty module marker files so the app lives outside the legacy scripts.

```text
apps/fishgoo_mcp/
  __init__.py
  config.py
  paths.py
  schemas.py
  README.md
  requirements.txt
```

- [ ] **Step 2: Define stable project paths in `paths.py`**

Add constants for the repo root, archive root, memory root, board files, and scripts used by the new service.

```python
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent.parent
ARCHIVE_ROOT = REPO_ROOT / "FISHGOO_广告成长档案"
MEMORY_ROOT = REPO_ROOT / "memory"
BOARD_HTML = REPO_ROOT / "fishgoo-ad-board.html"
BOARD_MD = ARCHIVE_ROOT / "05_30天广告成长看板" / "FISHGOO_广告负责人看板_V3_2026-03-30.md"
DAILY_AUDIT_SCRIPT = REPO_ROOT / "scripts" / "google_ads_daily_audit.py"
CHANGE_HISTORY_SCRIPT = REPO_ROOT / "scripts" / "google_ads_change_history.py"
```

- [ ] **Step 3: Define app config in `config.py`**

Create a small config loader that reads environment variables and gives sane defaults for host, port, customer ID, and publish settings.

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    host: str = os.environ.get("FISHGOO_MCP_HOST", "0.0.0.0")
    port: int = int(os.environ.get("FISHGOO_MCP_PORT", "8766"))
    customer_id: str = os.environ.get("FISHGOO_GOOGLE_ADS_CUSTOMER_ID", "1573113113")
    enable_publish: bool = os.environ.get("FISHGOO_MCP_ENABLE_PUBLISH", "false").lower() == "true"
```

- [ ] **Step 4: Define response schemas in `schemas.py`**

Create simple dataclasses or typed dicts for audit summaries, memory resources, and bridge responses so later tasks reuse one vocabulary.

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolResult:
    ok: bool
    message: str
    data: dict[str, Any]
```

- [ ] **Step 5: Document local setup in `README.md` and `requirements.txt`**

Add the MVP dependencies and run commands for future maintainers.

```text
fastmcp
pydantic
```

- [ ] **Step 6: Commit**

```bash
git add apps/fishgoo_mcp
git commit -m "feat: scaffold fishgoo mcp app shell"
```

### Task 2: Wrap The Existing Read-Only Google Ads Scripts

**Files:**
- Create: `apps/fishgoo_mcp/tools/__init__.py`
- Create: `apps/fishgoo_mcp/tools/ads_daily_audit.py`
- Create: `apps/fishgoo_mcp/tools/ads_change_history.py`
- Modify: `apps/fishgoo_mcp/schemas.py`

- [ ] **Step 1: Create the tools package**

```text
apps/fishgoo_mcp/tools/
  __init__.py
  ads_daily_audit.py
  ads_change_history.py
```

- [ ] **Step 2: Implement a subprocess wrapper for daily audit**

Call the existing script and parse stdout JSON without changing the legacy script.

```python
import json
import subprocess
from apps.fishgoo_mcp.paths import DAILY_AUDIT_SCRIPT

def run_daily_audit(date: str, customer_id: str) -> dict:
    proc = subprocess.run(
        ["python3", str(DAILY_AUDIT_SCRIPT), "--date", date, "--customer-id", customer_id],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)
```

- [ ] **Step 3: Implement a subprocess wrapper for change history**

```python
import json
import subprocess
from apps.fishgoo_mcp.paths import CHANGE_HISTORY_SCRIPT

def run_change_history(from_datetime: str, to_datetime: str, customer_id: str) -> list[dict]:
    proc = subprocess.run(
        [
            "python3",
            str(CHANGE_HISTORY_SCRIPT),
            "--customer-id",
            customer_id,
            "--from-datetime",
            from_datetime,
            "--to-datetime",
            to_datetime,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)
```

- [ ] **Step 4: Add simple normalization helpers**

Normalize the raw script outputs into stable summaries the MCP layer can expose.

```python
def summarize_account_totals(payload: dict) -> dict:
    account = (payload.get("account_today") or [{}])[0]
    return {
        "impressions": account.get("metrics.impressions", 0),
        "clicks": account.get("metrics.clicks", 0),
        "cost_micros": account.get("metrics.cost_micros", 0),
        "conversions": account.get("metrics.conversions", 0),
    }
```

- [ ] **Step 5: Commit**

```bash
git add apps/fishgoo_mcp/tools apps/fishgoo_mcp/schemas.py
git commit -m "feat: wrap read-only Google Ads audit scripts"
```

### Task 3: Build The Project Memory Layer

**Files:**
- Create: `apps/fishgoo_mcp/memory/__init__.py`
- Create: `apps/fishgoo_mcp/memory/builder.py`
- Create: `apps/fishgoo_mcp/memory/readers.py`
- Create: `apps/fishgoo_mcp/memory/writers.py`
- Create: `memory/overview.json`
- Create: `memory/current_truth.json`
- Create: `memory/decision_log.jsonl`
- Create: `memory/audit_timeline.jsonl`
- Create: `memory/business_reports_index.json`
- Create: `memory/learning_progress.json`
- Create: `memory/open_questions.json`

- [ ] **Step 1: Create the memory package**

```text
apps/fishgoo_mcp/memory/
  __init__.py
  builder.py
  readers.py
  writers.py
```

- [ ] **Step 2: Implement archive scanning in `builder.py`**

Scan the existing Fishgoo archive and project a minimal machine-readable layer.

```python
from pathlib import Path

def list_day_feedback_files(archive_root: Path) -> list[Path]:
    feedback_dir = archive_root / "03_后续观测计划"
    return sorted(feedback_dir.glob("Day*反馈_*.md"))
```

- [ ] **Step 3: Generate `business_reports_index.json`**

Store each business analysis/report file path with a human-readable label.

```python
{
  "reports": [
    {
      "path": "FISHGOO_广告成长档案/03_后续观测计划/业务侧效果分析_2026-04-08_2026-04-14.md",
      "label": "业务侧效果分析 2026-04-08 至 2026-04-14",
      "type": "business_analysis"
    }
  ]
}
```

- [ ] **Step 4: Generate `audit_timeline.jsonl` from Day docs**

Write one line per Day feedback file with date, title, and file path.

```json
{"day":"Day23","date":"2026-04-17","title":"Day 23 反馈","path":"FISHGOO_广告成长档案/03_后续观测计划/Day23反馈_2026-04-17.md"}
```

- [ ] **Step 5: Seed `overview.json` and `current_truth.json`**

Use the latest board summary plus archive README to build an initial project summary and current state snapshot.

- [ ] **Step 6: Add read helpers in `readers.py`**

Implement generic readers that return parsed JSON from the `memory/` directory.

- [ ] **Step 7: Commit**

```bash
git add apps/fishgoo_mcp/memory memory
git commit -m "feat: add fishgoo project memory layer"
```

### Task 4: Add The MCP Service Entry Point

**Files:**
- Create: `apps/fishgoo_mcp/server.py`
- Modify: `apps/fishgoo_mcp/config.py`
- Modify: `apps/fishgoo_mcp/tools/ads_daily_audit.py`
- Modify: `apps/fishgoo_mcp/tools/ads_change_history.py`
- Modify: `apps/fishgoo_mcp/memory/readers.py`

- [ ] **Step 1: Create a minimal MCP server entry**

Set up the server module with conditional FastMCP import so the app fails clearly if the dependency is missing.

```python
try:
    from fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("fastmcp is required for apps/fishgoo_mcp/server.py") from exc

mcp = FastMCP("Fishgoo Ads OS MCP")
```

- [ ] **Step 2: Register the read-only tools**

Expose `ads_daily_audit` and `ads_change_history` as MCP tools.

- [ ] **Step 3: Register core resources**

Expose `project://overview`, `project://current-truth`, and `project://audit-timeline`.

- [ ] **Step 4: Add a local run function**

```python
def main() -> None:
    mcp.run()

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Commit**

```bash
git add apps/fishgoo_mcp/server.py apps/fishgoo_mcp/config.py apps/fishgoo_mcp/tools apps/fishgoo_mcp/memory/readers.py
git commit -m "feat: expose fishgoo audit and memory through mcp"
```

### Task 5: Add A Lightweight HTTP Bridge

**Files:**
- Create: `apps/fishgoo_mcp/bridge/__init__.py`
- Create: `apps/fishgoo_mcp/bridge/app.py`
- Modify: `apps/fishgoo_mcp/schemas.py`
- Modify: `apps/fishgoo_mcp/README.md`

- [ ] **Step 1: Create the bridge package**

```text
apps/fishgoo_mcp/bridge/
  __init__.py
  app.py
```

- [ ] **Step 2: Add basic GET endpoints**

Expose:

- `/health`
- `/memory/current-truth`
- `/tools/ads-daily-audit?date=YYYY-MM-DD`

Use standard library HTTP to avoid blocking on framework setup.

- [ ] **Step 3: Reuse the same tool wrappers**

Do not duplicate business logic in the bridge; call the same wrappers from the tools package.

- [ ] **Step 4: Commit**

```bash
git add apps/fishgoo_mcp/bridge apps/fishgoo_mcp/README.md
git commit -m "feat: add fishgoo mcp http bridge"
```

### Task 6: Verify The MVP Locally

**Files:**
- Create: `apps/fishgoo_mcp/tests/test_memory_builder.py`
- Create: `apps/fishgoo_mcp/tests/test_tool_wrappers.py`
- Create: `apps/fishgoo_mcp/tests/test_bridge_smoke.py`

- [ ] **Step 1: Write a memory builder smoke test**

```python
def test_list_day_feedback_files_returns_day_docs():
    files = list_day_feedback_files(ARCHIVE_ROOT)
    assert any("Day23反馈_2026-04-17.md" in str(item) for item in files)
```

- [ ] **Step 2: Write a tool wrapper contract test**

Mock subprocess output and ensure the wrappers parse JSON correctly.

- [ ] **Step 3: Write a bridge smoke test**

Start the bridge on a random local port and assert `/health` returns `ok`.

- [ ] **Step 4: Run verification commands**

```bash
python3 -m py_compile apps/fishgoo_mcp/server.py apps/fishgoo_mcp/bridge/app.py
python3 -m pytest apps/fishgoo_mcp/tests -q
```

- [ ] **Step 5: Commit**

```bash
git add apps/fishgoo_mcp/tests
git commit -m "test: verify fishgoo mcp mvp locally"
```

### Task 7: Prepare Remote Deployment Hand-Off

**Files:**
- Create: `docs/product/2026-04-17-fishgoo-mcp-remote-runbook.md`
- Modify: `apps/fishgoo_mcp/README.md`

- [ ] **Step 1: Write the deployment runbook**

Document:

- required environment variables
- dependency install commands
- service start commands
- reverse proxy expectations
- Claude remote MCP connection note

- [ ] **Step 2: Add the exact remote start commands**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/fishgoo_mcp/requirements.txt
python3 apps/fishgoo_mcp/bridge/app.py
python3 apps/fishgoo_mcp/server.py
```

- [ ] **Step 3: Commit**

```bash
git add docs/product/2026-04-17-fishgoo-mcp-remote-runbook.md apps/fishgoo_mcp/README.md
git commit -m "docs: add fishgoo mcp remote deployment runbook"
```

## Spec Coverage Check

- Remote-accessible MCP service: covered in Tasks 1, 4, 5, and 7.
- Project memory system: covered in Task 3.
- Read-only Google Ads audit tools: covered in Task 2 and Task 4.
- HTTP bridge for compatibility: covered in Task 5.
- Verification and remote hand-off: covered in Tasks 6 and 7.

## Execution Note

The user has already approved moving past design and asked to continue implementation, so proceed with **Inline Execution** starting from Task 1.
