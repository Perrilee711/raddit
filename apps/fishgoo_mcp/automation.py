from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from apps.fishgoo_mcp.memory.builder import build_audit_timeline
from apps.fishgoo_mcp.memory.readers import read_current_truth
from apps.fishgoo_mcp.paths import GENERATED_BOARD_HTML, GENERATED_DAILY_DIR, GENERATED_DAILY_JSON_DIR


DAY1_DATE = date(2026, 3, 26)

CAMPAIGN_STATUS_MAP = {
    2: "ENABLED",
    3: "PAUSED",
}

CHANNEL_MAP = {
    2: "SEARCH",
    9: "DEMAND_GEN",
    10: "PERFORMANCE_MAX",
}

PRIMARY_STATUS_MAP = {
    3: "PAUSED",
    8: "LIMITED",
}


def day_label_for_date(target_date: date) -> str:
    return f"Day{(target_date - DAY1_DATE).days + 1}"


def _enum_label(value: Any, mapping: dict[int, str]) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return mapping.get(value, str(value))
    return str(value)


def _cost_usd(cost_micros: Any) -> float:
    try:
        return round(float(cost_micros or 0) / 1_000_000, 2)
    except (TypeError, ValueError):
        return 0.0


def _sum_campaigns(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "impressions": sum(int(row.get("metrics.impressions", 0) or 0) for row in rows),
        "clicks": sum(int(row.get("metrics.clicks", 0) or 0) for row in rows),
        "cost_usd": round(sum(_cost_usd(row.get("metrics.cost_micros", 0)) for row in rows), 2),
        "conversions": round(sum(float(row.get("metrics.conversions", 0) or 0) for row in rows), 2),
    }


def summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    account_today = (payload.get("account_today") or [{}])[0]
    campaigns_today = payload.get("campaigns_today") or []
    campaigns_yesterday = payload.get("campaigns_yesterday") or []
    campaigns_last_7d = payload.get("campaigns_last_7d") or []
    enabled_today = [
        row
        for row in campaigns_today
        if _enum_label(row.get("campaign.status"), CAMPAIGN_STATUS_MAP) == "ENABLED"
    ]
    return {
        "today": {
            "impressions": int(account_today.get("metrics.impressions", 0) or 0),
            "clicks": int(account_today.get("metrics.clicks", 0) or 0),
            "cost_usd": _cost_usd(account_today.get("metrics.cost_micros", 0)),
            "conversions": float(account_today.get("metrics.conversions", 0) or 0),
        },
        "yesterday": _sum_campaigns(campaigns_yesterday),
        "last_7d": _sum_campaigns(campaigns_last_7d),
        "enabled_today": enabled_today,
    }


def measurement_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    actions = payload.get("conversion_actions") or []
    goals = payload.get("campaign_goals") or []

    def find_action(name: str) -> dict[str, Any]:
        for item in actions:
            if item.get("conversion_action.name") == name:
                return item
        return {}

    purchase = find_action("fishgoo (web) purchase")
    purchase_value = find_action("fishgoo (web) purchase_value")
    signup = find_action("注册 (1)")
    campaign_goal_rows = [
        item
        for item in goals
        if item.get("campaign.name") in {"Pmax-", "search -品牌-0925"}
        and item.get("campaign_conversion_goal.origin") == "WEBSITE"
    ]
    return {
        "purchase_primary": bool(purchase.get("conversion_action.primary_for_goal")),
        "purchase_value_primary": bool(purchase_value.get("conversion_action.primary_for_goal")),
        "signup_primary": bool(signup.get("conversion_action.primary_for_goal")),
        "campaign_goal_rows": campaign_goal_rows,
    }


def write_generated_payload(payload: dict[str, Any], audit_date: date) -> Path:
    GENERATED_DAILY_JSON_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DAILY_JSON_DIR / f"{audit_date.isoformat()}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def render_feedback_markdown(payload: dict[str, Any], audit_date: date, refreshed_at: datetime) -> str:
    summary = summarize_payload(payload)
    measurement = measurement_snapshot(payload)
    day_label = day_label_for_date(audit_date)
    enabled_lines = []
    for row in summary["enabled_today"]:
        enabled_lines.append(
            "\n".join(
                [
                    f"- `{row.get('campaign.name', 'unknown')}`",
                    f"  - channel：`{_enum_label(row.get('campaign.advertising_channel_type'), CHANNEL_MAP)}`",
                    f"  - status：`{_enum_label(row.get('campaign.status'), CAMPAIGN_STATUS_MAP)}`",
                    f"  - primary status：`{_enum_label(row.get('campaign.primary_status'), PRIMARY_STATUS_MAP)}`",
                    f"  - budget：`${_cost_usd(row.get('campaign_budget.amount_micros', 0)):.2f}`",
                ]
            )
        )
    if not enabled_lines:
        enabled_lines.append("- 今天 `10:00` 时点没有检测到正在运行的 live campaign。")

    website_goals = []
    for row in measurement["campaign_goal_rows"]:
        website_goals.append(
            f"- `{row.get('campaign.name')}` / `{row.get('campaign_conversion_goal.category')}` / "
            f"`biddable={row.get('campaign_conversion_goal.biddable')}`"
        )
    if not website_goals:
        website_goals.append("- 当前没有读取到 website campaign goals。")

    return f"""# {day_label} 反馈

日期：{audit_date.isoformat()}  
观察对象：2026-03-25 调整后的 Google Ads live 账户  
审计方式：Google Ads API / MCP 只读拉数（自动日审）  
审计时间：约 `{refreshed_at.strftime("%H:%M")}`  

---

## 一、今日核心结论

{day_label} 的自动日审结论是：

**当前看板已经切换为每日自动刷新模式，今天这次读数以 `{refreshed_at.strftime("%H:%M")}` 的 live 数据为准。**

从系统判断看：

1. 今日截至当前展示：`{summary['today']['impressions']}`
2. 今日截至当前点击：`{summary['today']['clicks']}`
3. 今日截至当前花费：`${summary['today']['cost_usd']:.2f}`
4. 今日截至当前 Ads 转化：`{summary['today']['conversions']}`

如果今天在 `10:00` 左右仍然是低量或 `0` 花费，优先定义为“早盘尚未完全启动”，不要直接等同于全天异常；是否异常，要继续结合 `14:00` / `18:00` 的后续读数判断。

---

## 二、今日账户快照

### 账户总览（截至约 {refreshed_at.strftime("%H:%M")}）

- 展示：`{summary['today']['impressions']}`
- 点击：`{summary['today']['clicks']}`
- 花费：`${summary['today']['cost_usd']:.2f}`
- Ads 转化：`{summary['today']['conversions']}`

### 当前 live 系列

{chr(10).join(enabled_lines)}

---

## 三、昨日完整日

- 展示：`{summary['yesterday']['impressions']}`
- 点击：`{summary['yesterday']['clicks']}`
- 花费：`${summary['yesterday']['cost_usd']:.2f}`
- Ads 转化：`{summary['yesterday']['conversions']}`

---

## 四、最近 7 天

- 展示：`{summary['last_7d']['impressions']}`
- 点击：`{summary['last_7d']['clicks']}`
- 花费：`${summary['last_7d']['cost_usd']:.2f}`
- Ads 转化：`{summary['last_7d']['conversions']}`

---

## 五、Measurement 快照

- `fishgoo (web) purchase` primary：`{measurement['purchase_primary']}`
- `fishgoo (web) purchase_value` primary：`{measurement['purchase_value_primary']}`
- `注册 (1)` primary：`{measurement['signup_primary']}`

### 当前 website campaign goals

{chr(10).join(website_goals)}

---

## 六、负责人判断

1. 看板已具备每日自动刷新能力，后续可直接作为 `10:00` 的固定首看入口。  
2. 真正的操盘判断仍然要优先看 measurement、主力系列是否起量、以及昨日/近 7 天是否连续。  
3. 如果后续要让系统更像“负责人工作台”，下一步应该继续把异常预警和学习重点做成自动更新块。  

---

## 七、下一步建议

1. `14:00` 再看一次 live，判断今天是否从“早盘未启动”转为“正常起量”。  
2. `18:00` 再补一次收盘判断，确认是否需要记录成“全天异常”。  
3. 继续盯 `Purchase / Purchase value / Signup` 的 primary 与 biddable 逻辑。  
4. 如果你要讨论“下一步怎么调”，再结合业务侧真实订单和漏斗数据一起看。  
"""


def write_generated_feedback(payload: dict[str, Any], audit_date: date, refreshed_at: datetime) -> Path:
    GENERATED_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_DAILY_DIR / f"{day_label_for_date(audit_date)}反馈_{audit_date.isoformat()}.md"
    path.write_text(render_feedback_markdown(payload, audit_date, refreshed_at), encoding="utf-8")
    return path


def render_board_html(
    payload: dict[str, Any],
    refreshed_at: datetime,
    feedback_path: Path,
    timeline: list[dict[str, Any]],
    current_truth: dict[str, Any],
) -> str:
    summary = summarize_payload(payload)
    measurement = measurement_snapshot(payload)
    recent_rows = list(reversed(timeline[-10:]))
    timeline_rows = "\n".join(
        f"<tr><td>{row['day']}</td><td>{row['date']}</td><td>{row['title']}</td></tr>"
        for row in recent_rows
    )
    campaign_rows = "\n".join(
        "<tr>"
        f"<td>{row.get('campaign.name', '-')}</td>"
        f"<td>{_enum_label(row.get('campaign.advertising_channel_type'), CHANNEL_MAP)}</td>"
        f"<td>{_enum_label(row.get('campaign.status'), CAMPAIGN_STATUS_MAP)}</td>"
        f"<td>{_enum_label(row.get('campaign.primary_status'), PRIMARY_STATUS_MAP)}</td>"
        f"<td>${_cost_usd(row.get('campaign_budget.amount_micros', 0)):.2f}</td>"
        "</tr>"
        for row in summary["enabled_today"]
    ) or "<tr><td colspan='5'>今天这个时点没有检测到 live campaign。</td></tr>"

    next_actions = current_truth.get("next_actions_excerpt") or []
    current_judgment = current_truth.get("current_judgment") or []

    def render_lines(lines: list[str]) -> str:
        cleaned = [line.lstrip("- ").strip() for line in lines if line.strip()]
        return "".join(f"<li>{line}</li>" for line in cleaned[:6]) or "<li>暂无自动摘要。</li>"

    website_goal_rows = "\n".join(
        "<tr>"
        f"<td>{row.get('campaign.name')}</td>"
        f"<td>{row.get('campaign_conversion_goal.category')}</td>"
        f"<td>{row.get('campaign_conversion_goal.biddable')}</td>"
        "</tr>"
        for row in measurement["campaign_goal_rows"]
    ) or "<tr><td colspan='3'>暂无读取到 website goals。</td></tr>"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FISHGOO 广告负责人看板 Auto</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --panel: #ffffff;
      --text: #132238;
      --muted: #63758b;
      --accent: #0e7490;
      --accent-soft: #e0f2fe;
      --border: #d6e2ee;
      --good: #0f766e;
      --warn: #b45309;
      --shadow: 0 18px 50px rgba(19, 34, 56, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: radial-gradient(circle at top left, #e0f2fe 0%, var(--bg) 45%, #eef2ff 100%);
      color: var(--text);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 80px; }}
    .hero {{
      background: linear-gradient(135deg, #082f49, #164e63 60%, #155e75);
      color: #fff;
      border-radius: 28px;
      padding: 28px;
      box-shadow: var(--shadow);
    }}
    .hero h1 {{ margin: 0 0 10px; font-size: 34px; }}
    .hero p {{ margin: 6px 0; color: rgba(255,255,255,0.86); line-height: 1.7; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-top: 22px;
    }}
    .card, .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--shadow);
    }}
    .card {{ padding: 18px; }}
    .eyebrow {{ font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }}
    .value {{ margin-top: 10px; font-size: 30px; font-weight: 700; }}
    .note {{ margin-top: 8px; color: var(--muted); font-size: 14px; line-height: 1.6; }}
    .panel {{ padding: 22px; margin-top: 18px; }}
    .panel h2 {{ margin: 0 0 14px; font-size: 22px; }}
    .cols {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-top: 18px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      font-size: 14px;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    ul {{ margin: 0; padding-left: 18px; line-height: 1.8; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
      font-weight: 600;
    }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .footer {{ margin-top: 18px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 900px) {{
      .cols {{ grid-template-columns: 1fr; }}
      .hero h1 {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="badge">每日 10:00 自动刷新看板</div>
      <h1>FISHGOO 广告负责人看板</h1>
      <p>这版看板现在会由服务器每天固定自动拉一次 Google Ads live 数据，自动生成日审、重建项目记忆、刷新看板并发布。</p>
      <p>最近一次自动刷新：<strong>{refreshed_at.strftime("%Y-%m-%d %H:%M:%S")}</strong> · 最近日审文档：<strong>{feedback_path.name}</strong></p>
    </section>

    <section class="grid">
      <article class="card">
        <div class="eyebrow">Today Spend</div>
        <div class="value">${summary['today']['cost_usd']:.2f}</div>
        <div class="note">当前时点点击 {summary['today']['clicks']} · 展示 {summary['today']['impressions']}</div>
      </article>
      <article class="card">
        <div class="eyebrow">Yesterday Spend</div>
        <div class="value">${summary['yesterday']['cost_usd']:.2f}</div>
        <div class="note">昨日点击 {summary['yesterday']['clicks']} · 转化 {summary['yesterday']['conversions']}</div>
      </article>
      <article class="card">
        <div class="eyebrow">Last 7 Days</div>
        <div class="value">${summary['last_7d']['cost_usd']:.2f}</div>
        <div class="note">近 7 天点击 {summary['last_7d']['clicks']} · 转化 {summary['last_7d']['conversions']}</div>
      </article>
      <article class="card">
        <div class="eyebrow">Measurement</div>
        <div class="value {'good' if not measurement['signup_primary'] else 'warn'}">{'Needs Fix' if measurement['signup_primary'] else 'Improved'}</div>
        <div class="note">Purchase primary={measurement['purchase_primary']} · Signup primary={measurement['signup_primary']}</div>
      </article>
    </section>

    <section class="cols">
      <div>
        <section class="panel">
          <h2>当前负责人判断</h2>
          <ul>{render_lines(current_judgment)}</ul>
        </section>
        <section class="panel">
          <h2>今日动作建议</h2>
          <ul>{render_lines(next_actions)}</ul>
        </section>
        <section class="panel">
          <h2>Live Campaign 结构</h2>
          <table>
            <thead>
              <tr><th>Campaign</th><th>Type</th><th>Status</th><th>Primary</th><th>Budget</th></tr>
            </thead>
            <tbody>
              {campaign_rows}
            </tbody>
          </table>
        </section>
      </div>
      <div>
        <section class="panel">
          <h2>最近 10 次日审时间线</h2>
          <table>
            <thead><tr><th>Day</th><th>Date</th><th>Title</th></tr></thead>
            <tbody>{timeline_rows}</tbody>
          </table>
        </section>
        <section class="panel">
          <h2>Website Goals 快照</h2>
          <table>
            <thead><tr><th>Campaign</th><th>Goal</th><th>Biddable</th></tr></thead>
            <tbody>{website_goal_rows}</tbody>
          </table>
        </section>
        <section class="panel">
          <h2>自动刷新说明</h2>
          <ul>
            <li>每天 10:00 服务器自动跑一次日审。</li>
            <li>自动生成当天反馈文档并写入生成目录。</li>
            <li>自动重建 memory，Claude 读取时也能拿到最新时间线。</li>
            <li>自动发布到 `https://mcp.perrilee.com/ad-board/`。</li>
          </ul>
          <div class="footer">看板来源：Google Ads 只读审计 + 结构化项目记忆。当前页面为自动生成版。</div>
        </section>
      </div>
    </section>
  </div>
</body>
</html>
"""


def write_generated_board_html(
    payload: dict[str, Any], refreshed_at: datetime, feedback_path: Path
) -> Path:
    GENERATED_BOARD_HTML.parent.mkdir(parents=True, exist_ok=True)
    timeline = build_audit_timeline()
    current_truth = read_current_truth()
    GENERATED_BOARD_HTML.write_text(
        render_board_html(payload, refreshed_at, feedback_path, timeline, current_truth),
        encoding="utf-8",
    )
    return GENERATED_BOARD_HTML
