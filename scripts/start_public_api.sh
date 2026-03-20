#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

HOST="${DEMAND_INTEL_HOST:-0.0.0.0}"
PORT="${DEMAND_INTEL_PORT:-8765}"
DEFAULT_INPUT="$PROJECT_ROOT/data/raw/studies/fishgoo-us-dropshipping.jsonl"
FALLBACK_INPUT="$PROJECT_ROOT/data/examples/reddit_posts_demo.jsonl"
INPUT_PATH="${DEMAND_INTEL_INPUT:-$DEFAULT_INPUT}"
CORS_ORIGINS="${DEMAND_INTEL_CORS_ORIGINS:-https://skill-deploy-jr9bh4v87v.vercel.app}"

if [ ! -f "$INPUT_PATH" ]; then
  INPUT_PATH="$FALLBACK_INPUT"
fi

cd "$PROJECT_ROOT"

exec /usr/bin/python3 "$PROJECT_ROOT/scripts/demand_intelligence_server.py" \
  --host "$HOST" \
  --port "$PORT" \
  --input "$INPUT_PATH" \
  --cors-origins "$CORS_ORIGINS" \
  --cookie-secure
