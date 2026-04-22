#!/bin/bash
# Fishgoo Ad Board publish + self-check
#
# This script is called by scripts/run_fishgoo_daily_refresh.py after the
# board HTML is regenerated. It copies the fresh HTML into nginx's serving
# directory, then runs a 3-step self-check to catch the class of failures
# we hit on 2026-04-22 (nginx config was silently rewritten without the
# /ad-board/ location block, resulting in public 404).
#
# Self-checks:
#   1. Destination file exists and has reasonable size (>10KB)
#   2. nginx config test passes
#   3. Public URL returns 401 (auth required · healthy) or 200
#
# On failure: exits non-zero so systemd marks the service failed,
# which lets us discover it via `systemctl status` or journalctl.

set -euo pipefail

BOARD_DIR=/var/www/fishgoo-ad-board
REPO=/root/raddit
GENERATED_BOARD="$REPO/data/fishgoo_generated/board/fishgoo-ad-board.html"
SOURCE_BOARD="$REPO/fishgoo-ad-board.html"
PUBLIC_URL="https://mcp.perrilee.com/ad-board/"
HEALTH_LOG=/var/log/fishgoo-publish-health.log
MIN_SIZE_BYTES=10000  # 10KB · below this = almost certainly an empty/broken file

# ---------- Publish ----------

if [[ -f "$GENERATED_BOARD" ]]; then
  cp "$GENERATED_BOARD" "$BOARD_DIR/index.html"
else
  cp "$SOURCE_BOARD" "$BOARD_DIR/index.html"
fi

cp "$REPO/FISHGOO_广告成长档案/05_30天广告成长看板/FISHGOO_广告负责人看板_V2_2026-03-30.html" "$BOARD_DIR/v2.html"
cp "$REPO/FISHGOO_广告成长档案/05_30天广告成长看板/FISHGOO_广告负责人看板_V3_2026-03-30.html" "$BOARD_DIR/v3.html"
chown nginx:nginx "$BOARD_DIR"/*.html
chmod 644 "$BOARD_DIR"/*.html
echo "Board refreshed at $(date '+%Y-%m-%d %H:%M:%S')"

# ---------- Self-check ----------

timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

_log_health() {
  # $1 = OK|FAIL  $2 = detail
  echo "$timestamp $1 $2" >> "$HEALTH_LOG" 2>/dev/null || true
}

# Check 1: destination file sane
if [[ ! -f "$BOARD_DIR/index.html" ]]; then
  echo "❌ SELF-CHECK FAIL: $BOARD_DIR/index.html missing after publish" >&2
  _log_health "FAIL" "file_missing"
  exit 1
fi

file_size=$(stat -c%s "$BOARD_DIR/index.html" 2>/dev/null || stat -f%z "$BOARD_DIR/index.html")
if [[ "$file_size" -lt "$MIN_SIZE_BYTES" ]]; then
  echo "❌ SELF-CHECK FAIL: $BOARD_DIR/index.html only $file_size bytes (expected >$MIN_SIZE_BYTES)" >&2
  _log_health "FAIL" "file_too_small_${file_size}"
  exit 1
fi

# Check 2: nginx config still has /ad-board/ location (defense against what
# happened 2026-04-22 when someone rewrote nginx config and dropped it)
if ! grep -q "location /ad-board/" /etc/nginx/conf.d/*.conf 2>/dev/null; then
  echo "❌ SELF-CHECK FAIL: no /ad-board/ location in nginx config · someone deleted it" >&2
  _log_health "FAIL" "nginx_config_missing_location"
  exit 1
fi

# Check 3: public URL self-check (401 = auth required · healthy; 200 = no auth · also healthy)
http_status=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 "$PUBLIC_URL" 2>/dev/null || echo "000")

case "$http_status" in
  401|200)
    echo "✅ ad-board self-check passed (HTTP $http_status · file $file_size bytes)"
    _log_health "OK" "http_${http_status}_size_${file_size}"
    ;;
  *)
    echo "❌ SELF-CHECK FAIL: public URL returned HTTP $http_status (expected 401 or 200)" >&2
    echo "   URL: $PUBLIC_URL" >&2
    echo "   File: $BOARD_DIR/index.html ($file_size bytes)" >&2
    _log_health "FAIL" "http_${http_status}"
    exit 1
    ;;
esac
