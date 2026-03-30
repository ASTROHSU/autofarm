# AutoFarm

Blocktrend 的自動化新聞摘要系統。每天掃描電子報和 YouTube 頻道，產出繁體中文兩段式摘要，發布到 [news.blocktrend.today](https://news.blocktrend.today)。

## 核心流程

### 自動摘要（每天早上 8 點）

掃描 → 去重 → 摘要 → 社群討論 → 用字檢查 → 發布

1. 掃描 Gmail 電子報 + YouTube 頻道（`config.yml`）
2. 比對近 7 天已報導主題，排除重複
3. 兩段式摘要（背景 + 事實），120~220 字，台灣繁體中文
4. 搜尋 X 上的社群反應，附在摘要下方
5. `word-map.yml` 自動替換 + zhtw-mcp 用字檢查
6. 部署到 GitHub Pages（`docs/`）

### 自動回顧（每週一中午）

從 Gmail 讀取已發布的週報 → 跟原稿比對 → 自動學習

- 偵測用字替換 → 更新 `word-map.yml`
- 分析結構和語氣差異 → 更新 `draft-lessons.md`
- 記錄選題偏好（哪些被選、哪些被淘汰）

系統會越用越像作者的風格，不需要手動操作。

## 結構

```
farm.py              # 主程式：抓取、摘要、推送
auto_feedback.py     # 被動學習：存原稿、比對、套用字典
config.yml           # 新聞來源設定（RSS、YouTube）
word-map.yml         # 用字偏好字典（38+ 條規則）
CLAUDE.md            # 寫作風格規範
draft-lessons.md     # 累積的改稿教訓
prompts/             # prompt 模板
schedule-configs/    # 排程任務設定
scripts/             # 部署和維運腳本
docs/                # GitHub Pages 發布內容
```
