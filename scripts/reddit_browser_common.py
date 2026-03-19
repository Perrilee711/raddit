#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from urllib.parse import quote


DEFAULT_CHROME_APP = "Google Chrome"


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_osascript(lines: list[str]) -> str:
    command = ["/usr/bin/osascript"]
    wrapped_lines = ["with timeout of 120 seconds"] + lines + ["end timeout"]
    for line in wrapped_lines:
        command.extend(["-e", line])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "osascript command failed")
    return result.stdout.strip()


def applescript_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


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


def build_search_url(subreddit: str, term: str, listing_sort: str, time_filter: str) -> str:
    return (
        f"https://www.reddit.com/r/{subreddit}/search/"
        f"?q={quote(term)}&restrict_sr=1&sort={quote(listing_sort)}&t={quote(time_filter)}"
    )


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def dedupe_by_url(rows: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for row in rows:
        key = row.get("url") or row.get("title")
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = row
            continue
        current_term = str(existing.get("search_term", "")).strip()
        incoming_term = str(row.get("search_term", "")).strip()
        if incoming_term and incoming_term not in current_term.split(" | "):
            existing["search_term"] = " | ".join([part for part in [current_term, incoming_term] if part])
        for numeric in ["num_comments", "score"]:
            try:
                existing[numeric] = max(int(existing.get(numeric, 0)), int(row.get(numeric, 0)))
            except (TypeError, ValueError):
                pass
    return list(deduped.values())
