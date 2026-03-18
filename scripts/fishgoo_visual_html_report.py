#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
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
        "accent": "#257179",
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
        "accent": "#d26b2c",
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
        "accent": "#8c5e2a",
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
        "accent": "#5b7d3b",
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
    "general_operator": {
        "label": "General Operator",
        "keywords": [],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Fishgoo HTML visual dashboard from Reddit JSONL.")
    parser.add_argument("--input", required=True, help="Path to raw Reddit JSONL data.")
    parser.add_argument("--output", required=True, help="Path to HTML output.")
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=["dropship", "dropshipping"],
        help="Subreddits to include in the dashboard.",
    )
    parser.add_argument(
        "--top-posts",
        type=int,
        default=5,
        help="Number of post cards per opportunity.",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "zh"],
        default="en",
        help="Dashboard language.",
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
        if key == "general_operator":
            continue
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
        market_score = (volume_score * 0.6) + (avg_urgency * 0.4)
        result[key] = {
            "volume": volume,
            "volume_score": round(volume_score, 1),
            "urgency_score": round(avg_urgency, 1),
            "fishgoo_fit": config["fishgoo_fit"],
            "monetization": config["monetization"],
            "market_score": round(market_score, 1),
            "priority_score": round(
                (volume_score * 0.35)
                + (avg_urgency * 0.25)
                + (config["fishgoo_fit"] * 0.25)
                + (config["monetization"] * 0.15),
                1,
            ),
        }
    return result


def build_matrix(records: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        segment = classify_segment(record)
        pain = classify_pain(record)
        matrix[segment][pain] += 1
    return matrix


def top_posts_by_pain(records: list[dict[str, Any]], top_posts: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        pain = classify_pain(record)
        if pain in PAIN_CATEGORIES:
            grouped[pain].append(record)
    for key in grouped:
        grouped[key] = sorted(grouped[key], key=lambda item: (urgency_score(item), engagement(item)), reverse=True)[:top_posts]
    return grouped


def esc(value: Any) -> str:
    return html.escape(str(value))


def render_kpis(records: list[dict[str, Any]], scores: dict[str, dict[str, float]]) -> str:
    high_urgency = sum(1 for record in records if urgency_score(record) >= 7.0)
    top_key = max(scores.items(), key=lambda item: item[1]["priority_score"])[0]
    top_pain = max(scores.items(), key=lambda item: item[1]["volume"])[0]
    cards = [
        ("Total Posts", str(len(records))),
        ("High-Urgency Posts", str(high_urgency)),
        ("Top Pain Category", PAIN_CATEGORIES[top_pain]["label"]),
        ("Highest-Priority Opportunity", PAIN_CATEGORIES[top_key]["label"]),
    ]
    return "".join(
        f'<div class="kpi-card"><div class="kpi-label">{esc(label)}</div><div class="kpi-value">{esc(value)}</div></div>'
        for label, value in cards
    )


def ui_text(lang: str) -> dict[str, str]:
    if lang == "zh":
        return {
            "title": "Fishgoo 机会策略仪表盘",
            "hero_title": "基于 Reddit 的 Dropshipping 客户痛点仪表盘",
            "hero_body": "这份仪表盘把 Reddit 上抓取到的需求，转换成 Fishgoo 可执行的战略视图。它会告诉你：哪类痛点最强、集中在哪类客群阶段、以及未来 90 天最值得先卖什么前置产品。",
            "summary_label": "当前判断",
            "generated": "生成时间",
            "input": "数据输入",
            "focus": "聚焦版块",
            "sample_size": "样本量",
            "kpi_total": "总帖子数",
            "kpi_urgency": "高紧急度帖子",
            "kpi_pain": "最大痛点类别",
            "kpi_opportunity": "优先机会",
            "panel_pain": "痛点分布",
            "panel_pain_note": "Fishgoo 相关痛点里，哪类问题在 Reddit 上出现得最多。",
            "panel_cards": "机会卡片",
            "panel_cards_note": "把 Fishgoo 适配度、市场证据和适合的前置 offer 放在一个决策视图里。",
            "panel_matrix": "痛点 × 客群阶段矩阵",
            "panel_matrix_note": "这个表帮助你判断：不同阶段的 dropshipping 卖家，最集中抱怨的到底是什么。",
            "segment": "客群阶段",
            "wall_title": "高意向帖子卡片墙",
            "open_post": "打开帖子",
            "footer": "建议用法：先看机会卡片，决定未来 90 天主打哪个机会；再看矩阵，确认优先服务哪类客群；最后把帖子墙里的真实用户原话，转成产品页文案、销售话术和 Reddit 回复模板。",
            "fit": "适配度",
            "market": "市场证据",
            "priority": "优先级",
            "volume": "帖子量",
            "urgency": "紧急度",
            "monetization": "变现",
            "offer": "前置 Offer",
            "pain_table_pain": "痛点",
            "pain_table_posts": "帖子数",
            "pain_table_bar": "条形图",
            "other": "其他 / 未归类",
        }
    return {
        "title": "Fishgoo Opportunity Dashboard",
        "hero_title": "Reddit Pain Signals For Dropshipping Buyers",
        "hero_body": "This dashboard converts scraped Reddit demand into a strategy view for Fishgoo. It shows which pain clusters are strongest, which customer stage they belong to, and which front-end service is most defensible for the next 90 days.",
        "summary_label": "Current Read",
        "generated": "Generated",
        "input": "Input",
        "focus": "Focus",
        "sample_size": "Sample Size",
        "kpi_total": "Total Posts",
        "kpi_urgency": "High-Urgency Posts",
        "kpi_pain": "Top Pain Category",
        "kpi_opportunity": "Highest-Priority Opportunity",
        "panel_pain": "Pain Distribution",
        "panel_pain_note": "Which Fishgoo-relevant problems show up most often in the Reddit sample.",
        "panel_cards": "Opportunity Cards",
        "panel_cards_note": "A compact decision view: Fishgoo fit, market evidence, and the suggested front-end offer.",
        "panel_matrix": "Pain x Segment Matrix",
        "panel_matrix_note": "This table shows which stage of dropshipping operator is producing which type of pain most often.",
        "segment": "Segment",
        "wall_title": "High-Intent Post Wall",
        "open_post": "Open Post",
        "footer": "Suggested use: start with the top opportunity card, verify whether the team can standardize that offer, then use the post wall to translate real user wording into landing page copy, sales messaging, and Reddit response templates.",
        "fit": "Fit",
        "market": "Market",
        "priority": "Priority",
        "volume": "Volume",
        "urgency": "Urgency",
        "monetization": "Monetization",
        "offer": "Offer",
        "pain_table_pain": "Pain",
        "pain_table_posts": "Posts",
        "pain_table_bar": "Bar",
        "other": "Unclear / Other",
    }


def render_bar_chart(records: list[dict[str, Any]], t: dict[str, str]) -> str:
    counts = Counter(classify_pain(record) for record in records)
    max_count = max((counts[key] for key in PAIN_CATEGORIES), default=1)
    rows = []
    for key, config in sorted(PAIN_CATEGORIES.items(), key=lambda item: counts[item[0]], reverse=True):
        count = counts[key]
        width = 0 if max_count == 0 else round((count / max_count) * 100, 1)
        rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label">{esc(config['label'])}</div>
              <div class="bar-track">
                <div class="bar-fill" style="width:{width}%; background:{config['accent']};"></div>
              </div>
              <div class="bar-value">{count}</div>
            </div>
            """
        )
    other_count = counts["unclear"]
    width = 0 if max_count == 0 else round((other_count / max_count) * 100, 1)
    rows.append(
        f"""
        <div class="bar-row">
          <div class="bar-label">{esc(t["other"])}</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{width}%; background:#b8a897;"></div>
          </div>
          <div class="bar-value">{other_count}</div>
        </div>
        """
    )
    return "".join(rows)


def render_matrix_table(matrix: dict[str, Counter[str]], t: dict[str, str], lang: str) -> str:
    segment_order = ["beginner_setup", "supplier_transition", "ops_firefighting", "margin_pressure", "general_operator"]
    pain_order = list(PAIN_CATEGORIES.keys())
    header = "".join(f"<th>{esc(PAIN_CATEGORIES[pain]['label'])}</th>" for pain in pain_order)
    body_rows = []
    for segment in segment_order:
        label = SEGMENTS[segment]["label"]
        if lang == "zh":
            zh_map = {
                "New Seller / Setup": "新手 / 起盘阶段",
                "Replacing Supplier / 3PL": "换 Supplier / 换 3PL",
                "Ops / Shipping Firefighting": "履约 / 发货救火阶段",
                "Margin / Cost Pressure": "利润 / 成本压力阶段",
                "General Operator": "泛运营人群",
            }
            label = zh_map.get(label, label)
        cells = "".join(f"<td>{matrix[segment][pain]}</td>" for pain in pain_order)
        body_rows.append(f"<tr><th>{esc(label)}</th>{cells}</tr>")
    return f"<table><thead><tr><th>{esc(t['segment'])}</th>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def render_matrix_cards(scores: dict[str, dict[str, float]], t: dict[str, str]) -> str:
    cards = []
    for key, metrics in sorted(scores.items(), key=lambda item: item[1]["priority_score"], reverse=True):
        config = PAIN_CATEGORIES[key]
        x = round((config["fishgoo_fit"] / 10.0) * 100, 1)
        y = round((metrics["market_score"] / 10.0) * 100, 1)
        cards.append(
            f"""
            <div class="opportunity-card" style="border-top:4px solid {config['accent']};">
              <div class="opportunity-title">{esc(config['label'])}</div>
              <div class="opportunity-metrics">
                <span>{esc(t['priority'])} {metrics['priority_score']}</span>
                <span>{esc(t['fit'])} {metrics['fishgoo_fit']}</span>
                <span>{esc(t['market'])} {metrics['market_score']}</span>
              </div>
              <div class="opportunity-offer">{esc(config['offer'])}</div>
              <div class="opportunity-meta">{esc(t['volume'])} {metrics['volume']} | {esc(t['urgency'])} {metrics['urgency_score']} | {esc(t['monetization'])} {metrics['monetization']}</div>
              <div class="mini-axis">
                <div class="mini-dot" style="left:{x}%; bottom:{y}%; background:{config['accent']};"></div>
              </div>
            </div>
            """
        )
    return "".join(cards)


def render_post_wall(grouped_posts: dict[str, list[dict[str, Any]]], t: dict[str, str]) -> str:
    sections = []
    for key, posts in sorted(grouped_posts.items(), key=lambda item: len(item[1]), reverse=True):
        config = PAIN_CATEGORIES[key]
        cards = []
        for post in posts:
            cards.append(
                f"""
                <article class="post-card">
                  <div class="post-meta">
                    <span>{esc(post.get('subreddit'))}</span>
                    <span>{esc(t['urgency'])} {urgency_score(post):.1f}</span>
                    <span>Engagement {engagement(post)}</span>
                  </div>
                  <h4>{esc(post.get('title'))}</h4>
                  <p>{esc(post.get('body', ''))[:220]}</p>
                  <a href="{esc(post.get('url'))}" target="_blank" rel="noreferrer">{esc(t['open_post'])}</a>
                </article>
                """
            )
        sections.append(
            f"""
            <section class="wall-section">
              <div class="section-heading" style="border-left:5px solid {config['accent']};">{esc(config['label'])}</div>
              <div class="post-grid">{''.join(cards)}</div>
            </section>
            """
        )
    return "".join(sections)


def build_html(records: list[dict[str, Any]], input_path: Path, subreddits: list[str], top_posts: int, lang: str) -> str:
    subset = [record for record in records if record.get("subreddit") in set(subreddits)]
    scores = score_opportunities(subset)
    matrix = build_matrix(subset)
    top_posts_map = top_posts_by_pain(subset, top_posts)
    created_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top_key = max(scores.items(), key=lambda item: item[1]["priority_score"])[0]
    t = ui_text(lang)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(t["title"])}</title>
  <style>
    :root {{
      --bg: #f4efe8;
      --panel: #fffaf3;
      --ink: #1f2a2c;
      --muted: #667172;
      --line: #ddd1c0;
      --accent: #d26b2c;
      --shadow: 0 16px 40px rgba(34, 33, 28, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(210,107,44,0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(37,113,121,0.14), transparent 24%),
        linear-gradient(180deg, #f8f3ec 0%, var(--bg) 100%);
    }}
    .shell {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.3fr 0.7fr;
      gap: 24px;
      align-items: end;
      margin-bottom: 28px;
    }}
    .hero-card, .summary-card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
    }}
    .hero-card {{
      padding: 28px;
    }}
    .eyebrow {{
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      font-weight: 700;
    }}
    h1 {{
      margin: 10px 0 12px;
      font-size: 42px;
      line-height: 1.05;
    }}
    .hero p {{
      color: var(--muted);
      font-size: 17px;
      line-height: 1.6;
      margin: 0;
    }}
    .summary-card {{
      padding: 24px;
      min-height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .summary-card strong {{
      display: block;
      font-size: 22px;
      margin-top: 6px;
    }}
    .summary-meta {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin: 0 0 28px;
    }}
    .kpi-card {{
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .kpi-label {{
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }}
    .kpi-value {{
      margin-top: 10px;
      font-size: 28px;
      font-weight: 800;
      line-height: 1.1;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .panel {{
      padding: 24px;
      overflow: hidden;
    }}
    .panel h2 {{
      margin: 0 0 16px;
      font-size: 24px;
    }}
    .panel p.note {{
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.6;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 210px 1fr 48px;
      gap: 12px;
      align-items: center;
      margin: 10px 0;
    }}
    .bar-label {{
      font-weight: 600;
      font-size: 14px;
    }}
    .bar-track {{
      height: 16px;
      border-radius: 999px;
      background: #efe4d7;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: inherit;
    }}
    .bar-value {{
      text-align: right;
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 10px;
      text-align: left;
    }}
    th {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    .opportunity-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}
    .opportunity-card {{
      padding: 18px;
      border-radius: 18px;
      background: rgba(255,255,255,0.78);
      border: 1px solid var(--line);
    }}
    .opportunity-title {{
      font-weight: 800;
      font-size: 18px;
      margin-bottom: 8px;
    }}
    .opportunity-metrics {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 10px;
    }}
    .opportunity-offer {{
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .opportunity-meta {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 12px;
    }}
    .mini-axis {{
      position: relative;
      height: 130px;
      border-left: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      background:
        linear-gradient(to right, rgba(0,0,0,0.03) 1px, transparent 1px) 0 0 / 25% 100%,
        linear-gradient(to top, rgba(0,0,0,0.03) 1px, transparent 1px) 0 0 / 100% 25%;
    }}
    .mini-dot {{
      position: absolute;
      width: 14px;
      height: 14px;
      border-radius: 999px;
      transform: translate(-50%, 50%);
      box-shadow: 0 0 0 5px rgba(0,0,0,0.05);
    }}
    .wall-section {{
      margin-top: 28px;
    }}
    .section-heading {{
      font-size: 22px;
      font-weight: 800;
      padding-left: 14px;
      margin-bottom: 14px;
    }}
    .post-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}
    .post-card {{
      background: rgba(255,255,255,0.82);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .post-card h4 {{
      margin: 10px 0;
      font-size: 18px;
      line-height: 1.35;
    }}
    .post-card p {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
      min-height: 68px;
    }}
    .post-meta {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .post-card a {{
      color: var(--accent);
      font-weight: 700;
      text-decoration: none;
    }}
    .footer-note {{
      margin-top: 28px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.7;
    }}
    @media (max-width: 980px) {{
      .hero, .layout {{
        grid-template-columns: 1fr;
      }}
      .kpi-grid, .post-grid, .opportunity-grid {{
        grid-template-columns: 1fr;
      }}
      .bar-row {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-card">
        <div class="eyebrow">Fishgoo Strategy Dashboard</div>
        <h1>{esc(t["hero_title"])}</h1>
        <p>{esc(t["hero_body"])}</p>
      </div>
      <div class="summary-card">
        <div>
          <div class="eyebrow">{esc(t["summary_label"])}</div>
          <strong>{esc(PAIN_CATEGORIES[top_key]["label"])}</strong>
        </div>
        <div class="summary-meta">
          {esc(t["generated"])}: {esc(created_at)}<br>
          {esc(t["input"])}: {esc(input_path)}<br>
          {esc(t["focus"])}: {esc(", ".join(subreddits))}<br>
          {esc(t["sample_size"])}: {len(subset)}
        </div>
      </div>
    </section>

    <section class="kpi-grid">
      {render_kpis(subset, scores).replace("Total Posts", t["kpi_total"]).replace("High-Urgency Posts", t["kpi_urgency"]).replace("Top Pain Category", t["kpi_pain"]).replace("Highest-Priority Opportunity", t["kpi_opportunity"])}
    </section>

    <section class="layout">
      <div class="panel">
        <h2>{esc(t["panel_pain"])}</h2>
        <p class="note">{esc(t["panel_pain_note"])}</p>
        {render_bar_chart(subset, t)}
      </div>
      <div class="panel">
        <h2>{esc(t["panel_cards"])}</h2>
        <p class="note">{esc(t["panel_cards_note"])}</p>
        <div class="opportunity-grid">
          {render_matrix_cards(scores, t)}
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>{esc(t["panel_matrix"])}</h2>
      <p class="note">{esc(t["panel_matrix_note"])}</p>
      {render_matrix_table(matrix, t, lang)}
    </section>

    <section class="wall-section">
      <div class="section-heading">{esc(t["wall_title"])}</div>
      {render_post_wall(top_posts_map, t)}
    </section>

    <section class="footer-note">
      {esc(t["footer"])}
    </section>
  </div>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    records = read_jsonl(input_path)
    html_doc = build_html(records, input_path, args.subreddits, args.top_posts, args.lang)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()
