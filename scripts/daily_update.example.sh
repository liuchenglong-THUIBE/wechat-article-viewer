#!/usr/bin/env bash
set -Eeuo pipefail

# 将本文件复制为 scripts/daily_update.sh，并替换所有占位符。
# 如果复制后的文件包含本机路径，请只保留在本地，不要提交到 Git。

PROJECT_DIR="__PROJECT_DIR__"
PYTHON_BIN="__PYTHON_BIN__"
DAYS="__DAYS__"
LOG_DIR="$PROJECT_DIR/logs"
LOCK_DIR="$PROJECT_DIR/.daily-update.lock"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 每日更新已在运行，跳过本次执行"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR/src"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 每日更新开始"

# 等待网络连接就绪（最多等待 60 秒）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 正在等待网络连接..."
for i in {1..60}; do
  if ping -c 1 -W 1 mp.weixin.qq.com >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 网络已就绪"
    break
  fi
  sleep 1
done

"$PYTHON_BIN" -m wechat_reader weekly-update --days "$DAYS" --no-login
"$PYTHON_BIN" -m wechat_reader export --sync
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 每日更新完成"
