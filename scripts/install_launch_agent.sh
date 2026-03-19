#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$SOURCE_ROOT"
LABEL="com.fishgoo.demand-intelligence"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
UID_VALUE="$(/usr/bin/id -u)"
SERVICE_ROOT="$HOME/raddit-service"

sync_runtime_root() {
  /bin/mkdir -p "$SERVICE_ROOT"

  /usr/bin/rsync -a --delete \
    --exclude '.git' \
    --exclude '.DS_Store' \
    --exclude 'data/studies/' \
    --exclude 'data/runtime/logs/' \
    --exclude 'data/runtime/state/' \
    --exclude 'data/jobs/' \
    --exclude 'data/entities/studies/' \
    --exclude 'docs/product/data/studies/' \
    "$SOURCE_ROOT/" "$SERVICE_ROOT/"
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
    <string>$ROOT_DIR/scripts/start_demand_intelligence_agent.sh</string>
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
    <key>DEMAND_INTEL_HOST</key>
    <string>127.0.0.1</string>
    <key>DEMAND_INTEL_PORT</key>
    <string>8765</string>
  </dict>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/launchd.stdout.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/launchd.stderr.log</string>
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
echo "Logs:  $LOG_DIR"
echo "Health: http://127.0.0.1:8765/"
