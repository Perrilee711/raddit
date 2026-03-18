#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from reddit_research_report import generate_report


DEFAULT_CONFIG_PATH = "config/reddit_targets.json"
DEFAULT_CHROME_APP = "Google Chrome"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use the local Chrome session to collect Reddit search results and generate a Markdown report."
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to the target config JSON file.",
    )
    parser.add_argument(
        "--raw-output",
        help="Path to save raw JSONL records. Defaults to data/raw/<timestamp>_reddit_browser_posts.jsonl",
    )
    parser.add_argument(
        "--report-output",
        help="Path to save the Markdown report. Defaults to docs/reports/<timestamp>_reddit-browser-report.md",
    )
    parser.add_argument(
        "--top-leads",
        type=int,
        default=15,
        help="How many high-intent posts to include in the report.",
    )
    parser.add_argument(
        "--chrome-app",
        default=DEFAULT_CHROME_APP,
        help="Chrome app name for AppleScript. Default: Google Chrome",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Skip failed pages and continue the batch instead of aborting.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def default_paths() -> tuple[Path, Path]:
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    return (
        Path("data/raw") / f"{stamp}_reddit_browser_posts.jsonl",
        Path("docs/reports") / f"{stamp}_reddit-browser-report.md",
    )


def run_osascript(lines: list[str]) -> str:
    command = ["/usr/bin/osascript"]
    wrapped_lines = ["with timeout of 120 seconds"] + lines + ["end timeout"]
    for line in wrapped_lines:
        command.extend(["-e", line])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "osascript command failed")
    return result.stdout.strip()


def ensure_chrome_window(chrome_app: str) -> None:
    run_osascript(
        [
            f'tell application "{chrome_app}"',
            "activate",
            "if (count of windows) = 0 then make new window",
            "end tell",
        ]
    )


def open_url_in_chrome(chrome_app: str, url: str) -> None:
    run_osascript(
        [
            f'tell application "{chrome_app}"',
            "activate",
            "if (count of windows) = 0 then make new window",
            "set URL of active tab of front window to " + applescript_string(url),
            "end tell",
        ]
    )


def execute_js(chrome_app: str, javascript: str) -> str:
    run_osascript([f'tell application "{chrome_app}" to activate'])
    last_error: RuntimeError | None = None
    for _ in range(3):
        try:
            return run_osascript(
                [
                    f'tell application "{chrome_app}"',
                    "execute active tab of front window javascript " + applescript_string(javascript),
                    "end tell",
                ]
            )
        except RuntimeError as error:
            last_error = error
            time.sleep(1.0)
    if last_error is None:
        raise RuntimeError("execute_js failed without a captured error")
    raise last_error


def applescript_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def wait_for_ready(chrome_app: str, timeout_seconds: float) -> None:
    start = time.time()
    last_state = ""
    while time.time() - start < timeout_seconds:
        try:
            state = execute_js(chrome_app, "document.readyState")
            last_state = state or last_state
        except RuntimeError:
            time.sleep(0.5)
            continue

        if state == "complete":
            return
        if state == "interactive":
            try:
                body_ready = execute_js(
                    chrome_app,
                    """
(() => {
  const text = (document.body && (document.body.innerText || document.body.textContent || '')) || '';
  return text.trim().length > 0 ? 'ready' : 'empty';
})();
""".strip(),
                )
                if body_ready == "ready":
                    return
            except RuntimeError:
                pass
        time.sleep(0.5)

    try:
        title = execute_js(chrome_app, "document.title || ''")
        body_ready = execute_js(
            chrome_app,
            """
(() => {
  const text = (document.body && (document.body.innerText || document.body.textContent || '')) || '';
  return text.trim().length > 0 ? 'ready' : 'empty';
})();
""".strip(),
        )
        if title.strip() or body_ready == "ready":
            return
    except RuntimeError:
        pass

    raise RuntimeError(
        f"Timed out waiting for Chrome tab to finish loading. Last readyState: {last_state or 'unknown'}"
    )


def build_search_url(subreddit: str, term: str, listing_sort: str, time_filter: str) -> str:
    return (
        f"https://www.reddit.com/r/{subreddit}/search/"
        f"?q={quote(term)}&restrict_sr=1&sort={quote(listing_sort)}&t={quote(time_filter)}"
    )


def scroll_page(chrome_app: str, rounds: int, delay_seconds: float) -> None:
    for _ in range(rounds):
        try:
            execute_js(
                chrome_app,
                """
(() => {
  window.scrollTo(0, document.body.scrollHeight);
  return 'ok';
})();
""".strip(),
            )
        except RuntimeError as error:
            if "-1712" in str(error):
                return
            raise
        time.sleep(delay_seconds)


def extract_posts(chrome_app: str, subreddit: str, search_term: str) -> list[dict]:
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

    const lines = (card.innerText || card.textContent || '')
      .split('\\n')
      .map(norm)
      .filter((line) => line && !skipLine(line));

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
      source_endpoint: location.href
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


def dedupe_posts(posts: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for post in posts:
        key = post.get("url") or post.get("title")
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = post
            continue
        current_term = str(existing.get("search_term", "")).strip()
        incoming_term = str(post.get("search_term", "")).strip()
        if incoming_term and incoming_term not in current_term.split(" | "):
            existing["search_term"] = " | ".join(
                [part for part in [current_term, incoming_term] if part]
            )
        existing["num_comments"] = max(int(existing.get("num_comments", 0)), int(post.get("num_comments", 0)))
        existing["score"] = max(int(existing.get("score", 0)), int(post.get("score", 0)))
    return list(deduped.values())


def write_jsonl(path: Path, posts: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(post, ensure_ascii=False) for post in posts]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def save_progress(raw_output: Path, report_output: Path, posts: list[dict], top_leads: int) -> None:
    deduped = dedupe_posts(posts)
    write_jsonl(raw_output, deduped)
    if deduped:
        generate_report(raw_output, report_output, top_leads)


def print_progress(index: int, total: int, subreddit: str, search_term: str) -> None:
    print(f"[{index}/{total}] r/{subreddit} -> {search_term}", flush=True)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    raw_default, report_default = default_paths()
    raw_output = Path(args.raw_output) if args.raw_output else raw_default
    report_output = Path(args.report_output) if args.report_output else report_default

    browser_wait = float(config.get("browser_wait_seconds", 6))
    scroll_rounds = int(config.get("browser_scroll_rounds", 2))
    scroll_delay = float(config.get("browser_scroll_delay_seconds", 1.5))
    per_page_delay = float(config.get("browser_between_pages_seconds", 1.0))

    ensure_chrome_window(args.chrome_app)

    all_posts: list[dict] = []
    tasks = [
        (subreddit, search_term)
        for subreddit in config["subreddits"]
        for search_term in config["search_terms"]
    ]

    failures: list[str] = []
    for index, (subreddit, search_term) in enumerate(tasks, start=1):
        print_progress(index, len(tasks), subreddit, search_term)
        try:
            url = build_search_url(
                subreddit=subreddit,
                term=search_term,
                listing_sort=config.get("listing_sort", "new"),
                time_filter=config.get("time_filter", "month"),
            )
            open_url_in_chrome(args.chrome_app, url)
            wait_for_ready(args.chrome_app, browser_wait)
            scroll_page(args.chrome_app, scroll_rounds, scroll_delay)
            time.sleep(per_page_delay)
            page_posts = extract_posts(args.chrome_app, subreddit, search_term)
            all_posts.extend(page_posts)
            print(f"  collected {len(page_posts)} posts", flush=True)
            save_progress(raw_output, report_output, all_posts, args.top_leads)
        except Exception as error:
            message = f"r/{subreddit} -> {search_term}: {error}"
            failures.append(message)
            print(f"  failed: {message}", file=sys.stderr, flush=True)
            if not args.continue_on_error:
                raise

    deduped = dedupe_posts(all_posts)
    write_jsonl(raw_output, deduped)
    generate_report(raw_output, report_output, args.top_leads)

    print(f"Fetched {len(deduped)} posts from Chrome session")
    print(f"Raw data: {raw_output}")
    print(f"Report: {report_output}")
    if failures:
        print("Failed pages:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Browser pipeline failed: {error}", file=sys.stderr)
        raise
