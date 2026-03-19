#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from reddit_browser_common import (
    DEFAULT_CHROME_APP,
    build_search_url,
    dedupe_by_url,
    ensure_chrome_window,
    execute_js,
    load_config,
    open_url_in_chrome,
    scroll_page,
    wait_for_ready,
    write_jsonl,
)


DEFAULT_CONFIG_PATH = "config/reddit_targets.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover Reddit thread candidates from search pages using the local Chrome session."
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the target config JSON file.")
    parser.add_argument("--output", required=True, help="Path to save discovered thread JSONL.")
    parser.add_argument("--chrome-app", default=DEFAULT_CHROME_APP, help="Chrome app name for AppleScript.")
    parser.add_argument("--continue-on-error", action="store_true", help="Skip failed pages and continue the batch.")
    return parser.parse_args()


def extract_threads(chrome_app: str, subreddit: str, search_term: str) -> list[dict]:
    javascript = f"""
(() => {{
  const norm = (value) => (value || '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
  const skipLine = (line) => {{
    const text = norm(line).toLowerCase();
    if (!text) return true;
    if (/^r\\//.test(text)) return true;
    if (/^u\\//.test(text)) return true;
    if (/^[0-9]+\\s+(comments?|comment)$/.test(text)) return true;
    if (/^[0-9]+\\s+(upvotes?|votes?)$/.test(text)) return true;
    if (/^(share|save|hide|report)$/.test(text)) return true;
    if (/(ago|day|hour|minute|second|month|year)s?$/.test(text)) return true;
    return false;
  }};

  const toInt = (value) => {{
    const digits = String(value || '').replace(/[^0-9]/g, '');
    return digits ? parseInt(digits, 10) : 0;
  }};

  const findCard = (anchor) => {{
    let current = anchor;
    for (let depth = 0; depth < 8 && current; depth += 1) {{
      const raw = current.innerText || current.textContent || '';
      if (raw.includes('comments') || raw.includes('comment')) return current;
      current = current.parentElement;
    }}
    return anchor.closest('article') || anchor.parentElement || anchor;
  }};

  const titleFromCard = (anchor, card) => {{
    const selectors = ['h1', 'h2', 'h3', '[slot="title"]'];
    for (const selector of selectors) {{
      const element = card.querySelector(selector);
      const text = norm(element && (element.innerText || element.textContent));
      if (text.length >= 12) return text;
    }}
    const anchorText = norm(anchor.innerText || anchor.textContent);
    if (anchorText.length >= 12) return anchorText;
    const lines = (card.innerText || card.textContent || '').split('\\n').map(norm).filter((line) => line && !skipLine(line));
    for (const line of lines) {{
      if (line.length >= 12) return line;
    }}
    return '';
  }};

  const bodyFromCard = (card, title) => {{
    const lines = (card.innerText || card.textContent || '')
      .split('\\n')
      .map(norm)
      .filter((line) => line && !skipLine(line) && line !== title);
    return lines.slice(0, 3).join(' ');
  }};

  const getDatetime = (card) => {{
    const timeEl = card.querySelector('time');
    return timeEl ? (timeEl.getAttribute('datetime') || '') : '';
  }};

  const getStat = (rawText, regex) => {{
    const match = rawText.match(regex);
    return match ? toInt(match[1]) : 0;
  }};

  const anchors = Array.from(document.querySelectorAll('a[href*="/comments/"]'));
  const seen = new Set();
  const posts = [];

  for (const anchor of anchors) {{
    const href = anchor.getAttribute('href') || '';
    const absoluteUrl = href.startsWith('http') ? href : new URL(href, location.origin).href;
    if (!/\\/r\\/[^/]+\\/comments\\//.test(absoluteUrl)) continue;
    const canonical = absoluteUrl.split('?')[0];
    if (seen.has(canonical)) continue;
    seen.add(canonical);

    const card = findCard(anchor);
    const rawText = card.innerText || card.textContent || '';
    const title = titleFromCard(anchor, card);
    if (!title) continue;

    posts.push({{
      subreddit: {json.dumps(subreddit)},
      search_term: {json.dumps(search_term)},
      title,
      body: bodyFromCard(card, title),
      author: '',
      url: canonical,
      created_utc: getDatetime(card),
      score: getStat(rawText, /([0-9.,kK]+)\\s+(?:upvotes?|votes?)/i),
      num_comments: getStat(rawText, /([0-9.,kK]+)\\s+comments?/i),
      source_endpoint: location.href,
      discovery_stage: 'search_result'
    }});
  }}

  return JSON.stringify({{
    pageTitle: document.title,
    blocked: document.body && /blocked by network security/i.test(document.body.innerText || ''),
    count: posts.length,
    posts
  }});
}})();
"""

    output = execute_js(chrome_app, javascript)
    if not output:
        return []
    payload = json.loads(output)
    if payload.get("blocked"):
        raise RuntimeError("Chrome loaded a Reddit network security blocked page.")
    return payload.get("posts", [])


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    browser_wait = float(config.get("browser_wait_seconds", 6))
    scroll_rounds = int(config.get("browser_scroll_rounds", 2))
    scroll_delay = float(config.get("browser_scroll_delay_seconds", 1.5))
    per_page_delay = float(config.get("browser_between_pages_seconds", 1.0))

    ensure_chrome_window(args.chrome_app)

    tasks = [(subreddit, term) for subreddit in config["subreddits"] for term in config["search_terms"]]
    discovered: list[dict] = []
    failures: list[str] = []

    for index, (subreddit, term) in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] discover r/{subreddit} -> {term}", flush=True)
        try:
            url = build_search_url(
                subreddit=subreddit,
                term=term,
                listing_sort=config.get("listing_sort", "new"),
                time_filter=config.get("time_filter", "month"),
            )
            open_url_in_chrome(args.chrome_app, url)
            wait_for_ready(args.chrome_app, browser_wait)
            scroll_page(args.chrome_app, scroll_rounds, scroll_delay)
            time.sleep(per_page_delay)
            page_threads = extract_threads(args.chrome_app, subreddit, term)
            discovered.extend(page_threads)
            print(f"  discovered {len(page_threads)} threads", flush=True)
            write_jsonl(Path(args.output), dedupe_by_url(discovered))
        except Exception as error:
            message = f"r/{subreddit} -> {term}: {error}"
            failures.append(message)
            print(f"  failed: {message}", file=sys.stderr, flush=True)
            if not args.continue_on_error:
                raise

    deduped = dedupe_by_url(discovered)
    write_jsonl(Path(args.output), deduped)
    print(f"Discovered {len(deduped)} unique threads")
    print(f"Output: {args.output}")
    if failures:
        print("Failed pages:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Thread discovery failed: {error}", file=sys.stderr)
        raise
