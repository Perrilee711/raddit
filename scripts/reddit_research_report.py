#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


KEYWORD_TAGS = {
    "conversion": ["convert", "conversion", "cvr", "cro", "checkout", "abandoned cart"],
    "ads": ["ads", "facebook ads", "meta ads", "google ads", "roas", "cpa", "ppc"],
    "theme_dev": ["theme", "developer", "custom code", "liquid", "plugin", "app"],
    "performance": ["page speed", "site speed", "performance", "core web vitals", "loading", "load time"],
    "supplier": ["supplier", "fulfillment", "shipping", "delivery", "inventory"],
    "email_crm": ["email", "klaviyo", "flow", "welcome series", "retention"],
    "migration": ["migrate", "migration", "move from", "switch to", "replatform"],
    "tracking": ["tracking", "ga4", "pixel", "attribution", "analytics"],
    "payments": ["payment", "stripe", "paypal", "gateway", "chargeback"],
}

INTENT_KEYWORDS = {
    3: ["hire", "looking for", "recommend someone", "agency", "freelancer", "developer"],
    2: ["need help", "how do i fix", "not converting", "not working", "can someone help"],
    1: ["best way", "any tool", "what app", "how do i"],
}

PLATFORM_KEYWORDS = {
    "shopify": ["shopify", "liquid", "shop app"],
    "woocommerce": ["woocommerce", "wordpress", "wp", "elementor"],
    "operations": ["dropshipping", "supplier", "fulfillment", "3pl"],
}

STAGE_KEYWORDS = {
    "starting_out": ["starting", "beginner", "new store", "just launched", "first store"],
    "stuck_after_launch": ["not converting", "low sales", "getting traffic but", "few orders"],
    "scaling_issues": ["scale", "roas", "cpa", "ads not profitable", "cannot scale"],
    "technical_debt": ["bug", "broken", "conflict", "page speed", "error", "checkout issue"],
    "operations_issues": ["supplier", "fulfillment", "shipping", "refunds", "inventory"],
    "migration": ["migrate", "move to", "switch from", "replatform"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert scraped Reddit posts into a Markdown research report."
    )
    parser.add_argument("--input", required=True, help="Path to a JSON, JSONL, or CSV file.")
    parser.add_argument("--output", required=True, help="Path to the Markdown report.")
    parser.add_argument(
        "--top-leads",
        type=int,
        default=10,
        help="How many high-intent posts to include in the lead section.",
    )
    return parser.parse_args()


def read_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [ensure_dict(item) for item in data]
        raise ValueError("JSON input must be a list of objects.")
    if suffix == ".jsonl":
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(ensure_dict(json.loads(line)))
        return records
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise ValueError("Unsupported input format. Use .json, .jsonl, or .csv.")


def ensure_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Each record must be an object.")
    return value


def normalize_text(*values: Any) -> str:
    return " ".join(str(value or "").strip().lower() for value in values if value is not None)


def score_intent(text: str) -> int:
    score = 0
    for points, keywords in INTENT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            score += points
    return min(score, 10)


def infer_tags(text: str) -> list[str]:
    tags = [tag for tag, keywords in KEYWORD_TAGS.items() if any(keyword in text for keyword in keywords)]
    return tags or ["general"]


def infer_platform(record: dict[str, Any], text: str) -> str:
    subreddit = str(record.get("subreddit", "")).lower()
    for platform, keywords in PLATFORM_KEYWORDS.items():
        if platform in subreddit or any(keyword in text for keyword in keywords):
            return platform
    return "unknown"


def infer_stage(text: str) -> str:
    for stage, keywords in STAGE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return stage
    return "unclear"


def parse_number(value: Any) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0


def format_timestamp(value: Any) -> str:
    if value in (None, ""):
        return "unknown"
    try:
        timestamp = float(value)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OSError):
        return str(value)


def enrich_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for record in records:
        title = str(record.get("title", "")).strip()
        body = str(record.get("body", record.get("selftext", ""))).strip()
        text = normalize_text(title, body)
        intent_score = score_intent(text)
        engagement = parse_number(record.get("score")) + parse_number(record.get("num_comments"))
        pain_tags = infer_tags(text)
        enriched.append(
            {
                **record,
                "title": title,
                "body": body,
                "text": text,
                "intent_score": intent_score,
                "engagement_score": engagement,
                "pain_tags": pain_tags,
                "platform": infer_platform(record, text),
                "business_stage": infer_stage(text),
            }
        )
    return enriched


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    subreddit_counts = Counter(str(record.get("subreddit", "unknown")) for record in records)
    platform_counts = Counter(record["platform"] for record in records)
    stage_counts = Counter(record["business_stage"] for record in records)
    tag_counts = Counter(tag for record in records for tag in record["pain_tags"])

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for tag in record["pain_tags"]:
            grouped[tag].append(record)

    top_leads = sorted(
        records,
        key=lambda item: (item["intent_score"], item["engagement_score"]),
        reverse=True,
    )
    return {
        "subreddit_counts": subreddit_counts,
        "platform_counts": platform_counts,
        "stage_counts": stage_counts,
        "tag_counts": tag_counts,
        "grouped": grouped,
        "top_leads": top_leads,
    }


def suggest_offer(tags: list[str], platform: str) -> str:
    if "supplier" in tags:
        return "供应链与履约梳理"
    if "conversion" in tags:
        return "转化率诊断 / 结账流程优化"
    if "ads" in tags:
        return "广告漏斗诊断 / 投放排查"
    if "performance" in tags:
        return "站点性能优化"
    if "theme_dev" in tags and platform == "shopify":
        return "Shopify 主题与应用集成支持"
    if "theme_dev" in tags and platform == "woocommerce":
        return "WooCommerce 插件与定制开发"
    if "migration" in tags:
        return "平台迁移评估与执行"
    if "supplier" in tags:
        return "供应链与履约梳理"
    return "需求待人工复核"


def render_counter(counter: Counter[str], limit: int = 10) -> str:
    if not counter:
        return "- 无数据"
    return "\n".join(f"- {name}: {count}" for name, count in counter.most_common(limit))


def render_common_patterns(summary: dict[str, Any]) -> str:
    top_tags = [name for name, _ in summary["tag_counts"].most_common(3)]
    lines = []
    for tag in top_tags:
        sample_records = summary["grouped"][tag][:3]
        sample_titles = " / ".join(record["title"] for record in sample_records if record["title"])
        lines.append(f"- `{tag}`: 高频出现在 {sample_titles or '若干帖子'}")
    if not lines:
        return "- 暂未识别出稳定模式"
    return "\n".join(lines)


def render_top_leads(records: list[dict[str, Any]], limit: int) -> str:
    if not records:
        return "- 无高意向线索"
    lines = []
    for record in records[:limit]:
        url = record.get("url") or ""
        title = record.get("title") or "(untitled)"
        subreddit = record.get("subreddit") or "unknown"
        tags = ", ".join(record["pain_tags"])
        offer = suggest_offer(record["pain_tags"], record["platform"])
        lines.append(
            "\n".join(
                [
                    f"### {title}",
                    f"- subreddit: `{subreddit}`",
                    f"- intent_score: `{record['intent_score']}`",
                    f"- engagement_score: `{record['engagement_score']}`",
                    f"- platform: `{record['platform']}`",
                    f"- stage: `{record['business_stage']}`",
                    f"- pain_tags: `{tags}`",
                    f"- suggested_offer: {offer}",
                    f"- created_utc: {format_timestamp(record.get('created_utc'))}",
                    f"- url: {url or 'N/A'}",
                ]
            )
        )
    return "\n\n".join(lines)


def render_report(records: list[dict[str, Any]], summary: dict[str, Any], source: Path, limit: int) -> str:
    created_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""# Reddit 电商需求研究报告

- 生成时间: {created_at}
- 数据来源: `{source}`
- 样本量: `{len(records)}`

## 1. 抓取概况

### 子版块分布
{render_counter(summary["subreddit_counts"])}

### 平台分布
{render_counter(summary["platform_counts"])}

### 业务阶段分布
{render_counter(summary["stage_counts"])}

## 2. 高频需求与痛点

### 标签分布
{render_counter(summary["tag_counts"])}

### 共性总结
{render_common_patterns(summary)}

## 3. 高意向客户线索

{render_top_leads(summary["top_leads"], limit)}

## 4. 下一步实施建议

- 先人工复核 `intent_score >= 3` 且互动较高的帖子
- 优先围绕最高频的 2-3 个痛点设计服务切入点
- 把高频问题反推成内容选题、落地页标题、销售话术
- 对重复出现的问题单独建专题文档，沉淀成 SOP
"""


def generate_report(input_path: Path, output_path: Path, top_leads: int = 10) -> None:
    records = read_records(input_path)
    enriched = enrich_records(records)
    summary = build_summary(enriched)
    report = render_report(enriched, summary, input_path, top_leads)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    generate_report(input_path, output_path, args.top_leads)


if __name__ == "__main__":
    main()
