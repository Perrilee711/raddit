from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from apps.fishgoo_mcp.memory.builder import build_audit_timeline
from apps.fishgoo_mcp.memory.readers import read_current_truth
from apps.fishgoo_mcp.paths import (
    BOARD_HTML,
    GENERATED_BOARD_HTML,
    GENERATED_DAILY_DIR,
    GENERATED_DAILY_JSON_DIR,
    GENERATED_GA4_DAILY_DIR,
)


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


def _live_status_label(summary: dict[str, Any]) -> tuple[str, str]:
    today_cost = summary["today"]["cost_usd"]
    yesterday_cost = summary["yesterday"]["cost_usd"]
    if today_cost == 0:
        return (
            "晨间未起量",
            "当前时点仍为 0 花费；若 14:00 仍 0 则按全天异常处理",
        )
    if yesterday_cost > 0 and today_cost < yesterday_cost * 0.5:
        return (
            "起量偏慢",
            f"今日 ${today_cost:.2f} 未达昨日 ${yesterday_cost:.2f} 的一半",
        )
    return (
        "正常起量",
        f"今日已花 ${today_cost:.2f} / 昨日 ${yesterday_cost:.2f}",
    )


def _most_important_action(current_truth: dict[str, Any]) -> str:
    actions = current_truth.get("next_actions_excerpt") or []
    for line in actions:
        text = line.lstrip("- ").strip()
        if text:
            return text[:40]
    return "保成交 + 修目标"


def render_current_ops_block(
    summary: dict[str, Any],
    day_label: str,
    refreshed_at: datetime,
    current_truth: dict[str, Any],
) -> str:
    live_value, live_note = _live_status_label(summary)
    day_num = day_label.replace("Day", "") or "?"
    return (
        '      <div class="grid grid-4">\n'
        '        <div class="metric-card">\n'
        '          <div class="metric-label">当前 live 状态</div>\n'
        f'          <div class="metric-value">{live_value}</div>\n'
        f'          <div class="metric-note">{live_note}</div>\n'
        '        </div>\n'
        '        <div class="metric-card">\n'
        '          <div class="metric-label">最近一次成功 live</div>\n'
        f'          <div class="metric-value">{refreshed_at.strftime("%Y-%m-%d")}</div>\n'
        f'          <div class="metric-note">自动刷新于 {refreshed_at.strftime("%H:%M")}，下一次 10:00 再跑</div>\n'
        '        </div>\n'
        '        <div class="metric-card">\n'
        '          <div class="metric-label">阶段判断</div>\n'
        f'          <div class="metric-value">{day_label}</div>\n'
        f'          <div class="metric-note">累计 {day_num} 天观测窗（自 2026-03-26 起）</div>\n'
        '        </div>\n'
        '        <div class="metric-card">\n'
        '          <div class="metric-label">当前最重要任务</div>\n'
        f'          <div class="metric-value">{_most_important_action(current_truth)}</div>\n'
        '          <div class="metric-note">来源：memory/current_truth.json · next_actions_excerpt</div>\n'
        '        </div>\n'
        '      </div>'
    )


def render_refresh_banner(refreshed_at: datetime, day_label: str, feedback_name: str) -> str:
    return (
        '      <div class="metric-note" style="margin-bottom:12px;opacity:0.8;">'
        f'自动刷新：<strong>{refreshed_at.strftime("%Y-%m-%d %H:%M:%S")}</strong> · '
        f'{day_label} · 日审文档：<code>{feedback_name}</code> · 来源：Google Ads 只读审计'
        '</div>'
    )


def _extract_day_signature(md_text: str) -> str:
    """Extract Day-specific signature from an auto-generated Day feedback md.

    Auto-generated md files share a templated first paragraph ('当前看板已经
    切换为每日自动刷新模式...') — useless as a Day differentiator. Instead we
    pull the 4 concrete numbers (impressions/clicks/cost/conversions) that
    actually vary day to day.
    """
    impr_m = re.search(r"今日截至当前展示：`(\d+)`", md_text)
    clicks_m = re.search(r"今日截至当前点击：`(\d+)`", md_text)
    cost_m = re.search(r"今日截至当前花费：`\$([\d.]+)`", md_text)
    conv_m = re.search(r"今日截至当前 Ads 转化：`([\d.]+)`", md_text)

    if not any([impr_m, clicks_m, cost_m, conv_m]):
        return "已自动日审，详见 Day 反馈 md。"

    impr = impr_m.group(1) if impr_m else "-"
    clicks = clicks_m.group(1) if clicks_m else "-"
    cost = cost_m.group(1) if cost_m else "-"
    conv = conv_m.group(1) if conv_m else "-"

    # Determine headline judgment from cost
    try:
        cost_num = float(cost) if cost != "-" else 0.0
    except ValueError:
        cost_num = 0.0

    if cost_num == 0:
        judgment = "早盘未起量（10:00 时点 $0 花费，属正常冷启动）"
    elif cost_num < 10:
        judgment = f"早盘慢启动（10:00 时点 ${cost}，低于日均）"
    else:
        judgment = f"已正常起量（10:00 时点 ${cost}）"

    return f"10:00 快照：展示 {impr} · 点击 {clicks} · 花费 ${cost} · Ads 转化 {conv}。判断：{judgment}。"


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_learning_recent_block() -> str:
    """Render Day 24+ timeline items from auto-generated daily feedback md files."""
    from apps.fishgoo_mcp.paths import GENERATED_DAILY_DIR

    if not GENERATED_DAILY_DIR.exists():
        return "          <!-- no Day 24+ feedback yet · block will populate after first auto-refresh -->"

    items = []
    files = sorted(GENERATED_DAILY_DIR.glob("Day*反馈_*.md"))
    for md_path in files:
        match = re.match(r"Day(\d+)反馈_(\d{4}-\d{2}-\d{2})", md_path.stem)
        if not match:
            continue
        day_num = int(match.group(1))
        day_date = match.group(2)
        if day_num < 24:
            continue

        text = md_path.read_text(encoding="utf-8")
        note_raw = _extract_day_signature(text)
        note = _html_escape(note_raw)[:280]

        items.append(
            '          <div class="timeline-item">\n'
            f'            <div class="timeline-head"><span class="timeline-day">Day {day_num}</span>'
            f'<span class="timeline-date">{day_date}</span>'
            '<span class="pill pill-ok">已自动生成</span></div>\n'
            '            <div class="timeline-focus">自动日审 TL;DR（来自 Day 反馈 md 核心结论）</div>\n'
            f'            <div class="timeline-note">{note}</div>\n'
            "          </div>"
        )

    if not items:
        return "          <!-- no Day 24+ feedback yet · block will populate after first auto-refresh -->"
    return "\n".join(items)


def _load_recent_ga4_days(max_days: int = 7) -> list[dict[str, Any]]:
    """Read the last N ga4_daily/*.json files sorted by date desc."""
    if not GENERATED_GA4_DAILY_DIR.exists():
        return []
    files = sorted(GENERATED_GA4_DAILY_DIR.glob("*.json"), reverse=True)[:max_days]
    results = []
    for p in files:
        try:
            results.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def _ga4_noise_stats(day: dict[str, Any]) -> dict[str, Any]:
    """Compute noise vs real events from a ga4_daily json payload."""
    total = int(day.get("event_count_total") or 0)
    dup_rows = day.get("dup_ratio_by_txn") or []
    noise = 0
    max_dup = 0
    for row in dup_rows:
        cnt = int(row.get("dup_count") or 0)
        if cnt > max_dup:
            max_dup = cnt
        if row.get("transaction_id") == "(no_transaction_id)":
            noise += cnt
    real = max(total - noise, 0)
    ratio = (noise / total * 100.0) if total > 0 else 0.0
    return {
        "date": day.get("date"),
        "total": total,
        "real": real,
        "noise": noise,
        "noise_ratio": ratio,
        "max_dup": max_dup,
        "unique_txn": int(day.get("unique_transactions") or 0),
    }


def render_ga4_noise_block() -> str:
    """Render GA4 purchase event noise monitor card.

    Pulls from data/fishgoo_generated/ga4_daily/*.json. If GTM is fixed, the
    '(no_transaction_id)' bucket disappears → noise_ratio → 0%. This block
    is how we'll see that fix land in production within 24h.
    """
    days = _load_recent_ga4_days(7)
    if not days:
        return (
            '      <div class="card" style="margin-top:16px;border-left:4px solid #64748b;">\n'
            '        <h3>🧪 GA4 purchase event 噪声监测</h3>\n'
            '        <div class="metric-note">等待第一次自动刷新写入 ga4_daily/*.json · 明天 10:00 后自动展示</div>\n'
            '      </div>'
        )

    latest = _ga4_noise_stats(days[0])
    rows = [_ga4_noise_stats(d) for d in days]
    avg_ratio = sum(r["noise_ratio"] for r in rows) / len(rows)

    def _pill(ratio: float) -> str:
        if ratio >= 50.0:
            return '<span class="pill pill-danger">重污染</span>'
        if ratio >= 20.0:
            return '<span class="pill pill-warn">中等</span>'
        if ratio > 0:
            return '<span class="pill pill-warn">轻微</span>'
        return '<span class="pill pill-ok">已净化</span>'

    table_rows = []
    for r in rows:
        table_rows.append(
            '            <tr>'
            f'<td>{r["date"]}</td>'
            f'<td>{r["total"]}</td>'
            f'<td>{r["real"]}</td>'
            f'<td style="color:#b45309;font-weight:600;">{r["noise"]}</td>'
            f'<td>{r["noise_ratio"]:.1f}%</td>'
            f'<td>{r["max_dup"]}</td>'
            f'<td>{_pill(r["noise_ratio"])}</td>'
            '</tr>'
        )

    latest_pill = _pill(latest["noise_ratio"])
    healthy_banner = ""
    if avg_ratio < 5.0:
        healthy_banner = (
            '        <div class="metric-note" style="margin-top:10px;font-weight:600;color:#059669;">\n'
            '          ✅ <strong>GTM 已修</strong>：近 7 天平均噪声占比 < 5%，可以安全切换 Pmax MAX_CONVERSION_VALUE + tROAS。\n'
            '        </div>'
        )
    elif avg_ratio >= 50.0:
        healthy_banner = (
            '        <div class="metric-note" style="margin-top:10px;font-weight:600;color:#dc2626;">\n'
            '          ⚠️ <strong>GTM 未修</strong>：噪声比例依然 ≥50% · Ads 侧靠原生过滤保平安 · 技术同学修完 transaction_id condition 此处会归零。\n'
            '        </div>'
        )
    else:
        healthy_banner = (
            '        <div class="metric-note" style="margin-top:10px;font-weight:600;color:#b45309;">\n'
            f'          🔄 <strong>部分修复</strong>：近 7 天平均噪声 {avg_ratio:.1f}% · 已在好转 · 持续观察 3 天若继续降则可评估切 value-based bidding。\n'
            '        </div>'
        )

    return (
        '      <div class="card" style="margin-top:16px;border-left:4px solid #0e7490;">\n'
        '        <h3>🧪 GA4 purchase event 噪声监测（Day 27 打通 · 每天 10:00 自动刷）</h3>\n'
        '        <div class="metric-note" style="margin-bottom:12px;">\n'
        f'          数据源：<code>data/fishgoo_generated/ga4_daily/*.json</code> · '
        f'最新：<strong>{latest["date"]}</strong> · GA4 Property <code>494561223</code> · SA 拉 Data API\n'
        '        </div>\n'
        '        <div class="grid grid-4">\n'
        '          <div class="metric-card">\n'
        '            <div class="metric-label">最新一天噪声占比</div>\n'
        f'            <div class="metric-value">{latest["noise_ratio"]:.1f}%</div>\n'
        f'            <div class="metric-note">{latest_pill} · 空 txn_id event 占比</div>\n'
        '          </div>\n'
        '          <div class="metric-card">\n'
        '            <div class="metric-label">真实 events（带 txn_id）</div>\n'
        f'            <div class="metric-value">{latest["real"]}</div>\n'
        f'            <div class="metric-note">Ads 侧能看到的就是这部分</div>\n'
        '          </div>\n'
        '          <div class="metric-card">\n'
        '            <div class="metric-label">噪声 events（空 txn_id）</div>\n'
        f'            <div class="metric-value" style="color:#b45309;">{latest["noise"]}</div>\n'
        f'            <div class="metric-note">GTM 修完此处应归零</div>\n'
        '          </div>\n'
        '          <div class="metric-card">\n'
        '            <div class="metric-label">7 日均噪声占比</div>\n'
        f'            <div class="metric-value">{avg_ratio:.1f}%</div>\n'
        f'            <div class="metric-note">{len(rows)} 天窗口 · 趋势指标</div>\n'
        '          </div>\n'
        '        </div>\n'
        '        <div class="card" style="margin-top:12px;background:#ecfeff;">\n'
        '          <h3>📊 近 7 天逐日噪声</h3>\n'
        '          <table>\n'
        '            <tr><th>日期</th><th>总 event</th><th>真实</th><th>噪声</th><th>噪声占比</th><th>单桶 max</th><th>判断</th></tr>\n'
        + "\n".join(table_rows) + "\n"
        '          </table>\n'
        '        </div>\n'
        + healthy_banner + "\n"
        '      </div>'
    )


def render_freshness_stamp(refreshed_at: datetime, day_label: str) -> str:
    """Render the green "page-top freshness stamp" so users instantly see this is today's data."""
    tomorrow = refreshed_at.date() + timedelta(days=1)
    next_refresh = f"{tomorrow.isoformat()} 10:00 CST"
    return (
        '    <div class="freshness-stamp">\n'
        '      <span class="stamp-icon">✨</span>\n'
        '      <span>本页数据截至：<code>'
        f'{refreshed_at.strftime("%Y-%m-%d %H:%M:%S")}</code> · '
        f'<strong>{day_label}</strong> · 下次自动刷新 <code>{next_refresh}</code></span>\n'
        '    </div>'
    )


_AUTO_MARKER_PATTERN = re.compile(
    r"<!--\s*AUTO:(?P<name>[A-Z0-9_]+):START\s*-->.*?<!--\s*AUTO:(?P=name):END\s*-->",
    re.DOTALL,
)


def inject_into_v3_template(template_html: str, replacements: dict[str, str]) -> str:
    def _swap(match: re.Match) -> str:
        name = match.group("name")
        new_body = replacements.get(name)
        if new_body is None:
            return match.group(0)
        return (
            f"<!-- AUTO:{name}:START -->\n"
            f"{new_body}\n"
            f"      <!-- AUTO:{name}:END -->"
        )

    return _AUTO_MARKER_PATTERN.sub(_swap, template_html)


def render_board_html(
    payload: dict[str, Any],
    refreshed_at: datetime,
    feedback_path: Path,
    timeline: list[dict[str, Any]],
    current_truth: dict[str, Any],
) -> str:
    """Render the auto-refreshed board.

    If the V3 template at `BOARD_HTML` exists, inject fresh data into the
    AUTO:* markers and return the hybrid V3 output. Otherwise fall back to
    the from-scratch auto board (original behaviour).
    """
    if BOARD_HTML.exists():
        summary = summarize_payload(payload)
        day_label = day_label_for_date(refreshed_at.date())
        template = BOARD_HTML.read_text(encoding="utf-8")
        ops_block = render_current_ops_block(summary, day_label, refreshed_at, current_truth)
        banner_block = render_refresh_banner(refreshed_at, day_label, feedback_path.name)
        freshness_stamp = render_freshness_stamp(refreshed_at, day_label)
        learning_recent = render_learning_recent_block()
        ga4_noise = render_ga4_noise_block()
        return inject_into_v3_template(
            template,
            {
                "FRESHNESS_STAMP": freshness_stamp,
                "CURRENT_OPS": ops_block,
                "REFRESH_BANNER": banner_block,
                "LEARNING_RECENT": learning_recent,
                "GA4_NOISE_MONITOR": ga4_noise,
            },
        )
    return _render_fallback_board_html(payload, refreshed_at, feedback_path, timeline, current_truth)


def _render_fallback_board_html(
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
