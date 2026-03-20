#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/runtime/logs"

/bin/mkdir -p "$LOG_DIR"

API_BASE_URL="${DEMAND_INTEL_API_BASE_URL:-http://43.162.90.26}"
WORKER_TOKEN="${DEMAND_INTEL_WORKER_TOKEN:-fishgoo-mac-worker-token}"
WORKER_ID="${DEMAND_INTEL_WORKER_ID:-fishgoo-mac-worker}"
WORKER_NAME="${DEMAND_INTEL_WORKER_NAME:-$(/bin/hostname -s 2>/dev/null || /bin/hostname)}"
CHROME_APP="${DEMAND_INTEL_CHROME_APP:-Google Chrome}"

{
  echo "[$(/bin/date '+%Y-%m-%d %H:%M:%S')] starting mac worker agent"
  echo "root=$ROOT_DIR"
  echo "api=$API_BASE_URL"
  echo "worker_id=$WORKER_ID"
  echo "worker_name=$WORKER_NAME"
  echo "chrome_app=$CHROME_APP"
} >> "$LOG_DIR/mac_worker.launcher.log"

exec /usr/bin/python3 "$ROOT_DIR/scripts/mac_worker_agent.py" \
  --api-base-url "$API_BASE_URL" \
  --worker-token "$WORKER_TOKEN" \
  --worker-id "$WORKER_ID" \
  --worker-name "$WORKER_NAME" \
  --chrome-app "$CHROME_APP" \
  --continue-on-error
