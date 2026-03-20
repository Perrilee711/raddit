#!/bin/bash
set -euo pipefail

LABEL="com.fishgoo.demand-intelligence.mac-worker"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"
STDERR_LOG="$HOME/raddit-service/data/runtime/logs/mac_worker.stderr.log"

echo "Label: $LABEL"
echo "Plist: $PLIST_PATH"
echo

if [[ -f "$PLIST_PATH" ]]; then
  echo "LaunchAgent plist: present"
else
  echo "LaunchAgent plist: missing"
fi

echo
echo "launchctl print:"
/bin/launchctl print "gui/$UID_VALUE/$LABEL" 2>/dev/null || echo "not loaded"

echo
echo "Recent stderr:"
/usr/bin/tail -n 20 "$STDERR_LOG" 2>/dev/null || true
