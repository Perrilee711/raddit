#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from build_demand_intelligence_payload import (
    classify_pain,
    classify_row,
    parse_created_datetime,
    read_jsonl,
    specificity_score,
    urgency_score,
)


SCHEMA_VERSION = "thread-store-v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build thread/comment/snapshot entities from a study raw JSONL dataset."
    )
    parser.add_argument("--input", required=True, help="Path to raw JSONL.")
    parser.add_argument("--study-id", required=True, help="Study id used for entity output.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write entity JSON files into.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def score_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def source_level(record: dict[str, Any]) -> str:
    return "thread" if not record.get("comments") else "thread+comments"


def thread_id_for_record(record: dict[str, Any]) -> str:
    record_id = clean_text(record.get("id"))
    if record_id:
        return f"reddit-thread-{record_id}"
    if clean_text(record.get("url")):
        return stable_id("reddit-thread", clean_text(record.get("url")))
    return stable_id("reddit-thread", clean_text(record.get("title")))


def comment_id_for_payload(thread_id: str, payload: dict[str, Any], index_hint: str) -> str:
    raw_id = clean_text(payload.get("id"))
    if raw_id:
        return f"reddit-comment-{raw_id}"
    permalink = clean_text(payload.get("permalink"))
    if permalink:
        return stable_id("reddit-comment", permalink)
    body = clean_text(payload.get("body"))
    return stable_id("reddit-comment", f"{thread_id}:{index_hint}:{body[:120]}")


def flatten_comments(thread_id: str, comments: list[Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []

    def walk(items: list[Any], depth: int, parent_id: str | None, prefix: str) -> None:
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            comment_id = comment_id_for_payload(thread_id, item, f"{prefix}-{index}")
            body = clean_text(item.get("body") or item.get("text"))
            entry = {
                "comment_id": comment_id,
                "thread_id": thread_id,
                "parent_id": parent_id,
                "author": clean_text(item.get("author")),
                "depth": score_int(item.get("depth", depth)),
                "permalink": clean_text(item.get("permalink")),
                "created_at": item.get("created_utc") or item.get("created_at"),
                "body": body,
                "score": score_int(item.get("score")),
                "is_op_reply": bool(item.get("is_op_reply", False)),
                "awards_count": score_int(item.get("awards_count")),
            }
            flattened.append(entry)
            replies = item.get("replies") or []
            if isinstance(replies, list) and replies:
                walk(replies, entry["depth"] + 1, comment_id, f"{prefix}-{index}")

    walk(comments, 0, None, "c")
    return flattened


def default_bundle() -> dict[str, Any]:
    return {
        "manifest": {},
        "threads": [],
        "thread_snapshots": [],
        "comments": [],
        "comment_snapshots": [],
        "signals": [],
    }


def load_existing_bundle(output_dir: Path) -> dict[str, Any]:
    bundle = default_bundle()
    if not output_dir.exists():
        return bundle
    for key in bundle.keys():
        path = output_dir / f"{key}.json"
        if not path.exists():
            continue
        try:
            bundle[key] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            bundle[key] = [] if key != "manifest" else {}
    return bundle


def build_thread_entry(study_id: str, record: dict[str, Any], captured_at: str) -> dict[str, Any]:
    thread_id = thread_id_for_record(record)
    created_dt = parse_created_datetime(record)
    created_at = created_dt.isoformat(timespec="seconds") if created_dt else ""
    search_terms = [
        term.strip()
        for term in clean_text(record.get("search_term")).split("|")
        if term.strip()
    ]
    return {
        "thread_id": thread_id,
        "study_id": study_id,
        "source_platform": "reddit",
        "source_type": source_level(record),
        "subreddit": clean_text(record.get("subreddit")),
        "title": clean_text(record.get("title")),
        "url": clean_text(record.get("url")),
        "author": clean_text(record.get("author")),
        "created_at": created_at,
        "current_score": score_int(record.get("score")),
        "current_comment_count": score_int(record.get("num_comments")),
        "status": "tracked",
        "first_seen_at": captured_at,
        "last_seen_at": captured_at,
        "last_harvest_at": captured_at,
        "tracking_priority": (
            "high"
            if urgency_score(record) >= 7.0 or score_int(record.get("num_comments")) >= 20
            else "normal"
        ),
        "pain_category": classify_pain(record),
        "segment_id": classify_row(record),
        "urgency_score": urgency_score(record),
        "specificity_score": specificity_score(record),
        "search_terms": search_terms,
        "comment_capture_state": "captured" if record.get("comments") else "missing",
        "source_endpoint": clean_text(record.get("source_endpoint")),
    }


def build_thread_snapshot(thread: dict[str, Any], record: dict[str, Any], captured_at: str) -> dict[str, Any]:
    return {
        "snapshot_id": stable_id("thread-snapshot", f"{thread['thread_id']}:{captured_at}"),
        "thread_id": thread["thread_id"],
        "captured_at": captured_at,
        "title": clean_text(record.get("title")),
        "body": clean_text(record.get("body")),
        "score": score_int(record.get("score")),
        "comment_count": score_int(record.get("num_comments")),
        "op_reply_count": 0,
        "locked": False,
        "removed": False,
        "deleted": False,
        "page_hash": stable_id("page", f"{record.get('title', '')}:{record.get('body', '')}"),
        "selector_version": SCHEMA_VERSION,
    }


def build_thread_signal(study_id: str, thread: dict[str, Any], captured_at: str) -> dict[str, Any]:
    title = thread["title"].lower()
    signal_type = "vendor_search" if any(token in title for token in ["looking for", "supplier", "3pl", "service"]) else "pain_signal"
    decision_stage = "actively_buying" if any(token in title for token in ["looking for", "need", "recommend"]) else "aware"
    buying_signal = "high" if thread["urgency_score"] >= 7.0 else "medium" if thread["urgency_score"] >= 4.5 else "low"
    return {
        "signal_id": stable_id("signal", f"{thread['thread_id']}:{captured_at}:thread"),
        "study_id": study_id,
        "thread_id": thread["thread_id"],
        "comment_id": None,
        "source_level": "thread",
        "pain_category": thread["pain_category"],
        "problem_context": thread["pain_category"],
        "decision_stage": decision_stage,
        "buying_signal": buying_signal,
        "signal_type": signal_type,
        "solution_mention": None,
        "competitor_mention": None,
        "objection_type": None,
        "stance": "origin",
        "confidence": min(round((thread["specificity_score"] + thread["urgency_score"]) / 20, 2), 0.95),
        "captured_at": captured_at,
    }


def build_comment_signal(study_id: str, thread: dict[str, Any], comment: dict[str, Any], captured_at: str) -> dict[str, Any] | None:
    body = clean_text(comment.get("body")).lower()
    if not body:
        return None

    if any(token in body for token in ["same problem", "same issue", "same here", "me too"]):
        stance = "confirm"
    elif any(token in body for token in ["don't", "not true", "wrong", "disagree"]):
        stance = "contradict"
    elif any(token in body for token in ["use", "try", "recommend", "switch to", "go with"]):
        stance = "recommend"
    else:
        stance = "enrich"

    objection_type = None
    if any(token in body for token in ["expensive", "too much", "overpriced"]):
        objection_type = "too_expensive"
    elif any(token in body for token in ["slow", "delay", "late"]):
        objection_type = "too_slow"
    elif any(token in body for token in ["scam", "fake", "trust"]):
        objection_type = "low_trust"

    solution_mention = None
    for token in ["3pl", "fulfillment", "supplier", "agent", "warehouse"]:
        if token in body:
            solution_mention = token
            break

    return {
        "signal_id": stable_id("signal", f"{comment['comment_id']}:{captured_at}:comment"),
        "study_id": study_id,
        "thread_id": thread["thread_id"],
        "comment_id": comment["comment_id"],
        "source_level": "comment",
        "pain_category": thread["pain_category"],
        "problem_context": thread["pain_category"],
        "decision_stage": "enriching_discussion",
        "buying_signal": "medium" if stance in {"confirm", "recommend"} else "low",
        "signal_type": "comment_signal",
        "solution_mention": solution_mention,
        "competitor_mention": None,
        "objection_type": objection_type,
        "stance": stance,
        "confidence": 0.55 if solution_mention or objection_type else 0.4,
        "captured_at": captured_at,
    }


def summarize_comment_intelligence(threads: list[dict[str, Any]], signals: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = {}
    thread_counts: dict[str, int] = {}
    for thread in threads:
        pain = thread.get("pain_category", "unclear")
        thread_counts[pain] = thread_counts.get(pain, 0) + 1

    for signal in signals:
        if signal.get("source_level") != "comment":
            continue
        pain = signal.get("pain_category", "unclear")
        bucket = buckets.setdefault(
            pain,
            {
                "total": 0,
                "confirm": 0,
                "recommend": 0,
                "contradict": 0,
                "objection": 0,
                "solution_mentions": 0,
            },
        )
        bucket["total"] += 1
        stance = signal.get("stance")
        if stance in {"confirm"}:
            bucket["confirm"] += 1
        if stance in {"recommend"}:
            bucket["recommend"] += 1
        if stance in {"contradict"}:
            bucket["contradict"] += 1
        if signal.get("objection_type"):
            bucket["objection"] += 1
        if signal.get("solution_mention"):
            bucket["solution_mentions"] += 1

    def score_bucket(raw: dict[str, Any], thread_count: int) -> dict[str, Any]:
        total = raw.get("total", 0)
        if total <= 0:
            return {
                **raw,
                "comment_confirmation_score": 0.0,
                "recommendation_density": 0.0,
                "objection_density": 0.0,
            }
        net_confirmation = raw["confirm"] + (raw["recommend"] * 0.5) - raw["contradict"]
        confirmation_score = max(0.0, min(10.0, round(5 + (net_confirmation / total) * 5, 1)))
        denominator = max(thread_count, 1)
        recommendation_density = round(((raw["recommend"] + raw["solution_mentions"]) / denominator), 2)
        objection_density = round(((raw["objection"] + raw["contradict"]) / denominator), 2)
        return {
            **raw,
            "comment_confirmation_score": confirmation_score,
            "recommendation_density": recommendation_density,
            "objection_density": objection_density,
        }

    by_pain = {}
    all_raw = {
        "total": 0,
        "confirm": 0,
        "recommend": 0,
        "contradict": 0,
        "objection": 0,
        "solution_mentions": 0,
    }
    for pain, raw in buckets.items():
        by_pain[pain] = score_bucket(raw, thread_counts.get(pain, 0))
        for key in all_raw:
            all_raw[key] += raw.get(key, 0)

    overall = score_bucket(all_raw, len(threads))
    return {
        "overall": overall,
        "by_pain": by_pain,
    }


def build_entity_bundle(
    records: list[dict[str, Any]],
    study_id: str,
    source_input_path: str | None = None,
    existing_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    captured_at = now_iso()
    existing_bundle = existing_bundle or default_bundle()
    previous_manifest = existing_bundle.get("manifest", {}) or {}
    existing_threads_map = {
        item.get("thread_id"): dict(item)
        for item in existing_bundle.get("threads", [])
        if isinstance(item, dict) and item.get("thread_id")
    }
    existing_comments_map = {
        item.get("comment_id"): dict(item)
        for item in existing_bundle.get("comments", [])
        if isinstance(item, dict) and item.get("comment_id")
    }
    thread_snapshots: list[dict[str, Any]] = list(existing_bundle.get("thread_snapshots", []))
    comment_snapshots: list[dict[str, Any]] = list(existing_bundle.get("comment_snapshots", []))
    signals: list[dict[str, Any]] = list(existing_bundle.get("signals", []))
    threads_by_id: dict[str, dict[str, Any]] = {key: dict(value) for key, value in existing_threads_map.items()}
    comments_by_id: dict[str, dict[str, Any]] = {key: dict(value) for key, value in existing_comments_map.items()}
    new_thread_count = 0
    refreshed_thread_count = 0
    new_comment_count = 0

    for record in records:
        thread = build_thread_entry(study_id, record, captured_at)
        existing = threads_by_id.get(thread["thread_id"])
        if existing:
            refreshed_thread_count += 1
            existing["current_score"] = max(existing["current_score"], thread["current_score"])
            existing["current_comment_count"] = max(existing["current_comment_count"], thread["current_comment_count"])
            existing["last_seen_at"] = captured_at
            existing["last_harvest_at"] = captured_at
            existing["source_type"] = thread["source_type"]
            existing["tracking_priority"] = "high" if "high" in {existing.get("tracking_priority"), thread["tracking_priority"]} else "normal"
            existing_terms = set(existing.get("search_terms", []))
            existing["search_terms"] = sorted(existing_terms.union(thread.get("search_terms", [])))
            existing["urgency_score"] = max(float(existing.get("urgency_score", 0)), float(thread["urgency_score"]))
            existing["specificity_score"] = max(float(existing.get("specificity_score", 0)), float(thread["specificity_score"]))
            existing["pain_category"] = thread["pain_category"] if existing.get("pain_category") == "unclear" else existing.get("pain_category")
            existing["segment_id"] = thread["segment_id"] if existing.get("segment_id") == "operating_aware" else existing.get("segment_id")
            existing["harvest_count"] = score_int(existing.get("harvest_count", 1)) + 1
            if not existing.get("created_at") and thread.get("created_at"):
                existing["created_at"] = thread["created_at"]
            if existing.get("comment_capture_state") != "captured" and record.get("comments"):
                existing["comment_capture_state"] = "captured"
        else:
            new_thread_count += 1
            thread["harvest_count"] = 1
            threads_by_id[thread["thread_id"]] = thread

        thread_snapshots.append(build_thread_snapshot(thread, record, captured_at))
        signals.append(build_thread_signal(study_id, thread, captured_at))

        flattened_comments = flatten_comments(thread["thread_id"], record.get("comments") or [])
        if flattened_comments:
            threads_by_id[thread["thread_id"]]["comment_capture_state"] = "captured"
        for comment in flattened_comments:
            existing_comment = comments_by_id.get(comment["comment_id"])
            if existing_comment:
                existing_comment["last_seen_at"] = captured_at
                existing_comment["depth"] = max(score_int(existing_comment.get("depth")), comment["depth"])
                existing_comment["parent_id"] = existing_comment.get("parent_id") or comment["parent_id"]
                existing_comment["permalink"] = existing_comment.get("permalink") or comment["permalink"]
                existing_comment["thread_id"] = comment["thread_id"]
                existing_comment["status"] = "tracked"
            else:
                new_comment_count += 1
                comments_by_id[comment["comment_id"]] = {
                    "comment_id": comment["comment_id"],
                    "thread_id": comment["thread_id"],
                    "parent_id": comment["parent_id"],
                    "author": comment["author"],
                    "depth": comment["depth"],
                    "permalink": comment["permalink"],
                    "first_seen_at": captured_at,
                    "last_seen_at": captured_at,
                    "status": "tracked",
                }
            comment_snapshots.append(
                {
                    "snapshot_id": stable_id("comment-snapshot", f"{comment['comment_id']}:{captured_at}"),
                    "comment_id": comment["comment_id"],
                    "captured_at": captured_at,
                    "body": comment["body"],
                    "score": comment["score"],
                    "is_op_reply": comment["is_op_reply"],
                    "awards_count": comment["awards_count"],
                    "selector_version": SCHEMA_VERSION,
                }
            )
            signal = build_comment_signal(study_id, thread, comment, captured_at)
            if signal:
                signals.append(signal)

    comments = sorted(comments_by_id.values(), key=lambda item: (item["thread_id"], item["comment_id"]))
    threads = sorted(threads_by_id.values(), key=lambda item: (item["tracking_priority"] != "high", -item["current_comment_count"], -item["current_score"]))
    thread_with_comments_count = sum(1 for thread in threads if thread.get("comment_capture_state") == "captured")
    pain_breakdown: dict[str, int] = {}
    for thread in threads:
        pain_breakdown[thread["pain_category"]] = pain_breakdown.get(thread["pain_category"], 0) + 1

    comment_capture_rate = round((thread_with_comments_count / len(threads)) * 100, 1) if threads else 0.0
    comment_intelligence = summarize_comment_intelligence(threads, signals)
    data_gaps = []
    if not comments:
        data_gaps.append("评论尚未采集，当前结论仍以 thread 标题与正文为主。")
    elif comment_capture_rate < 50:
        data_gaps.append("评论覆盖率仍偏低，评论信号会影响推荐密度与异议密度置信度。")
    if any(not thread.get("created_at") for thread in threads):
        data_gaps.append("部分 thread 缺少稳定时间戳，趋势判断需降低置信度。")

    manifest = {
        "study_id": study_id,
        "schema_version": SCHEMA_VERSION,
        "built_at": captured_at,
        "source_input_path": source_input_path or "",
        "thread_count": len(threads),
        "thread_snapshot_count": len(thread_snapshots),
        "comment_count": len(comments),
        "comment_snapshot_count": len(comment_snapshots),
        "signal_count": len(signals),
        "thread_with_comments_count": thread_with_comments_count,
        "comment_capture_rate": comment_capture_rate,
        "comment_capture_state": (
            "full" if threads and thread_with_comments_count == len(threads)
            else "partial" if thread_with_comments_count
            else "thread_only"
        ),
        "freshness": {
            "last_entity_refresh_at": captured_at,
            "freshness_score": 90 if source_input_path else 60,
        },
        "refresh": {
            "build_number": score_int(previous_manifest.get("refresh", {}).get("build_number", 0)) + 1,
            "incremental_mode": "merge" if previous_manifest else "bootstrap",
            "new_threads": new_thread_count,
            "refreshed_threads": refreshed_thread_count,
            "new_comments": new_comment_count,
        },
        "coverage": {
            "thread_coverage": 100 if threads else 0,
            "comment_coverage": comment_capture_rate,
        },
        "pain_breakdown": pain_breakdown,
        "comment_intelligence": comment_intelligence,
        "data_gaps": data_gaps,
    }

    return {
        "manifest": manifest,
        "threads": threads,
        "thread_snapshots": thread_snapshots,
        "comments": comments,
        "comment_snapshots": comment_snapshots,
        "signals": signals,
    }


def write_entity_bundle(output_dir: Path, bundle: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key in ["manifest", "threads", "thread_snapshots", "comments", "comment_snapshots", "signals"]:
        path = output_dir / f"{key}.json"
        path.write_text(json.dumps(bundle[key], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths[key] = path
    return paths


def build_and_write_store(input_path: Path, study_id: str, output_dir: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    records = read_jsonl(input_path)
    bundle = build_entity_bundle(
        records,
        study_id=study_id,
        source_input_path=str(input_path),
        existing_bundle=load_existing_bundle(output_dir),
    )
    paths = write_entity_bundle(output_dir, bundle)
    return bundle, paths


def main() -> None:
    args = parse_args()
    bundle, paths = build_and_write_store(Path(args.input), args.study_id, Path(args.output_dir))
    print(f"Study entity store built: {args.study_id}")
    print(f"Threads: {bundle['manifest']['thread_count']}")
    print(f"Comments: {bundle['manifest']['comment_count']}")
    print(f"Manifest: {paths['manifest']}")


if __name__ == "__main__":
    main()
