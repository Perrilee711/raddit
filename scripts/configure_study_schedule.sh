#!/bin/bash
set -euo pipefail

HOST="${DEMAND_INTEL_HOST:-127.0.0.1}"
PORT="${DEMAND_INTEL_PORT:-8765}"
BASE_URL="http://$HOST:$PORT"
COOKIE_JAR="${TMPDIR:-/tmp}/demand-intel.cookie"

STUDY_ID="${1:-fishgoo-us-dropshipping}"
INTERVAL_HOURS="${2:-24}"
MODE="${3:-adaptive}"
START_NOW="${4:-true}"

EMAIL="${DEMAND_INTEL_ADMIN_EMAIL:-admin@local}"
PASSWORD="${DEMAND_INTEL_ADMIN_PASSWORD:-admin123}"

/usr/bin/curl -s -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  -c "$COOKIE_JAR" >/dev/null

/usr/bin/curl -s -X POST "$BASE_URL/api/studies/$STUDY_ID/schedule" \
  -H 'Content-Type: application/json' \
  -b "$COOKIE_JAR" \
  -d "{\"enabled\":true,\"mode\":\"$MODE\",\"interval_hours\":$INTERVAL_HOURS,\"start_now\":$START_NOW}"

echo
echo "Configured schedule:"
echo "study=$STUDY_ID mode=$MODE interval_hours=$INTERVAL_HOURS start_now=$START_NOW"
