#!/bin/bash
# AutoFarm 排程腳本 — 由 launchd 呼叫
set -euo pipefail

REPO="${AUTOFARM_DIR:-$HOME/autofarm}"
cd "$REPO"
source .venv/bin/activate

# 載入 .env
set -a
source .env
set +a

# 執行 pipeline + 自動推送到 Notion
python farm.py --run --push-notion >> "$REPO/data/cron.log" 2>&1
