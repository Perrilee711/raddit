#!/bin/bash
set -euo pipefail

LABEL="com.fishgoo.demand-intelligence"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"

/bin/launchctl bootout "gui/$UID_VALUE" "$PLIST_PATH" >/dev/null 2>&1 || true
/bin/rm -f "$PLIST_PATH"

echo "Removed LaunchAgent: $LABEL"
echo "Deleted plist: $PLIST_PATH"
