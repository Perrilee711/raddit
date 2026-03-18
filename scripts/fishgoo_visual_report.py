#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAIN_CATEGORIES = {
    "supplier_match": {
        "label": "Supplier / Sourcing",
        "keywords": [
            "supplier",
            "private supplier",
            "private agent",
            "sourcing",
            "china supplier",
            "vendor",
            "find supplier",
            "reliable supplier",
            "bad supplier",
            "supplier issues",
            "agent/supplier",
        ],
        "fishgoo_fit": 9.0,
        "monetization": 8.0,
        "offer": "Supplier Match Sprint",
    },
    "fulfillment_setup": {
        "label": "3PL / Fulfillment / Shipping",
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
        "fishgoo_fit": 10.0,
        "monetization": 9.0,
        "offer": "3PL & Fulfillment Audit",
    },
    "china_risk_control": {
        "label": "Risk / QC / Scam Avoidance",
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
        "fishgoo_fit": 8.0,
        "monetization": 6.0,
        "offer": "China Buying Risk Check",
    },
    "cost_down": {
        "label": "Cost / Margin / Packaging",
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
        "fishgoo_fit": 7.0,
        "monetization": 7.0,
        "offer": "Cost-Down Review",
    },
}

SEGMENTS = {
    "beginner_setup": {
        "label": "New Seller / Setup",
        "keywords": [
            "start",
            "starting",
            "beginner",
            "new to",
            "first time",
            "planning",
            "just started",
            "new store",
        ],
    },
    "supplier_transition": {
        "label": "Replacing Supplier / 3PL",
        "keywords": [
            "new supplier",
            "bad supplier",
            "reliable supplier",
            "private supplier",
            "find supplier",
            "3pl",
            "fulfillment partner",
            "looking for a 3pl",
            "new 3pl",
            "switching",
        ],
    },
    "ops_firefighting": {
        "label": "Ops / Shipping Firefighting",
        "keywords": [
            "shipping",
            "fulfillment",
            "delay",
            "slow",
            "refund",
            "chargeback",
            "wrong item",
            "quality",
            "problem",
            "issue",
            "need help",
        ],
    },
    "margin_pressure": {
        "label": "Margin / Cost Pressure",
        "keywords": [
            "margin",
            "profit",
            "cost",
            "packaging",
            "tariff",
            "pricing",
            "too expensive",
            "landed cost",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Fishgoo visual strategy report from Reddit data.")
    parser.add_argument("--input", required=True, help="Path to raw Reddit JSONL data.")
    parser.add_argument("--output", required=True, help="Path to Markdown output.")
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=["dropship", "dropshipping"],
        help="Subreddits to include in the report.",
    )
    parser.add_argument(
        "--top-posts",
        type=int,
        default=5,
        help="Top posts to show per pain category.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def text_of(record: dict[str, Any]) -> str:
    return f"{record.get('title', '')} {record.get('body', '')}".lower()


def engagement(record: dict[str, Any]) -> int:
    try:
        return int(float(record.get("score", 0) or 0)) + int(float(record.get("num_comments", 0) or 0))
    except (TypeError, ValueError):
        return 0


def urgency_score(record: dict[str, Any]) -> float:
    text = text_of(record)
    score = 0.0
    if any(
        token in text
        for token in [
            "looking for",
            "need help",
            "need advice",
            "service",
            "partner",
            "not working",
            "slow shipping",
            "shipping delays",
            "new supplier",
        ]
    ):
        score += 6.0
    if any(
        token in text
        for token in ["3pl", "fulfillment", "supplier", "shipping", "quality", "refund", "margin", "cost"]
    ):
        score += 2.0
    score += min(engagement(record), 40) / 10.0
    return min(score, 10.0)


def classify_pain(record: dict[str, Any]) -> str:
    text = text_of(record)
    for key, config in PAIN_CATEGORIES.items():
        if any(keyword in text for keyword in config["keywords"]):
            return key
    return "unclear"


def classify_segment(record: dict[str, Any]) -> str:
    text = text_of(record)
    for key, config in SEGMENTS.items():
        if any(keyword in text for keyword in config["keywords"]):
            return key
    return "general_operator"


def score_opportunities(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    pain_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        pain_groups[classify_pain(record)].append(record)

    max_count = max((len(items) for key, items in pain_groups.items() if key != "unclear"), default=1)
    result: dict[str, dict[str, float]] = {}

    for key, config in PAIN_CATEGORIES.items():
        items = pain_groups.get(key, [])
        volume = len(items)
        volume_score = (volume / max_count) * 10 if max_count else 0
        avg_urgency = sum(urgency_score(item) for item in items) / len(items) if items else 0
        result[key] = {
            "volume": volume,
            "volume_score": round(volume_score, 1),
            "urgency_score": round(avg_urgency, 1),
            "fishgoo_fit": config["fishgoo_fit"],
            "monetization": config["monetization"],
            "priority_score": round((volume_score * 0.35) + (avg_urgency * 0.25) + (config["fishgoo_fit"] * 0.25) + (config["monetization"] * 0.15), 1),
        }
    return result


def ascii_bar(value: int, max_value: int, width: int = 18) -> str:
    if max_value <= 0:
        return ""
    filled = max(1, round((value / max_value) * width)) if value > 0 else 0
    return "█" * filled


def render_pain_table(records: list[dict[str, Any]]) -> str:
    counts = Counter(classify_pain(record) for record in records)
    max_count = max((counts[key] for key in PAIN_CATEGORIES), default=1)
    lines = ["| Pain | Posts | Bar |", "|---|---:|---|"]
    for key, config in sorted(PAIN_CATEGORIES.items(), key=lambda item: counts[item[0]], reverse=True):
        count = counts[key]
        lines.append(f"| {config['label']} | {count} | {ascii_bar(count, max_count)} |")
    lines.append(f"| Unclear / Other | {counts['unclear']} | {ascii_bar(counts['unclear'], max_count)} |")
    return "\n".join(lines)


def render_segment_matrix(records: list[dict[str, Any]]) -> str:
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        pain = classify_pain(record)
        segment = classify_segment(record)
        matrix[segment][pain] += 1

    segment_order = ["beginner_setup", "supplier_transition", "ops_firefighting", "margin_pressure", "general_operator"]
    pain_order = list(PAIN_CATEGORIES.keys())
    header = "| Segment | " + " | ".join(PAIN_CATEGORIES[key]["label"] for key in pain_order) + " |"
    divider = "|---|" + "|".join(["---:" for _ in pain_order]) + "|"
    lines = [header, divider]
    for segment in segment_order:
        label = SEGMENTS[segment]["label"] if segment in SEGMENTS else "General Operator"
        values = [str(matrix[segment][pain]) for pain in pain_order]
        lines.append("| " + label + " | " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_dashboard_structure() -> str:
    return """## Dashboard Structure

建议把 dashboard 做成 4 个区块：

1. `Top KPI`
- Total posts
- High-urgency posts
- Top pain category
- Highest-priority opportunity

2. `Pain Distribution`
- 条形图: 4 类 Fishgoo 相关痛点帖子量
- 饼图: 高紧急度帖子在 4 类机会中的占比

3. `Pain x Segment Matrix`
- 行: 客群阶段
- 列: 痛点类型
- 颜色深浅: 帖子量 / 高意向数量

4. `Opportunity Decision`
- 气泡图 / 象限图: Fishgoo Fit vs Market Evidence
- 卡片墙: 每类机会最值得看的 3-5 条帖子
"""


def render_pie_mermaid(records: list[dict[str, Any]]) -> str:
    counts = Counter(classify_pain(record) for record in records)
    lines = ["```mermaid", "pie showData", '    title "Fishgoo-Relevant Pain Distribution"']
    for key, config in PAIN_CATEGORIES.items():
        lines.append(f'    "{config["label"]}" : {counts[key]}')
    lines.append("```")
    return "\n".join(lines)


def render_quadrant_mermaid(scores: dict[str, dict[str, float]]) -> str:
    max_volume = max((item["volume_score"] for item in scores.values()), default=1)
    lines = [
        "```mermaid",
        "quadrantChart",
        '    title "Opportunity Matrix: Fishgoo Fit vs Market Evidence"',
        '    x-axis "Lower Fishgoo Fit" --> "Higher Fishgoo Fit"',
        '    y-axis "Lower Market Evidence" --> "Higher Market Evidence"',
        '    quadrant-1 "Scale Later"',
        '    quadrant-2 "Explore Carefully"',
        '    quadrant-3 "Ignore for Now"',
        '    quadrant-4 "Prioritize"',
    ]
    for key, config in PAIN_CATEGORIES.items():
        market_evidence = round((scores[key]["volume_score"] * 0.6) + (scores[key]["urgency_score"] * 0.4), 1)
        fit = round(config["fishgoo_fit"], 1)
        lines.append(f'    "{config["label"]}" : [{fit}, {market_evidence}]')
    lines.append("```")
    return "\n".join(lines)


def render_opportunity_table(scores: dict[str, dict[str, float]]) -> str:
    lines = [
        "| Opportunity | Volume Score | Urgency | Fishgoo Fit | Monetization | Priority | Suggested Front Offer |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    ordered = sorted(scores.items(), key=lambda item: item[1]["priority_score"], reverse=True)
    for key, metrics in ordered:
        lines.append(
            f"| {PAIN_CATEGORIES[key]['label']} | {metrics['volume_score']} | {metrics['urgency_score']} | "
            f"{metrics['fishgoo_fit']} | {metrics['monetization']} | {metrics['priority_score']} | {PAIN_CATEGORIES[key]['offer']} |"
        )
    return "\n".join(lines)


def render_top_posts(records: list[dict[str, Any]], top_posts: int) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        pain = classify_pain(record)
        if pain in PAIN_CATEGORIES:
            grouped[pain].append(record)

    sections = []
    for key, config in sorted(PAIN_CATEGORIES.items(), key=lambda item: len(grouped[item[0]]), reverse=True):
        posts = sorted(grouped[key], key=lambda item: (urgency_score(item), engagement(item)), reverse=True)[:top_posts]
        lines = [f"### {config['label']}"]
        for post in posts:
            lines.append(
                f"- `{post.get('subreddit')}` {post.get('title')}  \n"
                f"  urgency: `{urgency_score(post):.1f}` | engagement: `{engagement(post)}` | url: {post.get('url')}"
            )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def generate_report(records: list[dict[str, Any]], input_path: Path, top_posts: int, subreddits: list[str]) -> str:
    subset = [record for record in records if record.get("subreddit") in set(subreddits)]
    scores = score_opportunities(subset)
    created_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top_opportunity = max(scores.items(), key=lambda item: item[1]["priority_score"])[0]

    return f"""# Fishgoo Visual Strategy Report

- Generated: {created_at}
- Input: `{input_path}`
- Focus Subreddits: `{", ".join(subreddits)}`
- Sample Size: `{len(subset)}`
- Current Top Opportunity: `{PAIN_CATEGORIES[top_opportunity]["label"]}`

{render_dashboard_structure()}

## Pain Distribution

{render_pie_mermaid(subset)}

{render_pain_table(subset)}

## Pain x Segment Matrix

{render_segment_matrix(subset)}

## Opportunity Matrix

{render_quadrant_mermaid(scores)}

{render_opportunity_table(scores)}

## High-Intent Post Wall

{render_top_posts(subset, top_posts)}

## How To Use This

1. 先看 `Opportunity Matrix`，决定未来 90 天主打哪个机会。
2. 再看 `Pain x Segment Matrix`，决定优先服务哪一类 dropshipping 客群。
3. 最后看 `High-Intent Post Wall`，把真实用户原话转成产品页标题、销售话术和 Reddit 回复模板。
"""


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    records = read_jsonl(input_path)
    report = generate_report(records, input_path, args.top_posts, args.subreddits)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
