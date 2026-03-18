#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HYPOTHESES = {
    "supplier_match": {
        "label": "找靠谱 supplier / sourcing partner",
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
        ],
        "offers": [
            "Supplier Match Sprint",
            "Private Supplier Shortlist",
            "China Sourcing Route Advice",
        ],
    },
    "fulfillment_setup": {
        "label": "3PL / fulfillment / shipping 方案混乱",
        "keywords": [
            "3pl",
            "fulfillment",
            "shipping",
            "warehouse",
            "consolidation",
            "delivery",
            "packaging",
            "fulfillment partner",
            "fulfillment center",
            "shipping delays",
            "slow shipping",
            "shipping times",
            "faster shipping",
        ],
        "offers": [
            "3PL & Fulfillment Setup",
            "Shipping Model Comparison",
            "Fulfillment Workflow Audit",
        ],
    },
    "china_risk_control": {
        "label": "从中国采购风险高",
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
        "offers": [
            "China Buying Risk Check",
            "QC & Inspection Support",
            "Seller Communication Support",
        ],
    },
    "cost_down": {
        "label": "shipping / packaging / margin 吃利润",
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
        "offers": [
            "China Sourcing Cost-Down Audit",
            "Packaging Cost Review",
            "Margin Impact Review",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Fishgoo opportunity hypotheses against scraped Reddit data."
    )
    parser.add_argument("--input", required=True, help="Path to raw Reddit JSONL data.")
    parser.add_argument("--output", required=True, help="Path to Markdown report.")
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=["dropship", "dropshipping"],
        help="Only analyze these subreddits.",
    )
    parser.add_argument(
        "--top-posts",
        type=int,
        default=5,
        help="Top posts to show per hypothesis.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def text_of(record: dict[str, Any]) -> str:
    return f"{record.get('title', '')} {record.get('body', '')}".lower()


def engagement_of(record: dict[str, Any]) -> int:
    try:
        return int(float(record.get("score", 0) or 0)) + int(float(record.get("num_comments", 0) or 0))
    except (TypeError, ValueError):
        return 0


def classify(record: dict[str, Any]) -> list[str]:
    text = text_of(record)
    matched = []
    for key, config in HYPOTHESES.items():
        if any(keyword in text for keyword in config["keywords"]):
            matched.append(key)
    return matched or ["unclear"]


def fit_score(hypothesis: str, record: dict[str, Any]) -> float:
    text = text_of(record)
    score = 0.0
    if any(
        key in text
        for key in [
            "looking for",
            "need help",
            "need advice",
            "how to find",
            "new",
            "partner",
            "service",
            "solution",
        ]
    ):
        score += 4.0
    if hypothesis != "unclear":
        score += 3.0
    if any(
        key in text
        for key in [
            "supplier",
            "3pl",
            "fulfillment",
            "shipping",
            "margin",
            "quality",
            "inspection",
            "cost",
        ]
    ):
        score += 2.0
    if any(
        key in text
        for key in [
            "for hire",
            "test for free",
            "i built",
            "thoughts on",
            "anyone here tried",
            "rate my",
        ]
    ):
        score -= 3.0
    score += min(engagement_of(record), 40) / 8.0
    return score


def summarize(records: list[dict[str, Any]], subreddits: list[str], top_posts: int) -> dict[str, Any]:
    subset = [record for record in records if record.get("subreddit") in set(subreddits)]
    classified: dict[str, list[dict[str, Any]]] = defaultdict(list)
    keyword_hits: Counter[str] = Counter()

    for record in subset:
        matched = classify(record)
        for hypothesis in matched:
            classified[hypothesis].append(record)
            if hypothesis in HYPOTHESES:
                text = text_of(record)
                for keyword in HYPOTHESES[hypothesis]["keywords"]:
                    if keyword in text:
                        keyword_hits[f"{hypothesis}:{keyword}"] += 1

    counts = Counter()
    high_fit_counts = Counter()
    top_examples: dict[str, list[dict[str, Any]]] = {}
    for hypothesis, items in classified.items():
        counts[hypothesis] = len(items)
        scored = sorted(items, key=lambda item: (fit_score(hypothesis, item), engagement_of(item)), reverse=True)
        high_fit_counts[hypothesis] = sum(1 for item in items if fit_score(hypothesis, item) >= 7.0)
        top_examples[hypothesis] = scored[:top_posts]

    return {
        "subset": subset,
        "counts": counts,
        "high_fit_counts": high_fit_counts,
        "top_examples": top_examples,
        "keyword_hits": keyword_hits,
    }


def render_counts(counts: Counter[str]) -> str:
    if not counts:
        return "- 无数据"
    return "\n".join(f"- {name}: {count}" for name, count in counts.most_common())


def recommend(summary: dict[str, Any]) -> tuple[str, str]:
    scored = []
    for hypothesis, count in summary["counts"].items():
        if hypothesis == "unclear":
            continue
        high_fit = summary["high_fit_counts"][hypothesis]
        score = count + high_fit * 1.5
        scored.append((score, hypothesis))
    if not scored:
        return "暂无结论", "当前样本不足以判断。"

    _, winner = max(scored)
    reasons = {
        "supplier_match": "因为它最接近 Fishgoo 当前 buying agent / sourcing / seller communication 的强能力。",
        "fulfillment_setup": "因为它最接近 Fishgoo 当前仓储、合单、发货、履约整合能力。",
        "china_risk_control": "因为它最接近 Fishgoo 当前验货、QC、退换支持和风险控制能力。",
        "cost_down": "因为它最适合往高价值咨询和长期供应链优化方向延展。",
    }
    return HYPOTHESES[winner]["label"], reasons[winner]


def render_examples(summary: dict[str, Any]) -> str:
    sections = []
    for hypothesis in ["supplier_match", "fulfillment_setup", "china_risk_control", "cost_down"]:
        label = HYPOTHESES[hypothesis]["label"]
        posts = summary["top_examples"].get(hypothesis, [])
        if not posts:
            continue
        lines = [f"### {label}"]
        for post in posts:
            lines.append(f"- `{post.get('subreddit')}` {post.get('title')}")
            lines.append(f"  url: {post.get('url')}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections) if sections else "- 暂无代表帖子"


def render_offers() -> str:
    lines = []
    for key in ["supplier_match", "fulfillment_setup", "china_risk_control", "cost_down"]:
        config = HYPOTHESES[key]
        lines.append(f"### {config['label']}")
        for offer in config["offers"]:
            lines.append(f"- {offer}")
    return "\n".join(lines)


def render_keyword_hits(summary: dict[str, Any], top_n: int = 8) -> str:
    sections = []
    for key in ["supplier_match", "fulfillment_setup", "china_risk_control", "cost_down"]:
        label = HYPOTHESES[key]["label"]
        lines = [f"### {label}"]
        pairs = []
        for keyword in HYPOTHESES[key]["keywords"]:
            count = summary["keyword_hits"].get(f"{key}:{keyword}", 0)
            if count:
                pairs.append((count, keyword))
        if not pairs:
            lines.append("- 暂无明显关键词命中")
        else:
            for count, keyword in sorted(pairs, reverse=True)[:top_n]:
                lines.append(f"- `{keyword}`: {count}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def render_report(summary: dict[str, Any]) -> str:
    created_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    winner, reason = recommend(summary)
    subset = summary["subset"]

    return f"""# Fishgoo Dropshipping 机会验证

- 生成时间: {created_at}
- 样本来源: `dropship + dropshipping`
- 样本量: `{len(subset)}`

## 1. 本轮验证目标

只验证一个客群:

- `dropshipping 卖家`

围绕 4 个机会假设：

- 找靠谱 supplier / sourcing partner
- 3PL / fulfillment / shipping 方案混乱
- 从中国采购风险高
- shipping / packaging / margin 吃利润

## 2. 假设分布

### 全部相关帖子量
{render_counts(summary["counts"])}

### 高适配帖子量
{render_counts(summary["high_fit_counts"])}

## 3. 初步判断

当前最值得优先验证的机会是：

- `{winner}`

原因：

- {reason}
- 它更接近 Fishgoo 现有官网能力：采购、卖家沟通、仓储、质检、合单、国际发货
- 对 3 人 B 端团队来说，也更容易讲清楚和标准化成交

## 3.5 关键词命中分布

{render_keyword_hits(summary)}

## 4. 代表帖子

{render_examples(summary)}

## 5. 更像可卖产品的方向

{render_offers()}

## 6. 这轮还不能替你回答的关键问题

Reddit 只能帮你验证：

- 用户是否真的在抱怨这类问题
- 用户是怎么描述这类问题的
- 哪类问题更常见、更具体

Reddit 还不能单独帮你验证：

- 哪类客户实际最愿意付费
- Fishgoo 目前成交最快的是哪类客户
- 哪类服务利润更高、交付更稳

## 7. 下一步最该补的信息

为了从“机会存在”走到“战略聚焦”，还需要补这 4 类信息：

1. Fishgoo 现有成交客户里，哪类客户成交最快
2. 哪类客户最赚钱、最不扯皮、最容易复购
3. Fishgoo 当前明确能做 / 不能做的边界
4. 这 4 个机会里，哪个最容易用轻产品先成交

## 8. 建议

这一轮先不要扩到更多客群。

建议下一轮只在 `dropshipping 卖家` 内继续缩小：

1. `supplier / sourcing`
2. `3PL / fulfillment`

先比较这两个方向，决定 Fishgoo 的第一主产品。
"""


if __name__ == "__main__":
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    records = read_jsonl(input_path)
    summary = summarize(records, args.subreddits, args.top_posts)
    report = render_report(summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
