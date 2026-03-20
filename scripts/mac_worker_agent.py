#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DEFAULT_API_BASE_URL = os.environ.get("DEMAND_INTEL_API_BASE_URL", "http://43.162.90.26")
DEFAULT_WORKER_TOKEN = os.environ.get("DEMAND_INTEL_WORKER_TOKEN", "fishgoo-mac-worker-token")
DEFAULT_WORKER_ID = os.environ.get("DEMAND_INTEL_WORKER_ID", "fishgoo-mac-worker")
DEFAULT_CHROME_APP = os.environ.get("DEMAND_INTEL_CHROME_APP", "Google Chrome")
REMOTE_STAGE_KINDS = ("discover", "harvest", "refresh_hot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Poll the public Demand Intelligence API and execute browser stages on a Mac worker."
    )
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL, help="Base URL for the public API.")
    parser.add_argument("--worker-token", default=DEFAULT_WORKER_TOKEN, help="Shared token registered in config/workers.json.")
    parser.add_argument("--worker-id", default=DEFAULT_WORKER_ID, help="Logical worker id. Defaults to the configured worker id.")
    parser.add_argument("--worker-name", default=socket.gethostname(), help="Display name reported in logs.")
    parser.add_argument("--chrome-app", default=DEFAULT_CHROME_APP, help="Chrome app name for AppleScript automation.")
    parser.add_argument("--poll-seconds", type=float, default=8.0, help="Seconds to wait before polling again when idle.")
    parser.add_argument("--continue-on-error", action="store_true", help="Pass through continue-on-error to browser collection commands.")
    parser.add_argument("--once", action="store_true", help="Claim at most one job and then exit.")
    return parser.parse_args()


def request_json(
    api_base_url: str,
    method: str,
    path: str,
    worker_token: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    body = None
    headers = {
        "Accept": "application/json",
        "X-Worker-Token": worker_token,
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{api_base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw or "{}")
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} {path}: {raw}") from error


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_harvest_command(
    input_path: Path,
    output_path: Path,
    config: dict[str, Any],
    chrome_app: str,
    continue_on_error: bool,
) -> list[str]:
    command = [
        sys.executable,
        "scripts/harvest_threads.py",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--chrome-app",
        chrome_app,
        "--max-comments",
        str(int(config.get("thread_max_comments", 40))),
        "--expand-rounds",
        str(int(config.get("thread_expand_rounds", 2))),
        "--scroll-rounds",
        str(int(config.get("thread_scroll_rounds", 3))),
        "--delay-seconds",
        str(float(config.get("thread_delay_seconds", 1.0))),
        "--browser-wait",
        str(float(config.get("browser_wait_seconds", 15.0))),
    ]
    if continue_on_error:
        command.append("--continue-on-error")
    return command


def run_stage(
    stage_kind: str,
    task: dict[str, Any],
    chrome_app: str,
    continue_on_error: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = task.get("config") or {}
    with tempfile.TemporaryDirectory(prefix=f"demand-worker-{stage_kind}-") as temp_dir:
        temp_root = Path(temp_dir)
        if stage_kind == "discover":
            config_path = temp_root / "config.json"
            output_path = temp_root / "discovered.jsonl"
            write_json(config_path, config)
            command = [
                sys.executable,
                "scripts/discover_threads.py",
                "--config",
                str(config_path),
                "--output",
                str(output_path),
                "--chrome-app",
                chrome_app,
            ]
            if continue_on_error:
                command.append("--continue-on-error")
            subprocess.run(command, check=True, cwd=str(ROOT_DIR))
            rows = read_jsonl(output_path)
            summary = {
                "discovered_count": len(rows),
                "search_term_count": len(config.get("search_terms") or []),
                "subreddit_count": len(config.get("subreddits") or []),
            }
            return rows, summary

        input_rows = task.get("input_rows") or []
        input_path = temp_root / "input.jsonl"
        output_path = temp_root / "output.jsonl"
        write_jsonl(input_path, input_rows)
        command = build_harvest_command(input_path, output_path, config, chrome_app, continue_on_error)
        subprocess.run(command, check=True, cwd=str(ROOT_DIR))
        rows = read_jsonl(output_path)
        comment_count = sum(len((row.get("comments") or [])) for row in rows)
        summary = {
            "input_count": len(input_rows),
            "output_count": len(rows),
            "comment_count": comment_count,
        }
        if stage_kind == "refresh_hot":
            selection = task.get("selection") or {}
            summary["selected_count"] = int(selection.get("selected_count", len(input_rows)) or len(input_rows))
        return rows, summary


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            {
                "event": "worker_start",
                "api_base_url": args.api_base_url,
                "worker_id": args.worker_id,
                "worker_name": args.worker_name,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    while True:
        claim = request_json(
            args.api_base_url,
            "POST",
            "/api/worker/claim",
            args.worker_token,
            payload={
                "worker_id": args.worker_id,
                "worker_name": args.worker_name,
                "capabilities": list(REMOTE_STAGE_KINDS),
            },
        )
        job = claim.get("job")
        task = claim.get("task")
        if not job or not task:
            if args.once:
                return
            time.sleep(args.poll_seconds)
            continue

        stage_kind = str(job.get("stage_kind") or "")
        job_id = str(job.get("id") or "")
        print(
            json.dumps(
                {
                    "event": "job_claimed",
                    "job_id": job_id,
                    "stage_kind": stage_kind,
                    "study_id": job.get("study_id"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        try:
            rows, summary = run_stage(stage_kind, task, args.chrome_app, args.continue_on_error)
            request_json(
                args.api_base_url,
                "POST",
                f"/api/worker/jobs/{job_id}/complete",
                args.worker_token,
                payload={"rows": rows, "summary": summary},
            )
            print(
                json.dumps(
                    {
                        "event": "job_completed",
                        "job_id": job_id,
                        "stage_kind": stage_kind,
                        "row_count": len(rows),
                        "summary": summary,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        except Exception as error:  # noqa: BLE001
            request_json(
                args.api_base_url,
                "POST",
                f"/api/worker/jobs/{job_id}/fail",
                args.worker_token,
                payload={
                    "error": str(error),
                    "context": {
                        "stage_kind": stage_kind,
                        "worker_id": args.worker_id,
                    },
                },
            )
            print(
                json.dumps(
                    {
                        "event": "job_failed",
                        "job_id": job_id,
                        "stage_kind": stage_kind,
                        "error": str(error),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
                flush=True,
            )
        if args.once:
            return


if __name__ == "__main__":
    main()
