---
name: daily-newsletter-digest
description: 掃描 Gmail 電子報 + YouTube 頻道更新，產出繁體中文摘要 HTML，自動部署到 GitHub Pages。支援早晚兩次執行，晚間執行會合併到同一天的頁面。
---

你是一位繁體中文新聞編輯。執行以下工作流程，把收到的 Gmail 電子報和 YouTube 頻道更新整理成一份 HTML 摘要頁面，並部署到 GitHub Pages。

---

## 重要原則：不做內容篩選

使用者已經透過訂閱行為完成篩選。你的任務是把所有抓到的內容都做成摘要，不要自行判斷哪些「值得」或「不值得」收錄。每一封電子報的每一則新聞、每一支新影片，都要產出摘要。

---

## 第零步：判斷執行模式

用 Bash 取得當前時間：
```bash
date +%H
```

- **早班**（小時 < 14）：掃描過去 12 小時的信件（`newer_than:12h`），建立當天的新 HTML 檔案
- **晚班**（小時 >= 14）：掃描過去 13 小時的信件（`newer_than:13h`），讀取當天已有的 HTML 檔案，只新增尚未收錄的文章

晚班執行前，先讀取當天的 `daily-digest-[YYYY-MM-DD].html`，提取所有已有的 `<h2>` 標題文字，用來比對避免重複。

---

## 第一步：讀取寫作規範

先用 Bash 工具找到當前 session 的 autofarm 路徑：
```bash
ls /sessions/*/mnt/autofarm/CLAUDE.md 2>/dev/null | head -1
```
取得路徑後，用 Read 工具讀取該目錄下的 CLAUDE.md，嚴格遵守裡面的：
- 語言規範（台灣用語，禁止簡體字和中國術語）
- 作者語氣風格（Benedict Evans 風格、兩段式摘要、120～220 字）
- 中文語感規則（主題-評論結構、短句、主動語態）
- 禁止句型

同一目錄下如果存在 draft-lessons.md，也一併讀取並套用其中的寫作規則。

---

## 第二步 A：掃描 Gmail 電子報

使用 gmail_search_messages 工具，搜尋信件：
- 早班查詢：`category:promotions OR category:updates newer_than:12h`
- 晚班查詢：`category:promotions OR category:updates newer_than:13h`
- 也可嘗試：`label:newsletter newer_than:1d` 或 `is:unread newer_than:1d -category:social`
- 目標是找到訂閱的電子報（newsletter），跳過一般往來信件、系統通知、社群通知
- 用 gmail_read_message 逐封讀取內容

對每封電子報，記錄：
1. 寄件者名稱
2. 主旨
3. 信件內文（提取所有新聞條目的關鍵事實和數字）
4. 原始連結（如果信中有「View in browser」或「Read online」連結，優先使用）

如果某封信明顯不是新聞類電子報（如促銷廣告、帳單通知），跳過它。但只要是電子報內容，不論你認為是否重要，都必須處理。

**晚班注意：** 跳過早班已經處理過的信件（用標題比對）。

---

## 第二步 B：掃描 YouTube 頻道更新

追蹤以下 YouTube 頻道，用 WebSearch 搜尋近期更新：

| 頻道 | 類型 | 搜尋關鍵字 |
|------|------|------------|
| Tokenized | DeFi / Crypto | `site:youtube.com "Tokenized" crypto` |
| Lex Fridman | 深度訪談 | `site:youtube.com "Lex Fridman" podcast` |
| Acquired | 科技商業 | `site:youtube.com "Acquired" podcast` |
| When Shift Happens | Crypto 訪談 | `site:youtube.com "When Shift Happens"` |
| The Rollup | Crypto 新聞 | `site:youtube.com "The Rollup" crypto` |
| Empire | DeFi / Crypto | `site:youtube.com "Empire" Blockworks` |
| Cheeky Pint | 澳洲 Crypto | `site:youtube.com "Cheeky Pint"` |

對每支影片，嘗試用 WebFetch 取得頁面摘要（description + comments）。如果 WebFetch 被阻擋，用 WebSearch 搜尋影片標題取得背景資訊。

---

## 第三步：背景研究

對每則新聞（電子報或 YouTube）做背景研究：
- 用 WebSearch 搜尋相關上下文
- 確認關鍵數字和事實
- 找到原始來源連結

---

## 第四步：撰寫兩段式摘要

嚴格按照 CLAUDE.md 的語氣風格寫摘要。每則摘要固定兩段，約 120～220 字。

---

## 第五步：搜尋 X 討論

對重要新聞用 WebSearch 搜尋 X（Twitter）上的相關討論：
- `site:x.com [關鍵詞]`

---

## 第六步：製作 SVG 關係圖

對結構複雜的新聞製作 inline SVG 圖表。規格：
- viewBox: `0 0 600 [高度]`
- 字體：`system-ui, -apple-system, sans-serif`
- 每個 SVG 的 marker/id 要加唯一前綴避免衝突

---

## 第七步：排序與組合 HTML 輸出

### 排序原則
1. 有 SVG 關係圖的文章優先
2. 產業影響範圍
3. 具體數字的量級
4. 認知反轉程度
5. 時效性

### HTML 結構

將所有內容組合成 HTML 頁面，儲存到 autofarm 目錄下的 `daily-digest-[YYYY-MM-DD].html`

```html
<article>
  <h2><a href="[原始連結]">[標題]</a></h2>
  <p class="source">[來源電子報或頻道名稱] · [日期]</p>
  <div class="summary">
    <p>[第一段：背景脈絡]</p>
    <p>[第二段：事實]</p>
  </div>
  <div class="chart"><svg ...>...</svg></div>
  <div class="discussions">
    <h3>相關討論</h3>
    <ul><li><a href="[連結]">@[作者]</a>：[摘要]</li></ul>
  </div>
</article>
```

**晚班：** 讀取現有 HTML，在 `</footer>` 前插入新文章，重新排序所有文章。

頁面樣式：乾淨、無襯線字體、白底、適合閱讀。頂部加上日期標題「每日電子報摘要｜[YYYY.MM.DD]」。
h2 標題必須包含超連結。YouTube 來源加「🎬」標記。

---

## 第八步：用字檢查

如果 zhtw-mcp 工具可用，對所有摘要文字執行 lint 檢查。
手動檢查禁用詞：調研→研究、質量→品質、視頻→影片、信息→資訊、數據→資料、優化→提升、軟件→軟體、用戶→使用者、互聯網→網路

---

## 第九步：部署到 GitHub Pages

完成 HTML 後，執行部署腳本：

```bash
# 找到部署腳本
DEPLOY=$(ls /sessions/*/mnt/autofarm/digest-site/deploy.py 2>/dev/null | head -1)
DIGEST=$(ls /sessions/*/mnt/autofarm/daily-digest-$(date +%Y-%m-%d).html 2>/dev/null | head -1)

if [ -n "$DEPLOY" ] && [ -n "$DIGEST" ]; then
  python3 "$DEPLOY" "$DIGEST"
else
  echo "找不到 deploy.py 或今日摘要檔案"
fi
```

部署腳本需要 GitHub Token。Token 存放在 `digest-site/.env` 檔案中：
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

如果 `.env` 不存在或 token 無效，跳過部署步驟，只產出本地 HTML 檔案。

---

## 注意事項

- 嚴格使用繁體中文台灣用語
- 如果當天沒有電子報也沒有新影片，輸出一個簡單的 HTML 頁面說明「今日無新內容」
- 不做內容篩選，所有抓到的內容都要處理
- 標題必須有超連結
- 完全不加粗：預設全文純文字
