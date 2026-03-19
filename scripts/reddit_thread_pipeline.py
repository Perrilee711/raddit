#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from reddit_research_report import generate_report


DEFAULT_CONFIG_PATH = "config/reddit_targets.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover Reddit threads, harvest thread detail + comments, and generate a Markdown report."
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the target config JSON file.")
    parser.add_argument("--raw-output", required=True, help="Path to save enriched thread JSONL.")
    parser.add_argument("--report-output", required=True, help="Path to save the Markdown report.")
    parser.add_argument(
        "--discovery-output",
        help="Optional path to save the intermediate discovered-thread JSONL.",
    )
    parser.add_argument("--top-leads", type=int, default=15, help="How many high-intent threads to include.")
    parser.add_argument("--chrome-app", default="Google Chrome", help="Chrome app name for AppleScript.")
    parser.add_argument("--continue-on-error", action="store_true", help="Skip failed pages or threads and continue.")
    return parser.parse_args()


def build_discovery_path(raw_output: Path, override: str | None) -> Path:
    if override:
        return Path(override)
    return raw_output.with_name(f"{raw_output.stem}_discovered{raw_output.suffix or '.jsonl'}")


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    raw_output = Path(args.raw_output)
    report_output = Path(args.report_output)
    discovery_output = build_discovery_path(raw_output, args.discovery_output)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    discovery_command = [
        sys.executable,
        "scripts/discover_threads.py",
        "--config",
        args.config,
        "--output",
        str(discovery_output),
        "--chrome-app",
        args.chrome_app,
    ]
    harvest_command = [
        sys.executable,
        "scripts/harvest_threads.py",
        "--input",
        str(discovery_output),
        "--output",
        str(raw_output),
        "--chrome-app",
        args.chrome_app,
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

    if args.continue_on_error:
        discovery_command.append("--continue-on-error")
        harvest_command.append("--continue-on-error")

    run_command(discovery_command)
    run_command(harvest_command)
    generate_report(raw_output, report_output, top_leads=args.top_leads)

    print(f"Discovery: {discovery_output}")
    print(f"Raw data: {raw_output}")
    print(f"Report: {report_output}")


if __name__ == "__main__":
    main()
