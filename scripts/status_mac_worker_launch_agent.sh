#!/bin/bash
set -euo pipefail

LABEL="com.fishgoo.demand-intelligence.mac-worker"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"
LOG_WINDOW_SECONDS=900

WORKING_DIR=""
STDOUT_LOG="$HOME/raddit-service/data/runtime/logs/mac_worker.stdout.log"
STDERR_LOG="$HOME/raddit-service/data/runtime/logs/mac_worker.stderr.log"
LAUNCHER_LOG="$HOME/raddit-service/data/runtime/logs/mac_worker.launcher.log"
API_BASE_URL="http://43.162.90.26"
WORKER_TOKEN=""

if [[ -f "$PLIST_PATH" && -x /usr/libexec/PlistBuddy ]]; then
  WORKING_DIR="$(/usr/libexec/PlistBuddy -c 'Print :WorkingDirectory' "$PLIST_PATH" 2>/dev/null || true)"
  STDOUT_LOG="$(/usr/libexec/PlistBuddy -c 'Print :StandardOutPath' "$PLIST_PATH" 2>/dev/null || printf '%s' "$STDOUT_LOG")"
  STDERR_LOG="$(/usr/libexec/PlistBuddy -c 'Print :StandardErrorPath' "$PLIST_PATH" 2>/dev/null || printf '%s' "$STDERR_LOG")"
  API_BASE_URL="$(/usr/libexec/PlistBuddy -c 'Print :EnvironmentVariables:DEMAND_INTEL_API_BASE_URL' "$PLIST_PATH" 2>/dev/null || printf '%s' "$API_BASE_URL")"
  WORKER_TOKEN="$(/usr/libexec/PlistBuddy -c 'Print :EnvironmentVariables:DEMAND_INTEL_WORKER_TOKEN' "$PLIST_PATH" 2>/dev/null || true)"
  if [[ -n "$WORKING_DIR" ]]; then
    LAUNCHER_LOG="$WORKING_DIR/data/runtime/logs/mac_worker.launcher.log"
  fi
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
echo "API: $API_BASE_URL"
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
echo "Worker health:"
if [[ -n "$WORKER_TOKEN" ]]; then
  HEALTH_PAYLOAD="$(/usr/bin/curl -s --max-time 4 -H "X-Worker-Token: $WORKER_TOKEN" "$API_BASE_URL/api/worker/health" 2>/dev/null || true)"
  if [[ -n "$HEALTH_PAYLOAD" ]]; then
    /usr/bin/python3 -c '
import json, sys
payload = json.loads(sys.argv[1])
worker = payload.get("worker") or {}
running = payload.get("running_job")
print("status: {}".format("ok" if payload.get("ok") else "degraded"))
print("worker: {}".format(worker.get("name") or worker.get("id") or "unknown"))
print("running job: {}".format(running.get("id") if isinstance(running, dict) and running else "idle"))
print("stage: {}".format(running.get("stage_kind") if isinstance(running, dict) and running else "idle"))
' "$HEALTH_PAYLOAD"
  else
    echo "unable to reach worker health endpoint"
  fi
else
  echo "worker token unavailable in LaunchAgent environment"
fi

show_recent_log "Recent launcher log" "$LAUNCHER_LOG"
show_recent_log "Recent actionable stderr" "$STDERR_LOG"
