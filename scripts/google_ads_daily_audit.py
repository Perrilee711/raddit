#!/usr/bin/env python3
"""Run a reusable read-only Google Ads daily audit via the local Google Ads MCP package.

Outputs JSON to stdout for the requested date.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any


def load_google_ads_env() -> None:
    if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"):
        project_id = os.environ.get("GOOGLE_PROJECT_ID")
        if project_id:
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
        return

    claude_config = Path.home() / ".claude.json"
    payload = json.loads(claude_config.read_text())
    env = payload["mcpServers"]["google-ads-mcp"]["env"]
    for key, value in env.items():
        os.environ.setdefault(key, value)
    project_id = env.get("GOOGLE_PROJECT_ID")
    if project_id:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)


def query(
    customer_id: str,
    *,
    fields: list[str],
    resource: str,
    conditions: list[str] | None = None,
    orderings: list[str] | None = None,
    limit: int | str | None = None,
) -> list[dict[str, Any]]:
    from ads_mcp.tools.search import search

    return search(
        customer_id=customer_id,
        fields=fields,
        resource=resource,
        conditions=conditions,
        orderings=orderings,
        limit=limit,
    )


def sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, tuple):
        return [sanitize(v) for v in value]
    if isinstance(value, (str, bytes, bytearray)):
        return value
    if hasattr(value, "__iter__") and value.__class__.__name__.startswith("Repeated"):
        return [sanitize(v) for v in value]
    if isinstance(value, Iterable):
        try:
            return [sanitize(v) for v in value]
        except TypeError:
            return value
    return value


def safe_query(
    out: dict[str, Any],
    errors: dict[str, str],
    key: str,
    customer_id: str,
    *,
    fields: list[str],
    resource: str,
    conditions: list[str] | None = None,
    orderings: list[str] | None = None,
    limit: int | str | None = None,
) -> None:
    try:
        out[key] = query(
            customer_id,
            fields=fields,
            resource=resource,
            conditions=conditions,
            orderings=orderings,
            limit=limit,
        )
    except Exception as exc:  # pragma: no cover - resilience path for flaky API/network
        out[key] = []
        errors[key] = repr(exc)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Audit date in YYYY-MM-DD")
    parser.add_argument("--customer-id", default="1573113113")
    args = parser.parse_args()

    load_google_ads_env()

    audit_day = date.fromisoformat(args.date)
    yesterday = audit_day - timedelta(days=1)
    seven_days_ago = audit_day - timedelta(days=6)

    d = audit_day.isoformat()
    dy = yesterday.isoformat()
    d7 = seven_days_ago.isoformat()

    out: dict[str, Any] = {"date": d, "customer_id": args.customer_id}
    errors: dict[str, str] = {}

    safe_query(
        out,
        errors,
        "account_today",
        args.customer_id,
        resource="customer",
        fields=[
            "customer.id",
            "customer.descriptive_name",
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
        ],
        conditions=[f"segments.date = '{d}'"],
        limit=10,
    )

    safe_query(
        out,
        errors,
        "campaigns_today",
        args.customer_id,
        resource="campaign",
        fields=[
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "campaign.advertising_channel_type",
            "campaign.serving_status",
            "campaign.primary_status",
            "campaign.primary_status_reasons",
            "campaign.bidding_strategy_type",
            "campaign_budget.amount_micros",
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
        ],
        conditions=[f"segments.date = '{d}'", "campaign.status != 'REMOVED'"],
        orderings=["metrics.cost_micros DESC"],
        limit=100,
    )

    safe_query(
        out,
        errors,
        "campaigns_yesterday",
        args.customer_id,
        resource="campaign",
        fields=[
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "campaign.advertising_channel_type",
            "campaign.serving_status",
            "campaign.primary_status",
            "campaign.bidding_strategy_type",
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
        ],
        conditions=[f"segments.date = '{dy}'", "campaign.status != 'REMOVED'"],
        orderings=["metrics.cost_micros DESC"],
        limit=100,
    )

    safe_query(
        out,
        errors,
        "campaigns_last_7d",
        args.customer_id,
        resource="campaign",
        fields=[
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "campaign.advertising_channel_type",
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
        ],
        conditions=[
            f"segments.date >= '{d7}'",
            f"segments.date <= '{d}'",
            "campaign.status != 'REMOVED'",
        ],
        orderings=["metrics.cost_micros DESC"],
        limit=100,
    )

    safe_query(
        out,
        errors,
        "search_terms_today",
        args.customer_id,
        resource="search_term_view",
        fields=[
            "search_term_view.search_term",
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "ad_group.id",
            "ad_group.name",
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
        ],
        conditions=[
            f"segments.date = '{d}'",
            "campaign.status != 'REMOVED'",
            "metrics.impressions > 0",
        ],
        orderings=["metrics.cost_micros DESC"],
        limit=100,
    )

    safe_query(
        out,
        errors,
        "keywords_today",
        args.customer_id,
        resource="keyword_view",
        fields=[
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "ad_group.id",
            "ad_group.name",
            "ad_group_criterion.criterion_id",
            "ad_group_criterion.status",
            "ad_group_criterion.keyword.text",
            "ad_group_criterion.keyword.match_type",
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
        ],
        conditions=[f"segments.date = '{d}'", "campaign.status != 'REMOVED'"],
        orderings=["metrics.cost_micros DESC"],
        limit=200,
    )

    safe_query(
        out,
        errors,
        "conversion_actions",
        args.customer_id,
        resource="conversion_action",
        fields=[
            "conversion_action.id",
            "conversion_action.name",
            "conversion_action.status",
            "conversion_action.category",
            "conversion_action.type",
            "conversion_action.include_in_conversions_metric",
            "conversion_action.primary_for_goal",
        ],
        conditions=["conversion_action.status != 'REMOVED'"],
        orderings=["conversion_action.name ASC"],
        limit=200,
    )

    safe_query(
        out,
        errors,
        "campaign_goals",
        args.customer_id,
        resource="campaign_conversion_goal",
        fields=[
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "campaign.advertising_channel_type",
            "campaign_conversion_goal.category",
            "campaign_conversion_goal.origin",
            "campaign_conversion_goal.biddable",
        ],
        conditions=["campaign.status != 'REMOVED'"],
        orderings=[
            "campaign.name ASC",
            "campaign_conversion_goal.category ASC",
            "campaign_conversion_goal.origin ASC",
        ],
        limit=1000,
    )

    out["errors"] = errors

    print(json.dumps(sanitize(out), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
