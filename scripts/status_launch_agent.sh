#!/bin/bash
set -euo pipefail

LABEL="com.fishgoo.demand-intelligence"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"
SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_WINDOW_SECONDS=900

WORKING_DIR=""
STDOUT_LOG="$ROOT_DIR/data/runtime/logs/launchd.stdout.log"
STDERR_LOG="$ROOT_DIR/data/runtime/logs/launchd.stderr.log"

if [[ -f "$PLIST_PATH" && -x /usr/libexec/PlistBuddy ]]; then
  WORKING_DIR="$(/usr/libexec/PlistBuddy -c 'Print :WorkingDirectory' "$PLIST_PATH" 2>/dev/null || true)"
  STDOUT_LOG="$(/usr/libexec/PlistBuddy -c 'Print :StandardOutPath' "$PLIST_PATH" 2>/dev/null || printf '%s' "$STDOUT_LOG")"
  STDERR_LOG="$(/usr/libexec/PlistBuddy -c 'Print :StandardErrorPath' "$PLIST_PATH" 2>/dev/null || printf '%s' "$STDERR_LOG")"
fi

launchctl_value() {
  local output="$1"
  local key="$2"
  printf '%s\n' "$output" | /usr/bin/awk -F'= ' -v pattern="$key" '$0 ~ pattern {print $2; exit}'
}

log_age_seconds() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    printf '%s' ""
    return 0
  fi
  local modified
  modified="$(/usr/bin/stat -f '%m' "$path" 2>/dev/null || true)"
  if [[ -z "$modified" ]]; then
    printf '%s' ""
    return 0
  fi
  local now
  now="$(/bin/date +%s)"
  printf '%s' "$((now - modified))"
}

show_recent_log() {
  local label="$1"
  local path="$2"
  local age
  age="$(log_age_seconds "$path")"

  echo
  echo "$label:"
  if [[ ! -f "$path" ]]; then
    echo "log missing"
    return 0
  fi
  if [[ -z "$age" ]]; then
    echo "unable to read log mtime"
    return 0
  fi
  if (( age > LOG_WINDOW_SECONDS )); then
    echo "no new log lines in the last 15 minutes"
    return 0
  fi
  /usr/bin/tail -n 20 "$path" 2>/dev/null | /usr/bin/awk 'NF'
}

echo "Label: $LABEL"
echo "Plist: $PLIST_PATH"
if [[ -n "$WORKING_DIR" ]]; then
  echo "Runtime root: $WORKING_DIR"
fi
echo "Stdout log: $STDOUT_LOG"
echo "Stderr log: $STDERR_LOG"
echo

if [[ -f "$PLIST_PATH" ]]; then
  echo "LaunchAgent plist: present"
else
  echo "LaunchAgent plist: missing"
fi

LAUNCHCTL_OUTPUT="$(/bin/launchctl print "gui/$UID_VALUE/$LABEL" 2>/dev/null || true)"

echo
echo "LaunchAgent summary:"
if [[ -z "$LAUNCHCTL_OUTPUT" ]]; then
  echo "not loaded"
else
  echo "state: $(launchctl_value "$LAUNCHCTL_OUTPUT" 'state = ')"
  echo "pid: $(launchctl_value "$LAUNCHCTL_OUTPUT" 'pid = ')"
  echo "runs: $(launchctl_value "$LAUNCHCTL_OUTPUT" 'runs = ')"
  echo "last exit code: $(launchctl_value "$LAUNCHCTL_OUTPUT" 'last exit code = ')"
fi

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
HEALTH_PAYLOAD="$(/usr/bin/curl -s --max-time 4 "http://127.0.0.1:8765/api/health" 2>/dev/null || true)"
if [[ -n "$HEALTH_PAYLOAD" ]]; then
  /usr/bin/python3 -c '
import json, sys
payload = json.loads(sys.argv[1])
print("status: {}".format("ok" if payload.get("ok") else "degraded"))
print("server_root: {}".format(payload.get("server_root", "-")))
' "$HEALTH_PAYLOAD"
elif [[ -n "$LISTENER_OUTPUT" ]]; then
  echo "listener is active on 127.0.0.1:8765; HTTP probe failed from current shell."
else
  echo "HTTP probe failed from current shell; check listener status above and logs below."
fi

show_recent_log "Recent stdout" "$STDOUT_LOG"
show_recent_log "Recent actionable stderr" "$STDERR_LOG"
