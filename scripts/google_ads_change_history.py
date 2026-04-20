#!/usr/bin/env python3
import argparse
from collections.abc import Iterable, Mapping
import json
import os
from pathlib import Path

from ads_mcp.tools.search import search


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


def sanitize(value):
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer-id", default="1573113113")
    parser.add_argument("--from-datetime", required=True)
    parser.add_argument("--to-datetime", required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    load_google_ads_env()

    rows = search(
        customer_id=args.customer_id,
        fields=[
            "change_event.change_date_time",
            "change_event.change_resource_type",
            "change_event.resource_change_operation",
            "change_event.user_email",
            "change_event.client_type",
            "change_event.old_resource",
            "change_event.new_resource",
        ],
        resource="change_event",
        conditions=[
            f"change_event.change_date_time >= '{args.from_datetime}'",
            f"change_event.change_date_time <= '{args.to_datetime}'",
        ],
        orderings=["change_event.change_date_time DESC"],
        limit=args.limit,
    )
    print(json.dumps(sanitize(rows), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
