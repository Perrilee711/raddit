#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime
from typing import Any


def score_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        return None


def config_value(config: dict[str, Any], key: str, default: int | float) -> int | float:
    value = config.get(key, default)
    try:
        if isinstance(default, int):
            return int(value)
        return float(value)
    except (TypeError, ValueError):
        return default


def rank_hot_threads(
    threads: list[dict[str, Any]],
    config: dict[str, Any],
    reference_time: datetime | None = None,
) -> list[dict[str, Any]]:
    now = reference_time or datetime.now()
    min_comments = int(config_value(config, "hot_thread_min_comments", 5))
    min_score = int(config_value(config, "hot_thread_min_score", 3))
    max_age_hours = float(config_value(config, "hot_thread_max_age_hours", 168))
    stale_after_hours = float(config_value(config, "hot_thread_stale_after_hours", 8))
    min_refresh_gap_minutes = int(config_value(config, "hot_thread_min_refresh_gap_minutes", 45))

    ranked: list[dict[str, Any]] = []

    for thread in threads:
        url = str(thread.get("url", "")).strip()
        if not url:
            continue

        created_at = parse_iso(thread.get("created_at"))
        last_seen_at = parse_iso(thread.get("last_seen_at"))
        last_harvest_at = parse_iso(thread.get("last_harvest_at"))
        activity_anchor = last_seen_at or last_harvest_at or created_at
        hours_since_activity = (
            max(0.0, (now - activity_anchor).total_seconds() / 3600) if activity_anchor else max_age_hours + 1
        )
        hours_since_created = (
            max(0.0, (now - created_at).total_seconds() / 3600) if created_at else hours_since_activity
        )
        if hours_since_activity > max_age_hours:
            continue

        hours_since_harvest = (
            max(0.0, (now - last_harvest_at).total_seconds() / 3600) if last_harvest_at else max_age_hours
        )
        if last_harvest_at and (hours_since_harvest * 60) < min_refresh_gap_minutes:
            continue

        comment_count = score_int(thread.get("current_comment_count"))
        score = score_int(thread.get("current_score"))
        tracking_priority = str(thread.get("tracking_priority", "normal")).strip() or "normal"
        comment_capture_state = str(thread.get("comment_capture_state", "missing")).strip() or "missing"
        needs_comments = comment_capture_state != "captured"
        stale = hours_since_harvest >= stale_after_hours or needs_comments
        eligible = (
            tracking_priority == "high"
            or comment_count >= min_comments
            or score >= min_score
            or needs_comments
        )
        if not eligible:
            continue

        hot_score = 0.0
        hot_score += 45 if tracking_priority == "high" else 15
        hot_score += min(comment_count, 120) * 1.2
        hot_score += min(score, 300) * 0.18
        hot_score += min(hours_since_harvest, 48) * 1.15
        hot_score += 18 if needs_comments else 0
        hot_score += 10 if stale else 0
        hot_score += 8 if hours_since_created <= 24 else 0

        ranked.append(
            {
                "thread_id": thread.get("thread_id"),
                "title": thread.get("title", ""),
                "url": url,
                "subreddit": thread.get("subreddit", ""),
                "tracking_priority": tracking_priority,
                "comment_capture_state": comment_capture_state,
                "current_comment_count": comment_count,
                "current_score": score,
                "hours_since_activity": round(hours_since_activity, 1),
                "hours_since_created": round(hours_since_created, 1),
                "hours_since_harvest": round(hours_since_harvest, 1),
                "stale": stale,
                "needs_comments": needs_comments,
                "hot_score": round(hot_score, 1),
                "search_terms": thread.get("search_terms", []),
            }
        )

    ranked.sort(
        key=lambda item: (
            item["tracking_priority"] != "high",
            not item["stale"],
            -item["hot_score"],
            -item["current_comment_count"],
            -item["current_score"],
        )
    )
    return ranked


def summarize_hot_threads(
    threads: list[dict[str, Any]],
    config: dict[str, Any],
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    ranked = rank_hot_threads(threads, config, reference_time=reference_time)
    max_count = int(config_value(config, "hot_thread_max_count", 12))
    selected = ranked[:max_count]
    stale_count = sum(1 for item in ranked if item.get("stale"))
    missing_comment_count = sum(1 for item in ranked if item.get("needs_comments"))
    high_priority_count = sum(1 for item in ranked if item.get("tracking_priority") == "high")
    recommendation = "hot_threads" if selected else "browser"
    return {
        "mode": "hot_threads",
        "candidate_count": len(ranked),
        "selected_count": len(selected),
        "stale_candidate_count": stale_count,
        "high_priority_candidate_count": high_priority_count,
        "missing_comment_capture_count": missing_comment_count,
        "recommended_mode": recommendation,
        "thresholds": {
            "max_count": max_count,
            "min_comments": int(config_value(config, "hot_thread_min_comments", 5)),
            "min_score": int(config_value(config, "hot_thread_min_score", 3)),
            "max_age_hours": float(config_value(config, "hot_thread_max_age_hours", 168)),
            "stale_after_hours": float(config_value(config, "hot_thread_stale_after_hours", 8)),
            "min_refresh_gap_minutes": int(config_value(config, "hot_thread_min_refresh_gap_minutes", 45)),
        },
        "selected_threads": selected,
    }
