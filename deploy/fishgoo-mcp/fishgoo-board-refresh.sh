#!/bin/bash
set -euo pipefail

BOARD_DIR=/var/www/fishgoo-ad-board
REPO=/root/raddit
GENERATED_BOARD="$REPO/data/fishgoo_generated/board/fishgoo-ad-board.html"
SOURCE_BOARD="$REPO/fishgoo-ad-board.html"

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
