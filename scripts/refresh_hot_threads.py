#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from hot_thread_policy import rank_hot_threads, summarize_hot_threads
from reddit_browser_common import load_config, write_jsonl
from reddit_research_report import generate_report

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh only high-value Reddit threads for an existing study raw dataset."
    )
    parser.add_argument("--config", required=True, help="Study browser config JSON path.")
    parser.add_argument("--entity-root", required=True, help="Entity directory containing threads.json.")
    parser.add_argument("--input", required=True, help="Current study raw JSONL path.")
    parser.add_argument("--output", required=True, help="Destination raw JSONL path.")
    parser.add_argument("--report-output", help="Optional Markdown report output path.")
    parser.add_argument("--chrome-app", default="Google Chrome", help="Chrome app name for AppleScript.")
    parser.add_argument("--continue-on-error", action="store_true", help="Skip failed thread refreshes.")
    parser.add_argument("--dry-run", action="store_true", help="Only compute hot-thread selection, do not harvest.")
    return parser.parse_args()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def canonical_key(row: dict[str, Any]) -> str:
    url = str(row.get("url", "")).split("?")[0].strip()
    if url:
        return url
    record_id = str(row.get("id", "")).strip()
    if record_id:
        return f"id:{record_id}"
    thread_id = str(row.get("thread_id", "")).strip()
    if thread_id:
        return f"thread:{thread_id}"
    return str(row.get("title", "")).strip()


def build_seed_row(candidate: dict[str, Any], existing_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    existing = existing_records.get(candidate["url"]) or existing_records.get(f"thread:{candidate['thread_id']}") or {}
    seed = dict(existing)
    seed.update(
        {
            "thread_id": candidate["thread_id"],
            "subreddit": seed.get("subreddit") or candidate.get("subreddit", ""),
            "title": seed.get("title") or candidate.get("title", ""),
            "url": candidate["url"],
            "score": max(int(seed.get("score", 0) or 0), int(candidate.get("current_score", 0) or 0)),
            "num_comments": max(
                int(seed.get("num_comments", 0) or 0),
                int(candidate.get("current_comment_count", 0) or 0),
            ),
            "search_term": " | ".join(candidate.get("search_terms", [])).strip() or seed.get("search_term", ""),
            "refresh_reason": (
                "missing_comments" if candidate.get("needs_comments")
                else "stale_hot_thread" if candidate.get("stale")
                else "active_hot_thread"
            ),
            "hot_score": candidate.get("hot_score", 0),
        }
    )
    return seed


def merge_rows(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "comments":
            existing_comments = existing.get("comments") or []
            incoming_comments = value or []
            merged[key] = incoming_comments if len(incoming_comments) >= len(existing_comments) else existing_comments
            continue
        if key in {"score", "num_comments"}:
            try:
                merged[key] = max(int(existing.get(key, 0) or 0), int(value or 0))
            except (TypeError, ValueError):
                merged[key] = value
            continue
        if key == "search_term":
            terms = {
                term.strip()
                for item in [existing.get("search_term", ""), value]
                for term in str(item).split("|")
                if term.strip()
            }
            merged[key] = " | ".join(sorted(terms))
            continue
        if value not in (None, "", []):
            merged[key] = value
    return merged


def merge_datasets(existing_rows: list[dict[str, Any]], refreshed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {canonical_key(row): dict(row) for row in existing_rows}
    for row in refreshed_rows:
        key = canonical_key(row)
        if key in merged:
            merged[key] = merge_rows(merged[key], row)
        else:
            merged[key] = dict(row)
    return list(merged.values())


def run_harvest(
    seeds: list[dict[str, Any]],
    output_path: Path,
    config: dict[str, Any],
    chrome_app: str,
    continue_on_error: bool,
) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="hot-thread-refresh-") as temp_dir:
        temp_root = Path(temp_dir)
        discovered_path = temp_root / "hot_candidates.jsonl"
        harvested_path = temp_root / "hot_harvested.jsonl"
        write_jsonl(discovered_path, seeds)

        command = [
            sys.executable,
            str(SCRIPT_DIR / "harvest_threads.py"),
            "--input",
            str(discovered_path),
            "--output",
            str(harvested_path),
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

        subprocess.run(command, check=True)
        refreshed_rows = read_jsonl(harvested_path)
        write_jsonl(output_path, refreshed_rows)
        return refreshed_rows


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    threads = read_json(Path(args.entity_root) / "threads.json", [])
    existing_rows = read_jsonl(Path(args.input))
    existing_lookup = {canonical_key(row): row for row in existing_rows}

    selection = summarize_hot_threads(threads, config)
    selected = rank_hot_threads(threads, config)[: int(selection["thresholds"]["max_count"])]

    if args.dry_run:
        print(json.dumps(selection, ensure_ascii=False, indent=2))
        return

    if not selected:
        if Path(args.input) != Path(args.output):
            write_jsonl(Path(args.output), existing_rows)
        if args.report_output:
            generate_report(Path(args.output), Path(args.report_output), top_leads=15)
        print(json.dumps({**selection, "refreshed_count": 0}, ensure_ascii=False))
        return

    seeds = [build_seed_row(candidate, existing_lookup) for candidate in selected]
    refreshed_only_path = Path(args.output).with_name(f"{Path(args.output).stem}_hot_threads.jsonl")
    refreshed_rows = run_harvest(
        seeds,
        refreshed_only_path,
        config=config,
        chrome_app=args.chrome_app,
        continue_on_error=args.continue_on_error,
    )
    merged_rows = merge_datasets(existing_rows, refreshed_rows)
    write_jsonl(Path(args.output), merged_rows)

    if args.report_output:
        generate_report(Path(args.output), Path(args.report_output), top_leads=15)

    summary = {
        **selection,
        "refreshed_count": len(refreshed_rows),
        "merged_count": len(merged_rows),
        "refreshed_output": str(refreshed_only_path),
        "output": str(Path(args.output)),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Hot-thread refresh failed: {error}", file=sys.stderr)
        raise
