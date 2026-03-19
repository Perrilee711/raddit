#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from demand_intelligence_server import (
    choose_adaptive_mode,
    load_study_record,
    materialize_record,
    run_hot_thread_rebuild,
    save_study_record,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the pipeline for a saved demand-intelligence study."
    )
    parser.add_argument("--study-id", required=True, help="Study id saved under data/studies/")
    parser.add_argument(
        "--mode",
        choices=["seeded", "browser", "hot_threads", "adaptive"],
        default="adaptive",
        help="Use the saved seed dataset or run the browser Reddit collector first.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="When running browser collection, continue past failed pages.",
    )
    return parser.parse_args()


def run_browser_collection(record: dict, continue_on_error: bool) -> Path:
    source = record.get("source", {})
    artifacts = record.get("artifacts", {})
    config_path = source.get("browser_config_path")
    raw_output = artifacts.get("raw_output_path")
    report_output = artifacts.get("report_output_path")
    if not config_path or not raw_output or not report_output:
        raise SystemExit("Study is missing browser pipeline config or artifact paths.")

    command = [
        sys.executable,
        "scripts/reddit_thread_pipeline.py",
        "--config",
        config_path,
        "--raw-output",
        raw_output,
        "--report-output",
        report_output,
    ]
    if continue_on_error:
        command.append("--continue-on-error")

    subprocess.run(command, check=True)
    return Path(raw_output)


def main() -> None:
    args = parse_args()
    record = load_study_record(args.study_id)
    if not record:
        raise SystemExit(f"Study not found: {args.study_id}")

    resolved_mode = args.mode
    if args.mode == "adaptive":
        resolved_mode, reason = choose_adaptive_mode(record)
        print(f"Adaptive mode resolved to: {resolved_mode}")
        print(f"Reason: {reason}")

    input_path = Path(record.get("source", {}).get("input_path", ""))
    if resolved_mode == "browser":
        input_path = run_browser_collection(record, args.continue_on_error)
        record["source"]["type"] = "browser_reddit"
        record["source"]["input_path"] = str(input_path)
    elif resolved_mode == "hot_threads":
        input_path = run_hot_thread_rebuild(record)
        record["source"]["type"] = "browser_reddit_thread_pipeline"
        record["source"]["input_path"] = str(input_path)

    if not input_path.exists():
        raise SystemExit(f"Input dataset not found: {input_path}")

    record = materialize_record(record, input_path)
    save_study_record(record)

    print(f"Study rebuilt: {record['id']}")
    print(f"Payload: {record.get('artifacts', {}).get('payload_json_path', '')}")
    print(f"Config: {record.get('artifacts', {}).get('config_path', '')}")
    print(f"Manifest: {record.get('artifacts', {}).get('manifest_path', '')}")
    print(f"Threads: {record.get('artifacts', {}).get('threads_path', '')}")
    print(f"Signals: {record.get('artifacts', {}).get('signals_path', '')}")
    print(
        "Foundation: "
        f"{record.get('data_foundation', {}).get('thread_count', 0)} threads / "
        f"{record.get('data_foundation', {}).get('comment_count', 0)} comments / "
        f"{record.get('data_foundation', {}).get('comment_capture_state', 'thread_only')}"
    )
    print(f"Source type: {record.get('source', {}).get('type', '')}")


if __name__ == "__main__":
    main()
