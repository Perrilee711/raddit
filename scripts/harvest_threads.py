#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from reddit_browser_common import (
    DEFAULT_CHROME_APP,
    ensure_chrome_window,
    execute_js,
    open_url_in_chrome,
    scroll_page,
    wait_for_ready,
    write_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Harvest Reddit thread detail pages and top comments using the local Chrome session."
    )
    parser.add_argument("--input", required=True, help="Path to discovered thread JSONL.")
    parser.add_argument("--output", required=True, help="Path to save enriched thread JSONL.")
    parser.add_argument("--chrome-app", default=DEFAULT_CHROME_APP, help="Chrome app name for AppleScript.")
    parser.add_argument("--max-comments", type=int, default=40, help="Maximum comments to extract per thread.")
    parser.add_argument("--expand-rounds", type=int, default=2, help="How many rounds to click comment expansion buttons.")
    parser.add_argument("--scroll-rounds", type=int, default=3, help="How many scroll passes to run per thread.")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between expansion/scroll actions.")
    parser.add_argument("--browser-wait", type=float, default=15.0, help="How long to wait for a thread page to render.")
    parser.add_argument("--continue-on-error", action="store_true", help="Skip failed threads and continue.")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def expand_comment_controls(chrome_app: str, rounds: int, delay_seconds: float) -> None:
    javascript = """
(() => {
  const labels = [/more replies/i, /view more comments/i, /load more comments/i, /continue this thread/i, /more comments/i, /see more/i];
  let clicks = 0;
  const buttons = Array.from(document.querySelectorAll('button, a[role="button"]'));
  for (const button of buttons) {
    const text = (button.innerText || button.textContent || '').trim();
    if (!text) continue;
    if (!labels.some((pattern) => pattern.test(text))) continue;
    try {
      button.click();
      clicks += 1;
    } catch (error) {}
  }
  return String(clicks);
})();
""".strip()

    for _ in range(rounds):
        try:
            execute_js(chrome_app, javascript)
        except RuntimeError as error:
            if "-1712" in str(error):
                return
            raise
        time.sleep(delay_seconds)


def extract_thread_payload(chrome_app: str, seed: dict, max_comments: int) -> dict:
    javascript = f"""
(() => {{
  const norm = (value) => (value || '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
  const toInt = (value) => {{
    const text = String(value || '').trim();
    if (!text) return 0;
    const normalized = text.toLowerCase().replace(/,/g, '');
    if (/^[0-9]+(\\.[0-9]+)?k$/.test(normalized)) return Math.round(parseFloat(normalized) * 1000);
    const digits = normalized.replace(/[^0-9.]/g, '');
    return digits ? Math.round(parseFloat(digits)) : 0;
  }};
  const firstText = (selectors, root=document) => {{
    for (const selector of selectors) {{
      const node = root.querySelector(selector);
      const text = norm(node && (node.innerText || node.textContent));
      if (text) return text;
    }}
    return '';
  }};
  const collectParagraphText = (root) => {{
    if (!root) return '';
    const nodes = Array.from(root.querySelectorAll('p, div[slot="text-body"], div[data-post-click-location="text-body"]'));
    const text = nodes.map((node) => norm(node.innerText || node.textContent)).filter(Boolean).join(' ');
    return norm(text);
  }};
  const firstTime = () => {{
    const node = document.querySelector('time');
    return node ? (node.getAttribute('datetime') || '') : '';
  }};
  const mainPostRoot = () => {{
    return document.querySelector('shreddit-post, faceplate-tracker[noun="post"], article, main');
  }};
  const extractComments = () => {{
    const selectors = ['shreddit-comment', 'faceplate-comment', '[data-testid="comment"]', '[id^="t1_"]'];
    const nodes = [];
    const seen = new Set();
    for (const selector of selectors) {{
      for (const node of document.querySelectorAll(selector)) {{
        if (!(node instanceof Element)) continue;
        const key =
          node.getAttribute('thingid') ||
          node.getAttribute('id') ||
          node.getAttribute('data-testid') ||
          norm((node.innerText || node.textContent || '').slice(0, 160));
        if (!key || seen.has(key)) continue;
        seen.add(key);
        nodes.push(node);
      }}
    }}

    const comments = [];
    for (const node of nodes) {{
      const raw = norm(node.innerText || node.textContent);
      if (!raw) continue;
      const body = firstText(
        [
          '[slot="comment"]',
          '[slot="comment-content"]',
          '[data-testid="comment-content"]',
          '.md',
          '.usertext-body',
          'p',
        ],
        node
      ) || collectParagraphText(node);
      if (!body) continue;

      const author =
        firstText(['a[href*="/user/"]', 'a[href*="/u/"]', '[slot="authorName"]', 'faceplate-author-link'], node) ||
        '';
      const permalinkNode = node.querySelector('a[href*="/comments/"]');
      const permalink = permalinkNode ? permalinkNode.href : '';
      const timeNode = node.querySelector('time');
      const scoreMatch = raw.match(/([0-9.,kK]+)\\s+(?:upvotes?|votes?|points?)/i);
      const depthAttr =
        node.getAttribute('depth') ||
        node.getAttribute('data-depth') ||
        node.getAttribute('comment-depth') ||
        '0';

      comments.push({{
        id: node.getAttribute('thingid') || node.getAttribute('id') || '',
        author: author.replace(/^u\\//i, ''),
        body,
        permalink,
        created_utc: timeNode ? (timeNode.getAttribute('datetime') || '') : '',
        score: scoreMatch ? toInt(scoreMatch[1]) : 0,
        depth: toInt(depthAttr),
        is_op_reply: /op/i.test(raw),
      }});
      if (comments.length >= {max_comments}) break;
    }}
    return comments;
  }};

  const postRoot = mainPostRoot();
  const fullText = norm(document.body && (document.body.innerText || document.body.textContent || ''));
  const scoreMatch = fullText.match(/([0-9.,kK]+)\\s+(?:upvotes?|votes?|points?)/i);
  const commentsMatch = fullText.match(/([0-9.,kK]+)\\s+comments?/i);
  const body =
    collectParagraphText(postRoot) ||
    firstText(['[slot="text-body"]', 'div[data-post-click-location="text-body"]', '.usertext-body', 'article p'], postRoot || document) ||
    {json.dumps(str(seed.get("body", "")))};
  const title =
    firstText(['h1', 'h2', 'shreddit-title'], postRoot || document) ||
    {json.dumps(str(seed.get("title", "")))};
  const author =
    firstText(['a[href*="/user/"]', 'a[href*="/u/"]', '[slot="authorName"]', 'faceplate-author-link'], postRoot || document) ||
    {json.dumps(str(seed.get("author", "")))};

  return JSON.stringify({{
    title,
    body,
    author: author.replace(/^u\\//i, ''),
    created_utc: firstTime() || {json.dumps(str(seed.get("created_utc", "")))},
    score: scoreMatch ? toInt(scoreMatch[1]) : {int(seed.get("score", 0) or 0)},
    num_comments: commentsMatch ? toInt(commentsMatch[1]) : {int(seed.get("num_comments", 0) or 0)},
    blocked: /blocked by network security/i.test(fullText),
    comments: extractComments(),
    source_endpoint: location.href
  }});
}})();
"""

    output = execute_js(chrome_app, javascript)
    if not output:
        return dict(seed)
    payload = json.loads(output)
    if payload.get("blocked"):
        raise RuntimeError("Chrome loaded a Reddit network security blocked page.")
    enriched = dict(seed)
    enriched.update(payload)
    enriched["discovery_stage"] = "thread_harvested"
    enriched["harvested_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return enriched


def main() -> None:
    args = parse_args()
    discovered = read_jsonl(Path(args.input))
    ensure_chrome_window(args.chrome_app)

    harvested: list[dict] = []
    failures: list[str] = []
    for index, seed in enumerate(discovered, start=1):
        title = seed.get("title", "untitled")
        url = seed.get("url")
        print(f"[{index}/{len(discovered)}] harvest {title[:80]}", flush=True)
        if not url:
            continue
        try:
            open_url_in_chrome(args.chrome_app, url)
            wait_for_ready(args.chrome_app, args.browser_wait)
            expand_comment_controls(args.chrome_app, args.expand_rounds, args.delay_seconds)
            scroll_page(args.chrome_app, args.scroll_rounds, args.delay_seconds)
            time.sleep(args.delay_seconds)
            enriched = extract_thread_payload(args.chrome_app, seed, args.max_comments)
            harvested.append(enriched)
            write_jsonl(Path(args.output), harvested)
            print(f"  comments captured: {len(enriched.get('comments', []))}", flush=True)
        except Exception as error:
            message = f"{url}: {error}"
            failures.append(message)
            fallback = dict(seed)
            fallback["harvest_error"] = str(error)
            harvested.append(fallback)
            write_jsonl(Path(args.output), harvested)
            print(f"  failed: {message}", file=sys.stderr, flush=True)
            if not args.continue_on_error:
                raise

    write_jsonl(Path(args.output), harvested)
    print(f"Harvested {len(harvested)} threads")
    print(f"Output: {args.output}")
    if failures:
        print("Failed threads:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Thread harvest failed: {error}", file=sys.stderr)
        raise
