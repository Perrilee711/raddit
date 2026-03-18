#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from reddit_research_report import generate_report


DEFAULT_HOSTS = ["old.reddit.com", "www.reddit.com"]
DEFAULT_USER_AGENT = "raddit-research-bot/0.1 by perrilee"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_HOST = "oauth.reddit.com"


@dataclass
class FetchConfig:
    subreddits: list[str]
    search_terms: list[str]
    listing_sort: str
    time_filter: str
    limit_per_request: int
    pages_per_term: int
    include_listing_fetch: bool
    request_delay_seconds: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Reddit lead-intent posts from selected subreddits and generate a Markdown report."
    )
    parser.add_argument(
        "--config",
        default="config/reddit_targets.json",
        help="Path to the target config JSON file.",
    )
    parser.add_argument(
        "--raw-output",
        help="Path to save raw JSONL records. Defaults to data/raw/<timestamp>_reddit_posts.jsonl",
    )
    parser.add_argument(
        "--report-output",
        help="Path to save the Markdown report. Defaults to docs/reports/<timestamp>_reddit-research.md",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Keep only posts newer than this many days based on created_utc.",
    )
    parser.add_argument(
        "--top-leads",
        type=int,
        default=15,
        help="How many high-intent posts to include in the report.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="Custom User-Agent string for requests.",
    )
    parser.add_argument(
        "--hosts",
        nargs="+",
        default=DEFAULT_HOSTS,
        help="Host fallback order for Reddit JSON pages.",
    )
    return parser.parse_args()


def load_config(path: Path) -> FetchConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return FetchConfig(
        subreddits=data["subreddits"],
        search_terms=data["search_terms"],
        listing_sort=data.get("listing_sort", "new"),
        time_filter=data.get("time_filter", "month"),
        limit_per_request=int(data.get("limit_per_request", 25)),
        pages_per_term=int(data.get("pages_per_term", 2)),
        include_listing_fetch=bool(data.get("include_listing_fetch", True)),
        request_delay_seconds=float(data.get("request_delay_seconds", 1.5)),
    )


def fetch_json(url: str, user_agent: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_json_with_headers(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def get_oauth_token(user_agent: str) -> str | None:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")

    if not client_id or not client_secret:
        return None

    grant_data: dict[str, str]
    if username and password:
        grant_data = {
            "grant_type": "password",
            "username": username,
            "password": password,
        }
    else:
        grant_data = {
            "grant_type": "client_credentials",
        }

    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    encoded_body = urlencode(grant_data).encode("utf-8")
    request = Request(
        TOKEN_URL,
        data=encoded_body,
        headers={
            "Authorization": f"Basic {basic_auth}",
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Reddit OAuth token response did not include access_token.")
    return str(token)


def candidate_urls(
    hosts: list[str],
    subreddit: str,
    path: str,
    params: dict[str, Any],
) -> list[str]:
    query = urlencode({key: value for key, value in params.items() if value not in (None, "")})
    return [f"https://{host}/r/{subreddit}/{path}?{query}" for host in hosts]


def oauth_url(subreddit: str, path: str, params: dict[str, Any]) -> str:
    query = urlencode({key: value for key, value in params.items() if value not in (None, "")})
    return f"https://{OAUTH_HOST}/r/{subreddit}/{path}?{query}"


def normalize_post(post: dict[str, Any], subreddit: str, source: str, search_term: str) -> dict[str, Any]:
    permalink = post.get("permalink") or ""
    return {
        "id": post.get("id"),
        "name": post.get("name"),
        "subreddit": post.get("subreddit") or subreddit,
        "title": post.get("title", ""),
        "body": post.get("selftext", ""),
        "author": post.get("author", ""),
        "url": f"https://www.reddit.com{permalink}" if permalink else post.get("url", ""),
        "permalink": permalink,
        "created_utc": post.get("created_utc"),
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "link_flair_text": post.get("link_flair_text"),
        "search_term": search_term,
        "source_endpoint": source,
    }


def parse_listing(payload: dict[str, Any]) -> list[dict[str, Any]]:
    children = payload.get("data", {}).get("children", [])
    results = []
    for child in children:
        if isinstance(child, dict) and child.get("kind") == "t3":
            data = child.get("data")
            if isinstance(data, dict):
                results.append(data)
    return results


def request_with_fallback(urls: list[str], user_agent: str) -> tuple[dict[str, Any], str]:
    last_error: Exception | None = None
    for url in urls:
        try:
            return fetch_json(url, user_agent), url
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
    if last_error is None:
        raise RuntimeError("No candidate URLs were generated.")
    raise last_error


def request_with_oauth(url: str, user_agent: str, token: str) -> tuple[dict[str, Any], str]:
    payload = fetch_json_with_headers(
        url,
        {
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )
    return payload, url


def fetch_search_posts(
    config: FetchConfig,
    subreddit: str,
    term: str,
    hosts: list[str],
    user_agent: str,
    oauth_token: str | None,
) -> list[dict[str, Any]]:
    all_posts = []
    after = None

    for _ in range(config.pages_per_term):
        params = {
            "q": term,
            "restrict_sr": "on",
            "sort": config.listing_sort,
            "t": config.time_filter,
            "limit": config.limit_per_request,
            "raw_json": 1,
            "after": after,
        }
        if oauth_token:
            payload, source = request_with_oauth(
                oauth_url(subreddit, "search", params), user_agent, oauth_token
            )
        else:
            urls = candidate_urls(hosts, subreddit, "search.json", params)
            payload, source = request_with_fallback(urls, user_agent)
        posts = parse_listing(payload)
        all_posts.extend(normalize_post(post, subreddit, source, term) for post in posts)
        after = payload.get("data", {}).get("after")
        if not after:
            break
        time.sleep(config.request_delay_seconds)

    return all_posts


def fetch_listing_posts(
    config: FetchConfig,
    subreddit: str,
    hosts: list[str],
    user_agent: str,
    oauth_token: str | None,
) -> list[dict[str, Any]]:
    params = {
        "limit": config.limit_per_request,
        "raw_json": 1,
        "t": config.time_filter,
    }
    if oauth_token:
        payload, source = request_with_oauth(
            oauth_url(subreddit, config.listing_sort, params), user_agent, oauth_token
        )
    else:
        path = f"{config.listing_sort}.json"
        urls = candidate_urls(hosts, subreddit, path, params)
        payload, source = request_with_fallback(urls, user_agent)
    posts = parse_listing(payload)
    return [normalize_post(post, subreddit, source, "__listing__") for post in posts]


def dedupe_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for post in posts:
        key = str(post.get("id") or post.get("url") or "")
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = post
            continue

        existing_term = existing.get("search_term", "")
        new_term = post.get("search_term", "")
        if new_term and new_term not in str(existing_term).split(" | "):
            existing["search_term"] = " | ".join(
                [part for part in [str(existing_term).strip(), str(new_term).strip()] if part]
            )
    return sorted(deduped.values(), key=lambda item: float(item.get("created_utc") or 0), reverse=True)


def filter_recent(posts: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    cutoff_ts = cutoff.timestamp()
    return [post for post in posts if float(post.get("created_utc") or 0) >= cutoff_ts]


def write_jsonl(path: Path, posts: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(post, ensure_ascii=False) for post in posts]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def build_default_paths() -> tuple[Path, Path]:
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    raw_path = Path("data/raw") / f"{stamp}_reddit_posts.jsonl"
    report_path = Path("docs/reports") / f"{stamp}_reddit-research.md"
    return raw_path, report_path


def run_pipeline(args: argparse.Namespace) -> tuple[Path, Path, int]:
    config = load_config(Path(args.config))
    default_raw, default_report = build_default_paths()
    raw_output = Path(args.raw_output) if args.raw_output else default_raw
    report_output = Path(args.report_output) if args.report_output else default_report
    oauth_token = get_oauth_token(args.user_agent)

    collected = []
    for subreddit in config.subreddits:
        if config.include_listing_fetch:
            collected.extend(
                fetch_listing_posts(config, subreddit, args.hosts, args.user_agent, oauth_token)
            )
            time.sleep(config.request_delay_seconds)
        for term in config.search_terms:
            collected.extend(
                fetch_search_posts(
                    config,
                    subreddit,
                    term,
                    args.hosts,
                    args.user_agent,
                    oauth_token,
                )
            )
            time.sleep(config.request_delay_seconds)

    recent_posts = filter_recent(dedupe_posts(collected), args.days)
    write_jsonl(raw_output, recent_posts)
    generate_report(raw_output, report_output, args.top_leads)
    return raw_output, report_output, len(recent_posts)


def main() -> None:
    args = parse_args()
    try:
        raw_output, report_output, count = run_pipeline(args)
    except Exception as error:
        print(f"Pipeline failed: {error}", file=sys.stderr)
        raise

    print(f"Fetched {count} posts")
    print(f"Raw data: {raw_output}")
    print(f"Report: {report_output}")


if __name__ == "__main__":
    main()
