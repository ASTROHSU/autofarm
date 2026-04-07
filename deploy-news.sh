#!/bin/bash
# ──────────────────────────────────────────────
# deploy-news.sh — 只同步「資料」到 MNnews，不碰前端
#
# autofarm 負責產出 feed.json（資料）
# MNnews 負責自己的前端（news.html 等）
# 這個腳本只把資料推過去，不覆蓋前端檔案
# ──────────────────────────────────────────────

set -e

AUTOFARM="/Users/staarrr/autofarm"
MNNEWS="/Users/staarrr/MNnews"

# 確認 MNnews repo 存在
if [ ! -d "$MNNEWS" ]; then
  echo "❌ 找不到 $MNNEWS，先 clone..."
  cd /Users/staarrr
  git clone git@github.com:ASTROHSU/MNnews.git
fi

# ── 只同步資料檔 ──
echo "📋 同步 feed 資料到 MNnews..."
cp "$AUTOFARM/docs/feed.json" "$MNNEWS/docs/feed.json"

# 從 feed.json 產生 feed.js（瀏覽器用的版本）
echo "⚙️  產生 feed.js..."
echo -n "window.FEED_DATA = " > "$MNNEWS/docs/feed.js"
cat "$MNNEWS/docs/feed.json" >> "$MNNEWS/docs/feed.js"
echo ";" >> "$MNNEWS/docs/feed.js"

# ── 推送 ──
cd "$MNNEWS"
git add docs/feed.json docs/feed.js
git commit -m "data: 更新 feed $(date +%Y-%m-%d_%H%M)" || echo "⏭️  沒有變更，跳過 commit"
git push origin main

echo "✅ 已推送到 ASTROHSU/MNnews（僅資料更新）"
