# AutoFarm

Blocktrend 的自動化新聞摘要系統。每天掃描電子報和 YouTube 頻道，產出繁體中文兩段式摘要，發布到 [news.blocktrend.today](https://news.blocktrend.today)。

## 運作方式

每天早上 8 點自動執行：

1. **掃描來源** — Gmail 電子報 + YouTube 頻道（config.yml）
2. **去重** — 比對近 7 天已報導主題，避免重複
3. **摘要** — 兩段式格式（背景 + 事實），120~220 字，嚴格台灣繁體中文
4. **社群討論** — 搜尋 X/Twitter 上的相關反應，附在每則摘要下方
5. **用字檢查** — 套用 word-map.yml 自動替換 + zhtw-mcp 檢查
6. **發布** — 部署到 GitHub Pages（docs/）

## 被動學習

系統會從每次改稿中學習，逐漸貼近作者風格：

- **word-map.yml** — 用字偏好字典，產出前自動替換（如「然而→不過」「24/7→全年無休」）
- **draft-lessons.md** — 累積的改稿教訓，每次產出前讀取
- **auto_feedback.py** — 存原稿、比對修改、偵測用字替換
- **週一自動回顧** — 從 Gmail 讀取已發布的週報，跟原稿比對，自動更新規則

## 工作流

| 路線 | 觸發方式 | 說明 |
|------|---------|------|
| 自動摘要 | 每日排程 | farm.py + prompts/auto_draft.md |
| 手動摘要 | `/digest` | 貼入新聞 → 研究 → 摘要 → Notion |
| 改稿回饋 | `/feedback` | 貼回修改版 → 分析差異 → 更新規則 |
| 發布週報 | `/publish` | Notion → Substack 電子報 |
| 自動回顧 | 週一中午 | Gmail 週報 vs 原稿 → 學習 |

## 結構

```
farm.py              # 主程式：抓取、摘要、推送
auto_feedback.py     # 被動學習：存原稿、比對、套用字典
config.yml           # 新聞來源設定
word-map.yml         # 用字偏好字典（38+ 條規則）
CLAUDE.md            # 寫作風格規範
draft-lessons.md     # 累積的改稿教訓
prompts/             # prompt 模板（自動 + 手動路線）
schedule-configs/    # 排程任務設定
scripts/             # 部署和維運腳本
docs/                # GitHub Pages 發布內容
```
