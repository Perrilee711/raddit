#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


PAIN_CATEGORIES = {
    "fulfillment_setup": {
        "label": "履约与发货",
        "keywords": [
            "3pl",
            "fulfillment",
            "shipping",
            "warehouse",
            "consolidation",
            "delivery",
            "fulfillment partner",
            "fulfillment center",
            "shipping delays",
            "slow shipping",
            "shipping times",
            "faster shipping",
        ],
        "offer": "3PL & Fulfillment Audit",
        "fishgoo_fit": 10.0,
        "monetization": 9.0,
        "packaging_base": 82.0,
        "segment_name": "运营期 / 替换中 / 履约与发货",
        "pain_summary": "发货慢、退款增加、3PL 结构不清楚",
        "trend": "样本最强",
        "action_mode": "立即测试",
        "problem_context": "履约与发货",
        "promise": "先找出延迟和退款背后的真正 bottleneck，再决定该不该换方案。",
        "format": "轻审查 / 诊断型服务",
        "angle": "不是先换 supplier，而是先找出到底哪一段在拖慢发货。",
        "avoid": "不要先卖泛 sourcing、泛供应链优化。",
    },
    "supplier_match": {
        "label": "供应商与采购",
        "keywords": [
            "supplier",
            "private supplier",
            "private agent",
            "agent",
            "sourcing",
            "china supplier",
            "vendor",
            "find supplier",
            "reliable supplier",
            "bad supplier",
            "supplier issues",
            "agent/supplier",
        ],
        "offer": "Supplier Match Sprint",
        "fishgoo_fit": 9.0,
        "monetization": 8.0,
        "packaging_base": 68.0,
        "segment_name": "扩张期 / 求解中 / 供应商与采购",
        "pain_summary": "想找 private supplier，但担心稳定性和执行能力",
        "trend": "第二主线",
        "action_mode": "第二优先级测试",
        "problem_context": "供应商与采购",
        "promise": "不是给你一堆名单，而是给你适合当前阶段的 supplier 路径。",
        "format": "匹配建议 / 结构化评估",
        "angle": "先判断你到底需要 supplier、agent，还是 supplier + fulfillment 组合。",
        "avoid": "不要包装成“万能 sourcing 代办”。",
    },
    "china_risk_control": {
        "label": "质量与风险",
        "keywords": [
            "scam",
            "fake",
            "quality",
            "qc",
            "inspection",
            "refund",
            "wrong item",
            "damaged",
            "supplier scam",
            "fake supplier",
            "quality issue",
            "quality issues",
            "product quality",
        ],
        "offer": "China Buying Risk Check",
        "fishgoo_fit": 8.0,
        "monetization": 6.0,
        "packaging_base": 56.0,
        "segment_name": "运营期 / 认知中 / 质量与风险",
        "pain_summary": "QC 不稳、错发漏发、fake supplier 风险",
        "trend": "支持型主题",
        "action_mode": "继续观察",
        "problem_context": "质量与风险",
        "promise": "先识别供应与质检链路里的主要风险，再决定要不要进入重交付。",
        "format": "风险检查 / 支持型服务",
        "angle": "把风险和质量波动先讲清楚，再延伸到 QC 与 seller coordination。",
        "avoid": "不要直接包装成重交付方案。",
    },
    "cost_down": {
        "label": "成本与利润",
        "keywords": [
            "margin",
            "packaging",
            "cost",
            "landed cost",
            "profit",
            "expensive shipping",
            "pricing",
            "tariff",
            "shipping cost",
            "packaging cost",
            "profit margin",
            "cost down",
            "too expensive",
        ],
        "offer": "Cost-Down Review",
        "fishgoo_fit": 7.0,
        "monetization": 7.0,
        "packaging_base": 52.0,
        "segment_name": "验证期 / 比较中 / 成本与利润",
        "pain_summary": "成本压力真实存在，但还不是最锋利的购买入口",
        "trend": "补充卖点",
        "action_mode": "暂缓投入",
        "problem_context": "成本与利润",
        "promise": "先定位利润被哪一段吃掉，再决定该从 packaging、shipping 还是 sourcing 下手。",
        "format": "复盘 / 分析型服务",
        "angle": "适合做 supporting offer，不适合做第一主打。",
        "avoid": "不要把它当成首页主入口。",
    },
}

SEGMENT_ROWS = [
    {
        "id": "operating_replacing",
        "label": "运营期 / 替换中",
        "keywords": [
            "3pl",
            "fulfillment",
            "shipping",
            "refund",
            "delay",
            "slow",
            "need help",
            "service",
            "replace",
            "switch",
        ],
    },
    {
        "id": "expansion_seeking",
        "label": "扩张期 / 求解中",
        "keywords": [
            "looking for",
            "private supplier",
            "private agent",
            "sourcing agent",
            "reliable supplier",
            "partner",
            "china supplier",
        ],
    },
    {
        "id": "validation_comparing",
        "label": "验证期 / 比较中",
        "keywords": [
            "beginner",
            "starting",
            "new to",
            "just started",
            "cost",
            "margin",
            "pricing",
            "landed cost",
            "too expensive",
        ],
    },
    {
        "id": "operating_aware",
        "label": "运营期 / 认知中",
        "keywords": [
            "quality",
            "qc",
            "inspection",
            "scam",
            "fake supplier",
            "wrong item",
            "issue",
        ],
    },
]

PAIN_ORDER = ["supplier_match", "fulfillment_setup", "china_risk_control", "cost_down"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Demand Intelligence dashboard payload from Reddit JSONL."
    )
    parser.add_argument("--input", required=True, help="Path to raw Reddit JSONL.")
    parser.add_argument("--json-output", required=True, help="Path to JSON payload output.")
    parser.add_argument("--js-output", required=True, help="Path to JS payload output.")
    parser.add_argument(
        "--study-title",
        default="美国 dropshipping / 履约与 supplier 问题",
        help="Study title shown in the dashboard.",
    )
    parser.add_argument(
        "--market",
        default="美国 dropshipping",
        help="Market label shown in the dashboard.",
    )
    parser.add_argument(
        "--date-range",
        default="最新 564 条定向采样",
        help="Date range / sampling label shown in the dashboard.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def iter_comment_bodies(comments: Any, limit: int = 12) -> list[str]:
    bodies: list[str] = []

    def walk(items: Any) -> None:
        if len(bodies) >= limit or not isinstance(items, list):
            return
        for item in items:
            if len(bodies) >= limit:
                return
            if not isinstance(item, dict):
                continue
            body = str(item.get("body") or item.get("text") or "").strip()
            if body:
                bodies.append(body)
            walk(item.get("replies"))

    walk(comments)
    return bodies


def comment_count(record: dict[str, Any]) -> int:
    return len(iter_comment_bodies(record.get("comments"), limit=999))


def iter_comment_dicts(comments: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            rows.append(item)
            walk(item.get("replies"))

    walk(comments)
    return rows


def content_text(record: dict[str, Any]) -> str:
    discussion = " ".join(iter_comment_bodies(record.get("comments")))
    return f"{record.get('title', '')} {record.get('body', '')} {discussion}".lower()


def text_of(record: dict[str, Any]) -> str:
    text = content_text(record).strip()
    if text:
        return text
    return str(record.get("search_term", "")).lower()


def keyword_in_text(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<!\w){escaped}(?!\w)"
    return re.search(pattern, text) is not None


def engagement(record: dict[str, Any]) -> int:
    try:
        return int(float(record.get("score", 0) or 0)) + int(float(record.get("num_comments", 0) or 0))
    except (TypeError, ValueError):
        return 0


def urgency_score(record: dict[str, Any]) -> float:
    text = content_text(record) or text_of(record)
    score = 0.0
    if any(
        keyword_in_text(text, token)
        for token in [
            "looking for",
            "need help",
            "need advice",
            "service",
            "partner",
            "reliable",
            "private supplier",
            "3pl",
            "fulfillment",
        ]
    ):
        score += 6.0
    keyword_hits = sum(
        1
        for category in PAIN_CATEGORIES.values()
        for keyword in category["keywords"]
        if keyword_in_text(text, keyword)
    )
    score += min(keyword_hits, 4) * 0.6
    score += min(engagement(record), 50) / 10.0
    return min(score, 10.0)


def specificity_score(record: dict[str, Any]) -> float:
    text = content_text(record) or text_of(record)
    score = 2.0
    if any(keyword_in_text(text, token) for token in ["looking for", "need", "how to find", "recommend", "service"]):
        score += 3.0
    score += min(
        sum(
            1
            for token in ["3pl", "fulfillment", "shipping", "supplier", "agent", "margin", "qc"]
            if keyword_in_text(text, token)
        ),
        4,
    )
    return min(score, 10.0)


def classify_pain(record: dict[str, Any]) -> str:
    text = content_text(record) or text_of(record)
    best_key = "unclear"
    best_hits = 0
    for key, config in PAIN_CATEGORIES.items():
        hits = sum(1 for keyword in config["keywords"] if keyword_in_text(text, keyword))
        if hits > best_hits:
            best_key = key
            best_hits = hits
    return best_key


def classify_row(record: dict[str, Any]) -> str:
    text = content_text(record) or text_of(record)
    best_id = "operating_aware"
    best_hits = 0
    for row in SEGMENT_ROWS:
        hits = sum(1 for keyword in row["keywords"] if keyword_in_text(text, keyword))
        if hits > best_hits:
            best_id = row["id"]
            best_hits = hits
    return best_id


def priority_score(
    volume_score: float,
    avg_urgency: float,
    fishgoo_fit: float,
    monetization: float,
    comment_confirmation_score: float = 0.0,
    recommendation_density: float = 0.0,
    objection_density: float = 0.0,
) -> float:
    raw = (
        (volume_score * 0.32)
        + (avg_urgency * 0.23)
        + (fishgoo_fit * 0.23)
        + (monetization * 0.14)
        + (comment_confirmation_score * 0.05)
        + (recommendation_density * 0.04)
        - (objection_density * 0.03)
    )
    return round(raw * 10, 1)


def packaging_score(
    base: float,
    avg_specificity: float,
    avg_urgency: float,
    count: int,
    max_count: int,
    comment_confirmation_score: float = 0.0,
    recommendation_density: float = 0.0,
    objection_density: float = 0.0,
) -> int:
    evidence_strength = (count / max_count) * 10 if max_count else 0
    score = (
        (base * 0.72)
        + (avg_specificity * 1.9)
        + (avg_urgency * 1.1)
        + (evidence_strength * 0.65)
        + (comment_confirmation_score * 1.1)
        + (recommendation_density * 1.2)
        - (objection_density * 0.9)
    )
    return max(40, min(int(round(score)), 92))


def confidence_label(count: int, high_urgency_count: int, comment_signal_count: int = 0, comment_coverage_rate: float = 0.0) -> str:
    if count >= 80 and high_urgency_count >= 20 and comment_coverage_rate >= 20:
        return "High"
    if count >= 80 and high_urgency_count >= 20:
        return "High"
    if count >= 30 or comment_signal_count >= 8:
        return "Medium"
    return "Low"


def derive_comment_signal_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_pain: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "comment_signal_count": 0,
            "confirm_count": 0,
            "recommend_count": 0,
            "contradict_count": 0,
            "objection_count": 0,
            "solution_mention_count": 0,
            "sample_comments": [],
        }
    )

    for record in records:
        pain = classify_pain(record)
        bucket = by_pain[pain]
        for comment in iter_comment_dicts(record.get("comments")):
            body = str(comment.get("body") or comment.get("text") or "").strip()
            if not body:
                continue
            lower = body.lower()
            bucket["comment_signal_count"] += 1
            if any(token in lower for token in ["same problem", "same issue", "same here", "me too"]):
                bucket["confirm_count"] += 1
            if any(token in lower for token in ["use", "try", "recommend", "switch to", "go with"]):
                bucket["recommend_count"] += 1
            if any(token in lower for token in ["don't", "not true", "wrong", "disagree"]):
                bucket["contradict_count"] += 1
            if any(token in lower for token in ["expensive", "too much", "overpriced", "slow", "delay", "late", "scam", "fake", "trust"]):
                bucket["objection_count"] += 1
            if any(token in lower for token in ["3pl", "fulfillment", "supplier", "agent", "warehouse"]):
                bucket["solution_mention_count"] += 1
            if len(bucket["sample_comments"]) < 3:
                bucket["sample_comments"].append(body[:140])

    thread_counts_by_pain = Counter(classify_pain(record) for record in records)
    normalized_by_pain: dict[str, dict[str, Any]] = {}
    overall = {
        "comment_signal_count": 0,
        "confirm_count": 0,
        "recommend_count": 0,
        "contradict_count": 0,
        "objection_count": 0,
        "solution_mention_count": 0,
        "sample_comments": [],
    }
    for pain, bucket in by_pain.items():
        total = bucket["comment_signal_count"]
        thread_count = max(thread_counts_by_pain.get(pain, 0), 1)
        net_confirmation = bucket["confirm_count"] + (bucket["recommend_count"] * 0.5) - bucket["contradict_count"]
        normalized = {
            **bucket,
            "comment_confirmation_score": max(0.0, min(10.0, round(5 + (net_confirmation / max(total, 1)) * 5, 1))) if total else 0.0,
            "recommendation_density": round((bucket["recommend_count"] + bucket["solution_mention_count"]) / thread_count, 2),
            "objection_density": round((bucket["objection_count"] + bucket["contradict_count"]) / thread_count, 2),
        }
        normalized_by_pain[pain] = normalized
        for key in overall:
            if key == "sample_comments":
                overall[key].extend(bucket[key][: max(0, 5 - len(overall[key]))])
            else:
                overall[key] += bucket[key]

    total_comments = overall["comment_signal_count"]
    overall["comment_confirmation_score"] = (
        max(
            0.0,
            min(
                10.0,
                round(
                    5
                    + (
                        (
                            overall["confirm_count"]
                            + (overall["recommend_count"] * 0.5)
                            - overall["contradict_count"]
                        )
                        / max(total_comments, 1)
                    )
                    * 5,
                    1,
                ),
            ),
        )
        if total_comments
        else 0.0
    )
    overall["recommendation_density"] = round(
        (overall["recommend_count"] + overall["solution_mention_count"]) / max(len(records), 1), 2
    )
    overall["objection_density"] = round(
        (overall["objection_count"] + overall["contradict_count"]) / max(len(records), 1), 2
    )
    return {"overall": overall, "by_pain": normalized_by_pain}


def resolve_comment_signal_metrics(records: list[dict[str, Any]], entity_bundle: dict[str, Any] | None) -> dict[str, Any]:
    manifest_metrics = ((entity_bundle or {}).get("manifest", {}) or {}).get("comment_intelligence")
    if manifest_metrics:
        return manifest_metrics
    return derive_comment_signal_metrics(records)


def normalize_heat(value: int, row_max: int) -> tuple[int, str]:
    if row_max <= 0:
        return 0, "low"
    score = int(round((value / row_max) * 100))
    if score >= 70:
        level = "high"
    elif score >= 35:
        level = "mid"
    else:
        level = "low"
    return score, level


def parse_created_datetime(record: dict[str, Any]) -> datetime | None:
    raw = record.get("created_utc")
    if raw in (None, ""):
        return None
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        if text.isdigit():
            return datetime.fromtimestamp(int(text))
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (OverflowError, OSError, ValueError):
        return None


def sequence_labels(bucket_count: int) -> list[str]:
    return [f"窗口 {index + 1}" for index in range(bucket_count)]


def build_trend_series(records: list[dict[str, Any]], pain_groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    bucket_count = 6
    dated_records = [(record, parse_created_datetime(record)) for record in records]
    valid_dated = [(record, dt) for record, dt in dated_records if dt is not None]

    if valid_dated and len(valid_dated) >= max(8, int(len(records) * 0.25)):
        valid_dated.sort(key=lambda item: item[1])
        buckets = [[] for _ in range(bucket_count)]
        labels = []
        for index, item in enumerate(valid_dated):
            bucket_index = min(int(index / max(len(valid_dated), 1) * bucket_count), bucket_count - 1)
            buckets[bucket_index].append(item[0])
        for bucket in buckets:
            if bucket:
                first_dt = parse_created_datetime(bucket[0])
                last_dt = parse_created_datetime(bucket[-1])
                if first_dt and last_dt:
                    labels.append(f"{first_dt.month}/{first_dt.day}-{last_dt.month}/{last_dt.day}")
                else:
                    labels.append("时间窗口")
            else:
                labels.append("时间窗口")
        mode = "dated"
    else:
        ordered = list(records)
        buckets = [[] for _ in range(bucket_count)]
        for index, record in enumerate(ordered):
            bucket_index = min(int(index / max(len(ordered), 1) * bucket_count), bucket_count - 1)
            buckets[bucket_index].append(record)
        labels = sequence_labels(bucket_count)
        mode = "sample_sequence"

    def period_comparison(values: list[int]) -> dict[str, Any]:
        midpoint = max(1, len(values) // 2)
        previous_period = values[:midpoint]
        current_period = values[midpoint:]
        previous_total = sum(previous_period)
        current_total = sum(current_period)
        delta = current_total - previous_total
        if previous_total > 0:
            percent = round((delta / previous_total) * 100, 1)
        elif current_total > 0:
            percent = 100.0
        else:
            percent = 0.0
        if delta > 0:
            explanation = f"较上一周期上升 {delta}（{percent:+.1f}%）"
        elif delta < 0:
            explanation = f"较上一周期下降 {abs(delta)}（{percent:+.1f}%）"
        else:
            explanation = "较上一周期基本持平"
        return {
            "current": current_total,
            "previous": previous_total,
            "delta": delta,
            "percent": percent,
            "explanation": explanation,
        }

    def anomaly_points(values: list[int], labels: list[str]) -> list[dict[str, Any]]:
        if len(values) < 4:
            return []
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        std_dev = math.sqrt(variance)
        threshold = max(2.0, std_dev * 1.5)
        anomalies = []
        for index, value in enumerate(values):
            delta_from_mean = value - mean
            if abs(delta_from_mean) < threshold:
                continue
            anomaly_type = "spike" if delta_from_mean > 0 else "dip"
            anomalies.append(
                {
                    "index": index,
                    "label": labels[index] if index < len(labels) else f"窗口 {index + 1}",
                    "value": value,
                    "type": anomaly_type,
                    "explanation": "异常上冲" if anomaly_type == "spike" else "异常回落",
                }
            )
        return anomalies

    series = []
    for pain_id in PAIN_ORDER[:3]:
        label = PAIN_CATEGORIES[pain_id]["label"]
        values = []
        for bucket in buckets:
            count = sum(1 for record in bucket if classify_pain(record) == pain_id)
            values.append(count)
        previous = values[-2] if len(values) > 1 else 0
        latest = values[-1] if values else 0
        delta = latest - previous
        series.append(
            {
                "id": pain_id,
                "label": label,
                "values": values,
                "latest": latest,
                "delta": delta,
                "periodComparison": period_comparison(values),
                "anomalies": anomaly_points(values, labels),
            }
        )

    lead_series = max(series, key=lambda item: item["latest"], default={"label": "N/A", "delta": 0})
    anomaly_total = sum(len(item.get("anomalies", [])) for item in series)
    top_mover = max(series, key=lambda item: abs(item.get("periodComparison", {}).get("delta", 0)), default=None)
    return {
        "mode": mode,
        "labels": labels,
        "series": series,
        "headline": f"最近 6 个窗口里，{lead_series['label']} 的末端信号最强。",
        "note": "如果原始数据没有稳定时间戳，系统会按样本顺序窗口近似趋势。",
        "comparisonSummary": (
            f"{top_mover['label']} {top_mover['periodComparison']['explanation']}"
            if top_mover
            else "暂无周期对比结论"
        ),
        "anomalySummary": (
            f"共识别到 {anomaly_total} 个异常波动窗口"
            if anomaly_total
            else "本窗口没有明显异常波动"
        ),
    }


def build_trend_views(records: list[dict[str, Any]], pain_groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    dated_records = [(record, parse_created_datetime(record)) for record in records]
    valid_dated = [(record, dt) for record, dt in dated_records if dt is not None]
    views = []

    if valid_dated and len(valid_dated) >= max(10, int(len(records) * 0.25)):
        latest_dt = max(dt for _, dt in valid_dated)
        for key, label, days in [("7d", "近7天", 7), ("30d", "近30天", 30), ("90d", "近90天", 90)]:
            cutoff = latest_dt - timedelta(days=days)
            subset = [record for record, dt in valid_dated if dt >= cutoff]
            if len(subset) < 8:
                continue
            trend = build_trend_series(subset, pain_groups)
            views.append(
                {
                    "key": key,
                    "label": label,
                    "recordCount": len(subset),
                    **trend,
                }
            )

    full_view = build_trend_series(records, pain_groups)
    views.append(
        {
            "key": "all",
            "label": "全量样本",
            "recordCount": len(records),
            **full_view,
        }
    )

    default_key = "30d" if any(view["key"] == "30d" for view in views) else views[0]["key"]
    selected = next((view for view in views if view["key"] == default_key), views[0])
    return {
        "defaultKey": default_key,
        "views": views,
        "mode": selected["mode"],
        "labels": selected["labels"],
        "series": selected["series"],
        "headline": selected["headline"],
        "note": selected["note"],
    }


def build_payload(
    records: list[dict[str, Any]],
    study_title: str,
    market: str,
    date_range: str,
    entity_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = (entity_bundle or {}).get("manifest", {}) if isinstance(entity_bundle, dict) else {}
    hot_refresh = manifest.get("hot_refresh", {}) if isinstance(manifest, dict) else {}
    pain_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    row_matrix: dict[str, Counter[str]] = defaultdict(Counter)
    subreddit_counter: Counter[str] = Counter()
    search_term_counter: Counter[str] = Counter()
    comment_enriched_records = 0
    total_comment_count = 0

    for record in records:
        pain = classify_pain(record)
        pain_groups[pain].append(record)
        row_matrix[classify_row(record)][pain] += 1
        subreddit = str(record.get("subreddit", "")).strip()
        if subreddit:
            subreddit_counter[subreddit] += 1
        search_term = str(record.get("search_term", "")).strip()
        if search_term:
            search_term_counter[search_term] += 1
        captured_comments = comment_count(record)
        if captured_comments:
            comment_enriched_records += 1
            total_comment_count += captured_comments

    comment_signal_metrics = resolve_comment_signal_metrics(records, entity_bundle)
    overall_comment_metrics = comment_signal_metrics.get("overall", {})
    comment_coverage_rate = round((comment_enriched_records / len(records)) * 100, 1) if records else 0.0

    filtered_counts = {key: len(pain_groups.get(key, [])) for key in PAIN_ORDER}
    max_count = max(filtered_counts.values(), default=1)

    opportunities: list[dict[str, Any]] = []
    for key in PAIN_ORDER:
        config = PAIN_CATEGORIES[key]
        items = pain_groups.get(key, [])
        count = len(items)
        if not count:
            continue
        avg_urgency = round(sum(urgency_score(item) for item in items) / count, 1)
        avg_specificity = round(sum(specificity_score(item) for item in items) / count, 1)
        high_urgency_count = sum(1 for item in items if urgency_score(item) >= 7.0)
        volume_score = round((count / max_count) * 10, 1) if max_count else 0.0
        pain_comment_metrics = comment_signal_metrics.get("by_pain", {}).get(key, {})
        comment_confirmation_score = float(pain_comment_metrics.get("comment_confirmation_score", 0.0))
        recommendation_density = float(pain_comment_metrics.get("recommendation_density", 0.0))
        objection_density = float(pain_comment_metrics.get("objection_density", 0.0))
        comment_signal_count = int(pain_comment_metrics.get("comment_signal_count", 0))
        opportunity = priority_score(
            volume_score,
            avg_urgency,
            config["fishgoo_fit"],
            config["monetization"],
            comment_confirmation_score,
            recommendation_density,
            objection_density,
        )
        packaging = packaging_score(
            config["packaging_base"],
            avg_specificity,
            avg_urgency,
            count,
            max_count,
            comment_confirmation_score,
            recommendation_density,
            objection_density,
        )
        opportunities.append(
            {
                "id": key,
                "count": count,
                "volume_score": volume_score,
                "avg_urgency": avg_urgency,
                "avg_specificity": avg_specificity,
                "high_urgency_count": high_urgency_count,
                "opportunity": opportunity,
                "packaging": packaging,
                "confidence": confidence_label(count, high_urgency_count, comment_signal_count, comment_coverage_rate),
                "comment_confirmation_score": comment_confirmation_score,
                "recommendation_density": recommendation_density,
                "objection_density": objection_density,
                "comment_signal_count": comment_signal_count,
                "sample_comments": pain_comment_metrics.get("sample_comments", []),
            }
        )

    opportunities.sort(key=lambda item: item["opportunity"], reverse=True)
    lead = opportunities[0]
    secondary = opportunities[1] if len(opportunities) > 1 else opportunities[0]
    trend_series = build_trend_views(records, pain_groups)
    lead_trend = next((item for item in trend_series["series"] if item["id"] == lead["id"]), None)
    secondary_trend = next((item for item in trend_series["series"] if item["id"] == secondary["id"]), None)

    def trend_phrase(item: dict[str, Any] | None) -> str:
        if not item:
            return "趋势暂不明显"
        delta = int(item.get("delta", 0))
        if delta > 0:
            return f"末端窗口上升 {delta}"
        if delta < 0:
            return f"末端窗口回落 {abs(delta)}"
        return "末端窗口持平"

    summary_metrics = [
        {
            "value": str(lead["opportunity"]),
            "label": "Opportunity Score",
            "note": f"当前最值得先打：{PAIN_CATEGORIES[lead['id']]['label']}",
        },
        {
            "value": str(lead["packaging"]),
            "label": "Packaging Readiness",
            "note": f"当前最容易卖清楚：{PAIN_CATEGORIES[lead['id']]['offer']}",
        },
        {
            "value": f"{lead_trend['delta']:+d}" if lead_trend else "0",
            "label": "趋势动量",
            "note": f"{PAIN_CATEGORIES[lead['id']]['label']} 在最近窗口里的变化",
        },
        {
            "value": f"{comment_enriched_records}/{len(records)}",
            "label": "评论覆盖",
            "note": f"已抓到评论的 thread 占比，累计评论 {total_comment_count} 条",
        },
        {
            "value": str(hot_refresh.get("selected_count", 0)),
            "label": "Hot Threads",
            "note": f"当前可增量刷新的高价值 thread，推荐模式 {hot_refresh.get('recommended_mode', 'browser')}",
        },
    ]

    today_changed = [
        {
            "title": "履约主题是当前最强主线",
            "body": (
                f"在 {len(records)} 条样本里，{PAIN_CATEGORIES[lead['id']]['label']} 的综合机会分最高，"
                f"高意向样本有 {lead['high_urgency_count']} 条，评论确认度 {lead['comment_confirmation_score']:.1f}，且 {trend_phrase(lead_trend)}，最适合先做主打入口。"
            ),
        },
        {
            "title": "Supplier 仍然值得保留为第二主产品",
            "body": (
                f"{PAIN_CATEGORIES[secondary['id']]['label']} 的数量和明确求助表达都不弱，"
                f"当前 {trend_phrase(secondary_trend)}，推荐密度 {secondary['recommendation_density']:.2f}，适合作为第二优先级 offer，而不是直接放弃。"
            ),
        },
        {
            "title": "Risk / Cost 更适合作为补充卖点",
            "body": "质量风险和利润压力都真实存在，但评论里的确认和解决方案推荐还没有像履约或 supplier 那样形成持续共识。",
        },
        {
            "title": "高价值 thread 已可走增量刷新",
            "body": (
                f"当前筛出 {hot_refresh.get('candidate_count', 0)} 个候选 hot thread，"
                f"其中 {hot_refresh.get('stale_candidate_count', 0)} 个已进入 stale 区间，"
                f"适合优先用 hot_threads 模式补评论和热度变化。"
            ),
        },
    ]

    weekly_actions = [
        {"title": "主推产品", "body": PAIN_CATEGORIES[lead["id"]]["offer"]},
        {"title": "主攻客群", "body": PAIN_CATEGORIES[lead["id"]]["segment_name"]},
        {"title": "测试话术", "body": PAIN_CATEGORIES[lead["id"]]["promise"]},
        {"title": "评论信号", "body": f"确认度 {overall_comment_metrics.get('comment_confirmation_score', 0):.1f} / 推荐密度 {overall_comment_metrics.get('recommendation_density', 0):.2f}"},
        {"title": "刷新建议", "body": f"建议模式：{hot_refresh.get('recommended_mode', 'browser')} · 候选 {hot_refresh.get('candidate_count', 0)} 条"},
        {"title": "暂缓投入", "body": "不要把 risk / cost 主题当成第一主打入口"},
    ]

    segments = []
    packages = []
    for rank, item in enumerate(opportunities, start=1):
        config = PAIN_CATEGORIES[item["id"]]
        top_signals = sorted(
            pain_groups[item["id"]],
            key=lambda record: (urgency_score(record), engagement(record)),
            reverse=True,
        )[:3]
        segments.append(
            {
                "id": item["id"],
                "name": config["segment_name"],
                "pain": config["pain_summary"],
                "opportunity": item["opportunity"],
                "packaging": item["packaging"],
                "confidence": item["confidence"],
                "trend": config["trend"],
                "actionMode": config["action_mode"],
                "recommendedProduct": config["offer"],
                "rationale": (
                    f"{config['label']} 相关问题在当前样本里共有 {item['count']} 条，"
                    f"高意向样本 {item['high_urgency_count']} 条，评论确认度 {item['comment_confirmation_score']:.1f}，"
                    f"推荐密度 {item['recommendation_density']:.2f}，说明它既真实存在，也更容易被业务团队拿来测试。"
                ),
                "signals": (
                    item["sample_comments"][:2]
                    + [post.get("title", "") for post in top_signals if post.get("title")]
                )[:3],
                "commentConfirmationScore": item["comment_confirmation_score"],
                "recommendationDensity": item["recommendation_density"],
                "objectionDensity": item["objection_density"],
            }
        )
        packages.append(
            {
                "name": config["offer"],
                "stage": "第一主产品" if rank == 1 else ("第二主产品" if rank == 2 else "支持型产品"),
                "targetSegment": config["segment_name"],
                "problem": config["pain_summary"],
                "promise": config["promise"],
                "format": config["format"],
                "angle": config["angle"],
                "avoid": config["avoid"],
            }
        )

    evidence = []
    for item in opportunities[:3]:
        config = PAIN_CATEGORIES[item["id"]]
        top_posts = sorted(
            pain_groups[item["id"]],
            key=lambda record: (urgency_score(record), engagement(record)),
            reverse=True,
        )[:3]
        for post in top_posts[:2]:
            evidence.append(
                {
                    "quote": post.get("title", ""),
                    "source": f"r/{post.get('subreddit', '')}",
                    "segment": config["segment_name"],
                    "pain": config["label"],
                    "sourceLevel": "comment" if post.get("comments") else "thread",
                }
            )

    heatmap_rows = []
    for row in SEGMENT_ROWS:
        counts = [row_matrix[row["id"]][pain] for pain in PAIN_ORDER]
        row_max = max(counts) if counts else 0
        values = []
        for pain, count in zip(PAIN_ORDER, counts):
            score, level = normalize_heat(count, row_max)
            values.append(
                {
                    "score": score,
                    "note": f"{PAIN_CATEGORIES[pain]['label']}：{count} 条",
                    "level": level,
                }
            )
        heatmap_rows.append({"label": row["label"], "values": values})

    source_breakdown = [
        {"name": f"r/{name}", "count": count}
        for name, count in subreddit_counter.most_common(5)
    ]
    keyword_breakdown = [
        {"name": name, "count": count}
        for name, count in search_term_counter.most_common(8)
    ]
    opportunity_drivers = []
    for item in opportunities[:3]:
        config = PAIN_CATEGORIES[item["id"]]
        opportunity_drivers.append(
            {
                "name": config["label"],
                "segment": config["segment_name"],
                "offer": config["offer"],
                "count": item["count"],
                "high_intent": item["high_urgency_count"],
                "avg_urgency": item["avg_urgency"],
                "avg_specificity": item["avg_specificity"],
                "opportunity_score": item["opportunity"],
                "packaging_score": item["packaging"],
                "comment_confirmation_score": item["comment_confirmation_score"],
                "recommendation_density": item["recommendation_density"],
                "objection_density": item["objection_density"],
            }
        )

    payload = {
        "study": {
            "topic": study_title,
            "market": market,
            "dateRange": date_range,
            "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "confidence": lead["confidence"],
            "threadCount": len(records),
            "commentCount": total_comment_count,
            "commentCoverageRate": comment_coverage_rate,
            "hotRefresh": hot_refresh,
        },
        "summary": {
            "headline": (
                f"优先打“{PAIN_CATEGORIES[lead['id']]['segment_name']}”，"
                f"主推 `{PAIN_CATEGORIES[lead['id']]['offer']}`。"
            ),
            "explanation": (
                f"当前样本里，{PAIN_CATEGORIES[lead['id']]['label']} 的综合机会分最高，"
                f"更适合作为第一主产品入口；`{PAIN_CATEGORIES[secondary['id']]['offer']}` 适合作为第二优先级产品保留。"
            ),
            "metrics": summary_metrics,
        },
        "todayChanged": today_changed,
        "weeklyActions": weekly_actions,
        "segments": segments,
        "packages": packages[:3],
        "evidence": evidence[:6],
        "heatmap": {
            "columns": [PAIN_CATEGORIES[key]["label"] for key in PAIN_ORDER],
            "rows": heatmap_rows,
        },
        "sourceBreakdown": source_breakdown,
        "keywordBreakdown": keyword_breakdown,
        "opportunityDrivers": opportunity_drivers,
        "trendSeries": trend_series,
        "mappingSummary": {
            "source_count": len(source_breakdown),
            "keyword_count": len(keyword_breakdown),
            "top_source": source_breakdown[0]["name"] if source_breakdown else "N/A",
            "top_driver": opportunity_drivers[0]["name"] if opportunity_drivers else "N/A",
            "thread_count": len(records),
            "comment_count": total_comment_count,
            "comment_enriched_records": comment_enriched_records,
            "comment_confirmation_score": overall_comment_metrics.get("comment_confirmation_score", 0),
            "recommendation_density": overall_comment_metrics.get("recommendation_density", 0),
            "objection_density": overall_comment_metrics.get("objection_density", 0),
            "hot_thread_candidates": hot_refresh.get("candidate_count", 0),
            "hot_thread_recommended_mode": hot_refresh.get("recommended_mode", "browser"),
        },
        "commentIntelligence": comment_signal_metrics,
        "weeklyBrief": {
            "topChange": (
                f"整体机会仍由 {PAIN_CATEGORIES[lead['id']]['label']} 主导，"
                f"但最近窗口里 {PAIN_CATEGORIES[secondary['id']]['label']} {trend_phrase(secondary_trend)}，"
                f"同时评论推荐密度 {secondary['recommendation_density']:.2f}，说明第二产品值得继续保留和测试。"
            ),
            "topSegments": [segment["name"] for segment in segments[:3]],
            "leadPackage": PAIN_CATEGORIES[lead["id"]]["offer"],
            "avoid": [
                "不要把风险或利润议题当成第一入口",
                "不要回到泛“供应链优化”表述",
                "不要让首页重新退化成帖子流",
            ],
            "nextWeek": [
                f"统一测试 {PAIN_CATEGORIES[lead['id']]['offer']} 的主话术",
                f"保留 {PAIN_CATEGORIES[secondary['id']]['offer']} 作为第二优先级",
                "继续跟踪评论确认度、推荐密度与异议密度，验证当前升温是否在延续",
            ],
        },
    }
    return payload


def write_outputs(payload: dict[str, Any], json_output: Path, js_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    js_output.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_output.write_text(json_text + "\n", encoding="utf-8")
    js_output.write_text(f"window.__MVP_PAYLOAD__ = {json_text};\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    records = read_jsonl(Path(args.input))
    payload = build_payload(records, args.study_title, args.market, args.date_range)
    write_outputs(payload, Path(args.json_output), Path(args.js_output))


if __name__ == "__main__":
    main()
