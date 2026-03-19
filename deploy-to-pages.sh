#!/bin/bash
# deploy-to-pages.sh
# 用法: ./deploy-to-pages.sh <type> <date> <title> <source_html_path>
# type: digest | morning | evening
# date: YYYY-MM-DD
# title: 文章標題
# source_html_path: 來源 HTML 檔案的完整路徑
#
# 此腳本會：
# 1. 將 HTML 檔案複製到 autofarm/docs/ 對應資料夾（本地備份）
# 2. 更新 manifest.json（新增條目、去重）
# 3. git add + commit + push autofarm repo
# 4. 同步 docs/ 內容到 digest repo，push 上線到 share.blocktrend.today/digest/

set -e

TYPE="$1"
DATE="$2"
TITLE="$3"
SOURCE="$4"
AUTOFARM_DIR="/Users/fymn/autofarm"
DIGEST_DIR="/Users/fymn/digest"

if [ -z "$TYPE" ] || [ -z "$DATE" ] || [ -z "$TITLE" ] || [ -z "$SOURCE" ]; then
  echo "Usage: $0 <type> <date> <title> <source_html_path>"
  exit 1
fi

cd "$AUTOFARM_DIR"

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

# 複製檔案到 autofarm/docs/
cp "$SOURCE" "$DEST_DIR/$FILENAME"

# 計算相對路徑（相對於 docs/）
case "$TYPE" in
  digest)  REL_PATH="digest/$FILENAME" ;;
  *)       REL_PATH="stories/$FILENAME" ;;
esac

# 更新 manifest.json
MANIFEST="docs/manifest.json"

python3 - <<PYEOF
import json, os

manifest_path = "$MANIFEST"
with open(manifest_path, 'r') as f:
    data = json.load(f)

entries = data.get('entries', [])

new_entry = {
    "type": "$TYPE",
    "date": "$DATE",
    "title": "$TITLE",
    "path": "$REL_PATH"
}
entries = [e for e in entries if e.get('path') != new_entry['path']]
entries.append(new_entry)

entries.sort(key=lambda e: e.get('date', ''), reverse=True)

data['entries'] = entries
with open(manifest_path, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Manifest updated: {len(entries)} entries")
PYEOF

# === Step 1: Commit to autofarm ===
git add docs/
git commit -m "Deploy ${TYPE}: ${TITLE} (${DATE})" || echo "Nothing to commit"
git push origin main || echo "[autofarm] Push failed, will retry next time"

# === Step 2: Sync to digest repo for GitHub Pages ===
if [ -d "$DIGEST_DIR/.git" ]; then
  echo "Syncing to digest repo..."

  # 同步所有 docs/ 內容到 digest repo 根目錄
  # digest repo 的根目錄 = share.blocktrend.today/digest/ 的根
  rsync -av --delete \
    --exclude '.git' \
    "$AUTOFARM_DIR/docs/" "$DIGEST_DIR/"

  cd "$DIGEST_DIR"
  git add -A
  git commit -m "Deploy ${TYPE}: ${TITLE} (${DATE})" || echo "Nothing to commit"
  git push origin main || echo "[digest] Push failed, will retry next time"

  echo "Synced to digest repo: $REL_PATH"
else
  echo ""
  echo "⚠️  digest repo not found at $DIGEST_DIR"
  echo "   Run: git clone https://github.com/ASTROHSU/digest.git ~/digest"
  echo "   Then re-run this script to sync."
  echo ""
fi

echo "Done: $REL_PATH"
