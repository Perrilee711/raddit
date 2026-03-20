#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$SOURCE_ROOT"
LABEL="com.fishgoo.demand-intelligence.mac-worker"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"
SERVICE_ROOT="$HOME/raddit-service"

copy_tree() {
  local relative_path="$1"
  if [[ ! -e "$SOURCE_ROOT/$relative_path" ]]; then
    return
  fi
  /bin/mkdir -p "$(/usr/bin/dirname "$SERVICE_ROOT/$relative_path")"
  /bin/rm -rf "$SERVICE_ROOT/$relative_path"
  /bin/mkdir -p "$SERVICE_ROOT/$relative_path"
  /bin/cp -R "$SOURCE_ROOT/$relative_path/." "$SERVICE_ROOT/$relative_path"
}

bootstrap_tree_if_missing() {
  local relative_path="$1"
  if [[ -e "$SERVICE_ROOT/$relative_path" || ! -e "$SOURCE_ROOT/$relative_path" ]]; then
    return
  fi
  /bin/mkdir -p "$(/usr/bin/dirname "$SERVICE_ROOT/$relative_path")"
  /bin/mkdir -p "$SERVICE_ROOT/$relative_path"
  /bin/cp -R "$SOURCE_ROOT/$relative_path/." "$SERVICE_ROOT/$relative_path"
}

copy_file() {
  local relative_path="$1"
  if [[ ! -f "$SOURCE_ROOT/$relative_path" ]]; then
    return
  fi
  /bin/mkdir -p "$(/usr/bin/dirname "$SERVICE_ROOT/$relative_path")"
  /bin/cp "$SOURCE_ROOT/$relative_path" "$SERVICE_ROOT/$relative_path"
}

sync_runtime_root() {
  /bin/mkdir -p "$SERVICE_ROOT"
  copy_tree "scripts"
  copy_tree "config"
  copy_tree "docs/product"
  copy_tree "deploy"
  copy_file "README.md"
  bootstrap_tree_if_missing "data/studies"
  bootstrap_tree_if_missing "data/entities/studies"
  bootstrap_tree_if_missing "data/raw/studies"
  /bin/mkdir -p "$SERVICE_ROOT/data/runtime/logs" "$SERVICE_ROOT/data/runtime/state"
}

if [[ "$SOURCE_ROOT" == "$HOME/Desktop/"* || "$SOURCE_ROOT" == *"/Desktop/"* ]]; then
  echo "Detected Desktop-based workspace; installing runtime copy into: $SERVICE_ROOT"
  sync_runtime_root
  ROOT_DIR="$SERVICE_ROOT"
fi

LOG_DIR="$ROOT_DIR/data/runtime/logs"
/bin/mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR"

/bin/cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$ROOT_DIR/scripts/start_mac_worker_agent.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$ROOT_DIR</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>ThrottleInterval</key>
  <integer>10</integer>

  <key>LimitLoadToSessionType</key>
  <array>
    <string>Aqua</string>
  </array>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
    <key>DEMAND_INTEL_API_BASE_URL</key>
    <string>${DEMAND_INTEL_API_BASE_URL:-http://43.162.90.26}</string>
    <key>DEMAND_INTEL_WORKER_TOKEN</key>
    <string>${DEMAND_INTEL_WORKER_TOKEN:-fishgoo-mac-worker-token}</string>
    <key>DEMAND_INTEL_WORKER_ID</key>
    <string>${DEMAND_INTEL_WORKER_ID:-fishgoo-mac-worker}</string>
    <key>DEMAND_INTEL_WORKER_NAME</key>
    <string>${DEMAND_INTEL_WORKER_NAME:-$(/bin/hostname -s 2>/dev/null || /bin/hostname)}</string>
    <key>DEMAND_INTEL_CHROME_APP</key>
    <string>${DEMAND_INTEL_CHROME_APP:-Google Chrome}</string>
  </dict>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/mac_worker.stdout.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/mac_worker.stderr.log</string>
</dict>
</plist>
PLIST

/usr/bin/plutil -lint "$PLIST_PATH" >/dev/null
/bin/launchctl bootout "gui/$UID_VALUE" "$PLIST_PATH" >/dev/null 2>&1 || true
/bin/launchctl bootstrap "gui/$UID_VALUE" "$PLIST_PATH"
/bin/launchctl kickstart -k "gui/$UID_VALUE/$LABEL"

echo "Installed LaunchAgent: $LABEL"
echo "Plist: $PLIST_PATH"
echo "Runtime root: $ROOT_DIR"
echo "Logs: $LOG_DIR"
echo "API: ${DEMAND_INTEL_API_BASE_URL:-http://43.162.90.26}"
