#!/bin/bash
set -euo pipefail

LABEL="com.fishgoo.demand-intelligence"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"
SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/runtime/logs"
WORKING_DIR=""
STDERR_LOG="$LOG_DIR/launchd.stderr.log"

if [[ -f "$PLIST_PATH" && -x /usr/libexec/PlistBuddy ]]; then
  WORKING_DIR="$(/usr/libexec/PlistBuddy -c 'Print :WorkingDirectory' "$PLIST_PATH" 2>/dev/null || true)"
  STDERR_LOG="$(/usr/libexec/PlistBuddy -c 'Print :StandardErrorPath' "$PLIST_PATH" 2>/dev/null || printf '%s' "$STDERR_LOG")"
fi

echo "Label: $LABEL"
echo "Plist: $PLIST_PATH"
if [[ -n "$WORKING_DIR" ]]; then
  echo "Runtime root: $WORKING_DIR"
fi
echo "Stderr log: $STDERR_LOG"
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
echo "Port listener:"
LISTENER_OUTPUT="$(/usr/sbin/lsof -nP -iTCP:8765 -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$LISTENER_OUTPUT" ]]; then
  printf '%s\n' "$LISTENER_OUTPUT"
else
  echo "nothing listening on 8765"
fi

echo
echo "HTTP health:"
if /usr/bin/curl -s "http://127.0.0.1:8765/" >/dev/null 2>&1; then
  echo "server responding on 127.0.0.1:8765"
elif [[ -n "$LISTENER_OUTPUT" ]]; then
  echo "listener is active on 127.0.0.1:8765; HTTP probe failed from current shell."
else
  echo "HTTP probe failed from current shell; check listener status above and logs below."
fi

echo
echo "Recent logs:"
/usr/bin/tail -n 20 "$STDERR_LOG" 2>/dev/null || true
