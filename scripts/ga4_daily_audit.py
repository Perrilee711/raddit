#!/usr/bin/env python3
"""
GA4 每日三源对账 · 拉昨日 purchase event 数据

设计意图：Day 27 诊断发现 GA4 purchase event 在 duplicate firing
（13 天 576 event vs Metabase 真实 36 单 · 每真实订单 fire 平均 16 次）。
在 GTM 技术修好前,持续监测 GA4 侧 fire pattern,一旦技术改动生效立刻
能看到失真度变化.

用法（手动）:
  source /root/raddit/.venv/bin/activate
  GOOGLE_APPLICATION_CREDENTIALS=/root/raddit/.env/ga4-sa.json \\
      python scripts/ga4_daily_audit.py --date 2026-04-20

用法（自动，通过 systemd timer 每天 10:00 跑）：
  由 scripts/run_fishgoo_daily_refresh.py 调用（通过 subprocess）

输出:
  data/fishgoo_generated/ga4_daily/{YYYY-MM-DD}.json
  结构:
  {
    "date": "2026-04-20",
    "pulled_at": "2026-04-21T10:00:00",
    "ga4_property_id": "494561223",
    "event_count_total": 37,
    "revenue_total_cny": 4679.17,
    "revenue_total_usd": 679.00,
    "transactions": [
      {"transaction_id": "abc123", "event_count": 12, "revenue_cny": 1234.00},
      ...
    ],
    "dup_ratio_by_txn": [
      {"transaction_id": "abc123", "dup_count": 12},
      ...
    ],
    "unique_transactions": 5,
    "warnings": ["5 transactions fired >10 times each"]
  }
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


GA4_PROPERTY_ID = "494561223"
FX_RATE_CNY_USD = 6.8921  # 看板管理口径
CRED_PATH = "/root/raddit/.env/ga4-sa.json"

# 输出目录
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "fishgoo_generated" / "ga4_daily"


def _yesterday_iso() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def check_credentials() -> None:
    """Credential sanity check —— 服务器上 SA JSON 是否就位 + 权限对."""
    if not Path(CRED_PATH).exists():
        sys.exit(
            f"ERROR: {CRED_PATH} not found.\n"
            "Perri 需要:\n"
            "  1. 在 Google Cloud Console 给 fishgoo-ga4-audit SA 建 JSON key\n"
            "  2. scp 到服务器 {CRED_PATH}, chmod 600\n"
            "  3. 在 GA4 property 494561223 授予该 SA 查看者权限\n"
        )
    stat = Path(CRED_PATH).stat()
    if stat.st_mode & 0o077:  # 组或其他用户有权限 = 不安全
        print(f"WARN: {CRED_PATH} 权限过宽 ({oct(stat.st_mode)}), 建议 chmod 600")


def pull_ga4_purchase_events(target_date: str) -> dict:
    """Pull purchase events from GA4 Data API for a single day.

    使用 event_name=purchase 过滤,按 transaction_id 拆分计数.
    """
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", CRED_PATH)

    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        DimensionFilter,
        Filter,
        FilterExpression,
        Metric,
        RunReportRequest,
    )

    client = BetaAnalyticsDataClient()

    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[
            Dimension(name="date"),
            Dimension(name="eventName"),
            Dimension(name="transactionId"),
        ],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="purchaseRevenue"),
        ],
        date_ranges=[DateRange(start_date=target_date, end_date=target_date)],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="purchase"),
            )
        ),
        limit=10000,
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        txn_id = row.dimension_values[2].value or "(no_transaction_id)"
        event_count = int(row.metric_values[0].value)
        revenue_cny = float(row.metric_values[1].value)
        rows.append({
            "transaction_id": txn_id,
            "event_count": event_count,
            "revenue_cny": round(revenue_cny, 2),
        })

    return {
        "rows": rows,
        "row_count": len(rows),
    }


def analyze(date_str: str, ga4_data: dict) -> dict:
    """把 GA4 原始行数据聚合成三源对账需要的信号."""
    rows = ga4_data["rows"]
    event_count_total = sum(r["event_count"] for r in rows)
    revenue_total_cny = sum(r["revenue_cny"] for r in rows)

    # 按 transaction_id 聚合（识别 duplicate firing）
    by_txn = defaultdict(lambda: {"event_count": 0, "revenue_cny": 0})
    for r in rows:
        by_txn[r["transaction_id"]]["event_count"] += r["event_count"]
        by_txn[r["transaction_id"]]["revenue_cny"] += r["revenue_cny"]

    dup_ratio = []
    heavy_dup = []
    for txn_id, v in by_txn.items():
        dup_ratio.append({
            "transaction_id": txn_id,
            "dup_count": v["event_count"],
            "revenue_cny": round(v["revenue_cny"], 2),
        })
        if v["event_count"] > 5:
            heavy_dup.append((txn_id, v["event_count"]))

    warnings = []
    if heavy_dup:
        warnings.append(
            f"{len(heavy_dup)} transactions fired >5 times each "
            f"(max: {max(c for _, c in heavy_dup)} dup) · GTM purchase "
            f"trigger 仍然未修"
        )

    if event_count_total > 0 and len(by_txn) == 1 and "(no_transaction_id)" in by_txn:
        warnings.append(
            "all purchase events missing transaction_id · GTM dataLayer "
            "push 可能没传 transaction_id"
        )

    return {
        "date": date_str,
        "pulled_at": datetime.now().isoformat(timespec="seconds"),
        "ga4_property_id": GA4_PROPERTY_ID,
        "event_count_total": event_count_total,
        "revenue_total_cny": round(revenue_total_cny, 2),
        "revenue_total_usd": round(revenue_total_cny / FX_RATE_CNY_USD, 2),
        "unique_transactions": len(by_txn),
        "dup_ratio_by_txn": sorted(dup_ratio, key=lambda x: -x["dup_count"]),
        "warnings": warnings,
    }


def write_output(result: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{result['date']}.json"
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "--date",
        help="YYYY-MM-DD. Defaults to yesterday.",
        default=_yesterday_iso(),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output file, print to stdout only.",
    )
    args = parser.parse_args()

    check_credentials()

    print(f"Pulling GA4 purchase events for {args.date}...", file=sys.stderr)
    ga4_data = pull_ga4_purchase_events(args.date)
    print(f"  Got {ga4_data['row_count']} rows", file=sys.stderr)

    result = analyze(args.date, ga4_data)

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    out_path = write_output(result)
    print(f"✅ Wrote {out_path}", file=sys.stderr)

    # Concise summary to stdout (json, parseable by wrapper script)
    print(json.dumps({
        "date": result["date"],
        "event_count": result["event_count_total"],
        "revenue_cny": result["revenue_total_cny"],
        "revenue_usd": result["revenue_total_usd"],
        "unique_transactions": result["unique_transactions"],
        "output": str(out_path),
        "warnings": result["warnings"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
