#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from apps.fishgoo_mcp.automation import (
    write_generated_board_html,
    write_generated_feedback,
    write_generated_payload,
)
from apps.fishgoo_mcp.paths import DAILY_AUDIT_SCRIPT, REPO_ROOT


GA4_AUDIT_SCRIPT = REPO_ROOT / "scripts" / "ga4_daily_audit.py"
GA4_SA_CREDENTIAL = Path("/root/raddit/.env/ga4-sa.json")


def run_daily_audit(audit_date: str) -> dict:
    python_bin = os.environ.get("FISHGOO_PYTHON_BIN") or os.environ.get("PYTHON_BIN") or "python3"
    cmd = [python_bin, str(DAILY_AUDIT_SCRIPT), "--date", audit_date]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=REPO_ROOT)
    return json.loads(proc.stdout)


def run_ga4_audit(audit_date: str) -> dict | None:
    """Pull GA4 purchase event data. Failures are non-fatal to the main pipeline.

    Returns the parsed summary JSON on success, or None if GA4 credential is
    missing / API fails. This lets the daily refresh keep running even if
    GA4 side breaks.
    """
    if not GA4_SA_CREDENTIAL.exists():
        return {"skipped": True, "reason": f"no credential at {GA4_SA_CREDENTIAL}"}
    python_bin = os.environ.get("FISHGOO_PYTHON_BIN") or os.environ.get("PYTHON_BIN") or "python3"
    env = os.environ.copy()
    env["GOOGLE_APPLICATION_CREDENTIALS"] = str(GA4_SA_CREDENTIAL)
    cmd = [python_bin, str(GA4_AUDIT_SCRIPT), "--date", audit_date]
    try:
        proc = subprocess.run(
            cmd, check=True, capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=60
        )
        # ga4_daily_audit.py prints JSON summary on last stdout line
        last_json = proc.stdout.strip().splitlines()[-1]
        return json.loads(last_json)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError, IndexError) as e:
        return {"skipped": False, "error": type(e).__name__, "detail": str(e)[:200]}


def publish_board() -> None:
    refresh_script = Path("/usr/local/bin/fishgoo-board-refresh.sh")
    if refresh_script.exists():
        subprocess.run([str(refresh_script)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Fishgoo daily audit refresh and publish board.")
    parser.add_argument("--date", help="Audit date in YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--publish", action="store_true", help="Publish the refreshed board after generation.")
    args = parser.parse_args()

    now = datetime.now()
    audit_date = args.date or now.date().isoformat()
    payload = run_daily_audit(audit_date)
    payload_path = write_generated_payload(payload, now.date())
    feedback_path = write_generated_feedback(payload, now.date(), now)

    subprocess.run(
        [os.environ.get("FISHGOO_PYTHON_BIN") or "python3", "-m", "apps.fishgoo_mcp.memory.builder"],
        check=True,
        cwd=REPO_ROOT,
    )
    board_path = write_generated_board_html(payload, now, feedback_path)

    # GA4 audit runs in parallel-ish with the main pipeline. Non-fatal.
    # Typically audits yesterday (D-1) since today's events still trickling in.
    from datetime import timedelta

    ga4_target = (now.date() - timedelta(days=1)).isoformat()
    ga4_summary = run_ga4_audit(ga4_target)

    if args.publish:
        publish_board()

    result = {
        "audit_date": audit_date,
        "payload_path": str(payload_path),
        "feedback_path": str(feedback_path),
        "board_path": str(board_path),
        "ga4_target_date": ga4_target,
        "ga4_summary": ga4_summary,
        "published": bool(args.publish),
        "refreshed_at": now.isoformat(timespec="seconds"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
