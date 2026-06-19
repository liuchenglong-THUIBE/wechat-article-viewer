#!/usr/bin/env bash
set -Eeuo pipefail

# Copy this file to scripts/daily_update.sh and replace all placeholders.
# Keep the copied file local if it contains machine-specific paths.

PROJECT_DIR="__PROJECT_DIR__"
PYTHON_BIN="__PYTHON_BIN__"
DAYS="__DAYS__"
LOG_DIR="$PROJECT_DIR/logs"
LOCK_DIR="$PROJECT_DIR/.daily-update.lock"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily update is already running, skip"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR/src"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily update started"
"$PYTHON_BIN" -m wechat_reader weekly-update --days "$DAYS"
"$PYTHON_BIN" -m wechat_reader export --sync
echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily update finished"
