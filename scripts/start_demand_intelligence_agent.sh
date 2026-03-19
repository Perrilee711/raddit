#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/runtime/logs"
STATE_DIR="$ROOT_DIR/data/runtime/state"

/bin/mkdir -p "$LOG_DIR" "$STATE_DIR"

HOST="${DEMAND_INTEL_HOST:-127.0.0.1}"
PORT="${DEMAND_INTEL_PORT:-8765}"

pick_input() {
  local explicit="${DEMAND_INTEL_INPUT:-}"
  if [[ -n "$explicit" && -f "$explicit" ]]; then
    printf '%s\n' "$explicit"
    return 0
  fi

  local candidates=(
    "/Users/perrilee/raddit/data/raw/fishgoo_dropshipping_expanded.jsonl"
    "$ROOT_DIR/data/examples/reddit_posts_demo.jsonl"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  printf '%s\n' "$ROOT_DIR/data/examples/reddit_posts_demo.jsonl"
}

INPUT_PATH="$(pick_input)"

{
  echo "[$(/bin/date '+%Y-%m-%d %H:%M:%S')] starting demand intelligence server"
  echo "root=$ROOT_DIR"
  echo "input=$INPUT_PATH"
  echo "host=$HOST port=$PORT"
} >> "$LOG_DIR/launcher.log"

exec /usr/bin/python3 "$ROOT_DIR/scripts/demand_intelligence_server.py" \
  --host "$HOST" \
  --port "$PORT" \
  --input "$INPUT_PATH"
