#!/bin/bash
# auto-push.sh
# 每次執行時檢查 autofarm repo 是否有未推送的 commit，有就推
# 設計給 launchd 定期呼叫

REPO_DIR="$HOME/autofarm"
LOG_FILE="$REPO_DIR/.auto-push.log"

cd "$REPO_DIR" || exit 1

# 確認是 git repo
if [ ! -d .git ]; then
    echo "$(date): Not a git repo" >> "$LOG_FILE"
    exit 1
fi

# 取得本地和遠端的 commit 差距
git fetch origin main 2>/dev/null

LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    # 沒有新 commit，不做事
    exit 0
fi

# 有新 commit，推送
if git push origin main 2>>"$LOG_FILE"; then
    echo "$(date): Pushed $LOCAL (was $REMOTE)" >> "$LOG_FILE"
else
    echo "$(date): Push failed" >> "$LOG_FILE"
fi
