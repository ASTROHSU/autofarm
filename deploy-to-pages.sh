#!/bin/bash
# deploy-to-pages.sh
# 用法: ./deploy-to-pages.sh <type> <date> <title> <source_html_path>
# type: digest | morning | evening
# date: YYYY-MM-DD
# title: 文章標題
# source_html_path: 來源 HTML 檔案的完整路徑
#
# 此腳本會：
# 1. 將 HTML 檔案複製到 docs/ 對應資料夾
# 2. 更新 manifest.json（新增條目、去重）
# 3. git add + commit + push
#
# 網站由 GitHub Pages 從 autofarm repo 的 docs/ 資料夾提供
# URL: share.blocktrend.today/autofarm/

set -e

TYPE="$1"
DATE="$2"
TITLE="$3"
SOURCE="$4"
REPO_DIR="/Users/fymn/autofarm"

if [ -z "$TYPE" ] || [ -z "$DATE" ] || [ -z "$TITLE" ] || [ -z "$SOURCE" ]; then
  echo "Usage: $0 <type> <date> <title> <source_html_path>"
  exit 1
fi

cd "$REPO_DIR"

# 決定目標路徑
case "$TYPE" in
  digest)
    DEST_DIR="docs/digest"
    FILENAME="${DATE}.html"
    ;;
  morning)
    DEST_DIR="docs/stories"
    BASENAME=$(basename "$SOURCE")
    FILENAME="$BASENAME"
    ;;
  evening)
    DEST_DIR="docs/stories"
    BASENAME=$(basename "$SOURCE")
    FILENAME="$BASENAME"
    ;;
  *)
    echo "Unknown type: $TYPE (use digest, morning, or evening)"
    exit 1
    ;;
esac

mkdir -p "$DEST_DIR"

# 複製檔案
cp "$SOURCE" "$DEST_DIR/$FILENAME"

# 計算相對路徑（相對於 docs/）
case "$TYPE" in
  digest)  REL_PATH="digest/$FILENAME" ;;
  *)       REL_PATH="stories/$FILENAME" ;;
esac

# 更新 manifest.json
MANIFEST="docs/manifest.json"

# 用 python 更新 JSON（去重 + 新增）
python3 - <<PYEOF
import json, os

manifest_path = "$MANIFEST"
with open(manifest_path, 'r') as f:
    data = json.load(f)

entries = data.get('entries', [])

# 去重：移除同 path 的舊條目
new_entry = {
    "type": "$TYPE",
    "date": "$DATE",
    "title": "$TITLE",
    "path": "$REL_PATH"
}
entries = [e for e in entries if e.get('path') != new_entry['path']]
entries.append(new_entry)

# 按日期降序排列
entries.sort(key=lambda e: e.get('date', ''), reverse=True)

data['entries'] = entries
with open(manifest_path, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Manifest updated: {len(entries)} entries")
PYEOF

# Git commit & push
git add docs/
git commit -m "Deploy ${TYPE}: ${TITLE} (${DATE})" || echo "Nothing to commit"
git push origin main || echo "Push failed, will retry next time"

echo "Deployed: $REL_PATH"
