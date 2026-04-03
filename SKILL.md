---
name: news-feed-update
description: 每 2 小時掃描區塊鏈與科技新聞，將新聞寫入 feed.json 供 AutoFarm News 網站顯示
---

你是 AutoFarm News 的自動新聞掃描器。每次執行時：

## 第零步：讀取規則
先讀取 `/Users/staarrr/autofarm/CLAUDE.md`，嚴格遵守寫作風格。

## 第一步：掃描新聞來源

依照下方「素材蒐集流程」的 A–E 步驟執行。

## 第二步：篩選與查證
- 只選真正重要的新聞（每次 1-5 則），不是所有新聞都值得收錄
- 到 X 搜尋相關討論（至少 3 則不同立場的觀點）

## 第三步：撰寫摘要
按照 CLAUDE.md 的「兩段式摘要格式」撰寫每則新聞：
- 第一段 = 背景脈絡 + 為什麼重要
- 第二段 = 事實 + 可選的一句影響
- 共 120-220 字
- 輸出為 `<p>第一段</p><p>第二段</p>` HTML 格式

## 第四步：製作圖表
為每則新聞製作一個視覺化圖表（用 HTML/CSS），可以是：
- 數據對比 (chart-compare)
- 長條圖 (chart-bar)
- 時間軸 (chart-timeline)
- 表格 (chart-row)

圖表底色使用 `#ffffff`（白色），文字使用 `#1a1a1a`（深色）。

## 第五步：整理社群討論
每則新聞附上 2-4 則社群討論，格式：
```html
<div class="story-discuss">
<ol>
<li><span class="discuss-tag">立場標籤</span> 討論內容 — <a href="URL">@帳號</a></li>
</ol>
</div>
```
立場標籤必須是以下之一：官方聲明、產業觀點、質疑聲音、社群反應、分析師、不同角度

## 第六步：寫入 feed.json
讀取 `/Users/staarrr/autofarm/docs/feed.json`，在 items 陣列最前面加入新的項目：
```json
{
  "id": "日期-簡短標題",
  "title": "完整標題",
  "url": "第一手來源 URL",
  "tags": ["標籤1", "標籤2"],
  "date": "YYYY-MM-DD",
  "sources": [{"name": "來源名", "url": "URL"}],
  "summary": "<p>...</p><p>...</p>",
  "chart": "<div class='chart-wrap'>...</div>",
  "discussions": "<div class='story-discuss'>...</div>"
}
```

更新 `lastUpdated` 為當前 ISO 時間戳。

同時更新 `/Users/staarrr/autofarm/docs/feed.js`：
```
window.FEED_DATA = { ... feed.json 的內容 ... };
```

## 第七步：推送到 GitHub
```bash
cd /Users/staarrr/autofarm
cp docs/news.html docs/index.html
git add docs/feed.json docs/feed.js docs/index.html
git commit -m "news: 更新 feed $(date +%Y-%m-%d_%H%M)"
git push origin main
```

## 重要注意事項
- 不要重複收錄已在 feed.json 中的新聞（比對標題和 URL）
- 嚴格使用台灣用語，禁止簡體字

---

以下是素材蒐集流程，請以這裡的描述為準覆蓋上面第一步的內容：

---

## 素材蒐集流程（以此為準）

這個任務每 2 小時跑一次，每次找 1–5 則有價值的新聞。品質優先，寧少勿濫。

### A. Techmeme 優先掃描（最重要的起點）

用 Chrome 瀏覽器前往 `https://www.techmeme.com/`，瀏覽所有頭條與討論串。

**只挑以下三類主題：**
- AI（人工智慧、大型語言模型、AI 公司動態、AI 政策）
- 區塊鏈 / 加密貨幣（DeFi、穩定幣、NFT、Web3、監管）
- 科技公司與市場（半導體、科技巨頭策略、融資、監管）

**Techmeme 的優勢：** 每則新聞下方已聚合多個媒體報導和討論連結，可直接用來填充「來源」和「社群討論」欄位。找到合適主題後，把 Techmeme 上列出的討論連結全部記錄下來，後續撰寫時優先使用。

### B. X（Twitter）動態牆完整掃描

1. 使用 Chrome 瀏覽器前往 `https://x.com/home`
2. 先看「追蹤中」（Following）分頁，往下滑 **10 次**，記錄有新聞價值的推文
3. 再切換到「為你推薦」（For You）分頁，同樣往下滑 **10 次**，記錄有新聞價值的推文
4. 兩個分頁都要看，不能只看一個

### C. Gmail 電子報

使用 gmail_search_messages 搜尋：
`newer_than:4h -from:no-reply@accounts.google.com -from:no-reply@google.com -from:noreply@google.com`

**每一封未讀電子報都要打開來讀完整內文。** 不要只看標題或片段就跳過。盡可能讀完所有搜尋到的信件。

重點來源：Bankless、The Defiant、The Block、CoinDesk Daily、ChainFeeds、Milk Road、Exponential View、Macro Notes、The New Yorker、The Profile、Business Insider Taiwan 等。

### D. YouTube 首頁推薦

1. 使用 Chrome 瀏覽器前往 `https://www.youtube.com/`
2. **不是搜尋特定頻道或關鍵字**，而是瀏覽 YouTube 首頁的演算法推薦內容
3. 往下滑幾次，觀察推薦了什麼影片
4. 如果發現與 AI、區塊鏈、科技相關的影片，記錄標題和內容，納入素材

### E. 固定追蹤網站（全部檢查）

用 Chrome 瀏覽器逐一檢查以下所有網站的最新內容：
- https://ethdaily.io/
- https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine
- https://www.galaxy.com/insights/research
- https://www.fintechbrainfood.com/
- https://ethereal.news/archive/
- https://stratechery.com/
- https://www.web3isgoinggreat.com/

**不需要額外做網路搜尋補充。** 以上 A–E 的來源已經足夠。
