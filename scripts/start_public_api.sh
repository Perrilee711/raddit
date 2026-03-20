#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

HOST="${DEMAND_INTEL_HOST:-0.0.0.0}"
PORT="${DEMAND_INTEL_PORT:-8765}"
INPUT_PATH="${DEMAND_INTEL_INPUT:-$PROJECT_ROOT/data/raw/studies/fishgoo-us-dropshipping.jsonl}"
CORS_ORIGINS="${DEMAND_INTEL_CORS_ORIGINS:-https://skill-deploy-jr9bh4v87v.vercel.app}"

cd "$PROJECT_ROOT"

exec /usr/bin/python3 "$PROJECT_ROOT/scripts/demand_intelligence_server.py" \
  --host "$HOST" \
  --port "$PORT" \
  --input "$INPUT_PATH" \
  --cors-origins "$CORS_ORIGINS" \
  --cookie-secure
