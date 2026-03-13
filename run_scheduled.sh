#!/bin/bash
# AutoFarm 排程腳本 — 由 launchd 呼叫
set -euo pipefail

cd /Users/fymn/autofarm
source .venv/bin/activate

# 載入 .env
set -a
source .env
set +a

# 執行 pipeline + 自動推送到 Notion
python farm.py --run --push-notion >> /Users/fymn/autofarm/data/cron.log 2>&1
