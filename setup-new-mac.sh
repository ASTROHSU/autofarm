#!/bin/bash
# setup-new-mac.sh
# 在新電腦上執行這個腳本，完成 autofarm 環境的遷移
# 用法: bash setup-new-mac.sh
# 前提: 新電腦已安裝 Homebrew、git、GitHub SSH key 已設定
set -e

REPO="https://github.com/ASTROHSU/autofarm.git"
TARGET="$HOME/autofarm"

echo ""
echo "=== autofarm 新電腦安裝腳本 ==="
echo ""

# 1. Clone repo
if [ -d "$TARGET/.git" ]; then
  echo "✓ $TARGET 已存在，執行 git pull 更新..."
  cd "$TARGET" && git pull origin main
else
  echo "→ Clone repo 到 $TARGET ..."
  git clone "$REPO" "$TARGET"
fi

echo ""
echo "✓ repo 已就緒：$TARGET"
echo ""
echo "=== 接下來請手動完成以下步驟 ==="
echo ""
echo "【1】在 Cowork 選擇 workspace 資料夾"
echo "     開啟 Cowork → 點左上角資料夾圖示 → 選擇 $TARGET"
echo ""
echo "【2】重新授權 Gmail MCP"
echo "     Cowork 設定 → Connections → Gmail → Reconnect"
echo ""
echo "【3】重新授權 Notion MCP"
echo "     Cowork 設定 → Connections → Notion → Reconnect"
echo ""
echo "【4】確認 git push 可以運作"
echo "     cd $TARGET && git push origin main"
echo "     （如果失敗，請先設定 GitHub SSH key 或 Personal Access Token）"
echo ""
echo "【5】測試排程（可選）"
echo "     在 Cowork 裡對著 daily-newsletter-digest 排程點「立即執行」，確認可以產出 HTML"
echo ""
echo "=== 完成！==="
