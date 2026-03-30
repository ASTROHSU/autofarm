# 電子報工作流改善報告

生成時間：2026-03-24 11:30（自動排程執行）

---

## 摘要

這次檢視發現三個值得優先處理的問題：其一，近三天日報中有兩天（03-22、03-23）完全缺少討論區塊，與 CLAUDE.md 規範不符；其二，`auto_draft.md` 和 `auto_draft_multi.md` 完全沒有 few-shot 範例，而 `draft-lessons.md` 已累積了十多組優質定稿可供引用；其三，config.yml 目前只啟用 YouTube/podcast 來源，但近期日報的來源標注都是 Gmail 電子報——兩者之間存在明顯的工作流斷層，代表日報主要是手動撰寫，自動化 pipeline 尚未用上。

---

## 一、摘要品質

### 做得好的地方

**03-24 日報整體品質最高。** 四則摘要全部附有討論區塊，且討論品質不錯——特別是 Resolv 那則，引用了 @d2_finance 的鏈上數據與 The Defiant 創辦人 Cami 的評論，正反立場都有，完全符合規範。

**「今日關聯」區塊是這週最亮眼的新增功能。** 03-23 把伊朗 LNG 與巴基斯坦太陽能串在一起；03-24 把 Resolv 駭客事件與 CLARITY Act 並排，並在前言中說明「市場失敗與監管推進，本週恰好同步發生」——這種跨新聞的脈絡串聯讓整份日報有故事感，超出了單純的新聞羅列，值得繼續保留並強化。

**03-24 的氦氣/晶片供應鏈摘要是近期最佳範例。** 數字錨定紮實（34%、65%、80%、35～48 天），結尾是事實（「採購團隊接下來幾週要加緊補貨」），沒有分析性收尾，完全符合規範。

### 需要改善的地方

**問題一：03-22 和 03-23 完全缺少討論區塊**

03-22 的 5 則摘要、03-23 的 3 則摘要都沒有任何討論區塊，違反 CLAUDE.md「每則兩段式摘要下方必須附上一個相關討論區塊」的規範。從 HTML 結構看，03-22 的設計也與後兩天不同（沒有 `relation-notice`、沒有 `story-group`），推測這兩天是手動撰寫但跳過了搜尋討論這個步驟。

建議：手動撰寫流程（/digest）有完整的討論搜尋步驟（步驟 3），應確保每次都執行；若某則新聞確實找不到相關討論，補一個「相關：」背景連結也符合規範。

**問題二：Anthropic vs Pentagon 摘要字數超標**

03-24 第一則（Anthropic 起訴五角大廈）估計兩段合計約 270 字，明顯超過 220 字上限。第二段資訊密度過高，把「加州聽證」「150 名退休法官連署」「Jeff Dean 與 OpenAI 研究員聯名」全塞進去，讀起來像新聞整理而非摘要。

原文片段（第二段）：「近 150 名退休聯邦法官已連署支持 Anthropic；Google 首席科學家 Jeff Dean 與多名 OpenAI 研究人員也聯名提交意見書，稱政府這項指定可能「嚴重衝擊整個產業」。」

建議修改：選一個最有力的事實留下，另一個刪去。「近 150 名退休聯邦法官連署」比「Jeff Dean 也表態」更有分量，建議保留前者，刪去後者。

**問題三：03-23 伊朗/油價摘要有制式開頭**

第一段開頭：「中東衝突中，能源從來是最鋒利的武器。過去幾十年，化石燃料出口國靠著控制天然氣和石油供給，在地緣政治上握有極大籌碼；一旦局勢緊張，進口依賴型國家就首當其衝。」

這段很像 CLAUDE.md 所禁止的「在當今社會」型制式開頭——以宏觀道理打頭，而不是直接給讀者具體資訊。對比 03-24 的氦氣摘要開頭「氦氣在晶片製造中不可替代：冷卻矽晶圓超過 20 個製程步驟都需要它，目前沒有替代材料」，後者直接給事實，前者給道理。

建議：此類摘要的第一段應從「卡達的 LNG 設施是全球最集中的液化天然氣出口樞紐」這樣的具體事實出發，而不是先說「能源是地緣政治武器」這種通論。

**問題四：巴基斯坦太陽能摘要有分析性收尾（出現兩次）**

03-23 結尾：「能源主權從來不只是環保議題；對依賴進口的國家，這是地緣政治的防護罩。」
03-22 同一則結尾：「太陽能板裝上去了，歐佩克就擋不住陽光了。」

前者（03-23 版）是明確的分析性結論，違反規範；後者（03-22 版）雖然口語化，也是作者本人在下判斷。建議改為事實收尾，例如直接以「Azeem Azhar 估計，這讓巴基斯坦在此次衝擊中至少節省了 63 億美元（約佔 GDP 的 1.7%）」結束。

---

## 二、Prompt 工程

### 現況 vs Best Practice

根據 2025-2026 年的 prompt engineering 研究，提升生成式 AI 輸出品質最有效的手段是提供 **few-shot 範例**——直接在 prompt 中貼入過去的優質輸出作為參照。GDELT Project 的 Prompt Evolver 研究指出，即使是精心設計的規則清單，也不如直接展示「理想輸出長什麼樣」來得有效，因為規則是抽象的，範例是具體的。

目前 `auto_draft.md` 和 `auto_draft_multi.md` 都沒有附任何 few-shot 範例，只有規則清單和自查表。相較之下，`draft-lessons.md` 已累積了 13 組高品質的「AI 初稿 vs 使用者定稿」對照，是極佳的 few-shot 素材，卻完全沒有被直接引用——現在只是整份文件 `{LESSONS}` 整體塞入，而非挑選代表性範例突出呈現。

另一個差距是 `auto_discussion.md` 只提供了格式範例，但沒有展示「好討論區塊 vs 差討論區塊」的對照，導致模型難以判斷什麼樣的引言值得選。

### 建議修改

**建議一：在 auto_draft.md 的 {LESSONS} 注入之外，另加 2～3 個精選 few-shot 範例**

從 draft-lessons.md 中選取最具代表性的定稿（建議選案例一 Visa×Bridge、案例二 Kraken Federal、案例八 Nasdaq×Kraken），以以下格式加入 prompt，放在「文章內容」之前：

```
---

## 優質輸出範例（直接參照格式與語感）

### 範例一（機制說明型）
TITLE: Visa × Bridge 開啟穩定幣發卡新模式
SUMMARY:
市面上的穩定幣 Visa 卡已經不少，EtherFi、RedotPay 都是常見的選擇。但多數穩定幣 Visa 卡背後，都依賴同一家公司 Rain。這家公司持有 Visa 的主要會員資格（Principal Member），負責發卡以及後續的監管合規。

不過上週 Visa 宣布與 Bridge 合作，開啟另一種新模式。未來如果想發一張穩定幣 Visa 卡，大致有兩條路可以走：找 Rain 是全端模式，簽約後由他們包辦一條龍服務；找 Bridge 則是 API 模式。Bridge 把 Visa 與卡片贊助銀行 Lead Bank 打包成一個 API 介面，讓想發行穩定幣 Visa 卡的公司可以直接串接。
```

這樣可以讓模型直接理解語感，而不只是靠規則描述去猜測。

**建議二：自查清單移到 prompt 末尾，緊跟在文章內容之後**

目前自查清單放在禁止事項之後、文章內容之前。LLM 在讀完文章、準備生成時，自查清單已經在遠端。建議移到 prompt 最末尾（輸出格式說明之後），讓模型在輸出前能即時對照。

**建議三：統一 auto_draft.md 和 auto_draft_multi.md 的段落結構描述**

`auto_draft.md` 用「兩段結構」描述（第一段=背景、第二段=事實），`auto_draft_multi.md` 用「三要素順序」描述（過去狀況→現在事件→為什麼會這樣）。雖然本質相同，但描述方式不同可能導致模型在 multi 模式下生成偏離兩段式結構的摘要。建議統一為「兩段式結構」的描述。

---

## 三、工作流程架構

### 效率與品質觀察

**關鍵發現：config.yml 啟用的來源與實際日報來源完全脫節**

目前 config.yml 啟用的來源全部是 YouTube 頻道（Tokenized Podcast、Lex Fridman、Acquired 等）和一個 podcast RSS（Cheeky Pint）。但近三天日報的 meta 標注都是「來源：Gmail 電子報」，內容取自 The Defiant、a16z crypto、Bankless、Exponential View、Milk Road——這些全部標記為「暫時停用」或根本不在設定中。

這代表目前日報的實際工作流是：**手動從 Gmail 電子報取材 → 手動製作日報**，`farm.py` 的自動化 pipeline 可能主要用於處理 YouTube 逐字稿，與日報主流工作流沒有直接連結。這不是問題，但值得明確記錄，避免日後維護時產生混淆。

**DuckDuckGo 討論搜尋品質不穩定**

`search_web_discussions()` 和 `search_x_discussions()` 都用 DuckDuckGo HTML 抓取，容易受反爬蟲策略影響，也無法取得完整推文內容（只有標題+snippet）。從 03-22 和 03-23 完全沒有討論區塊來看，可能這兩天的搜尋就靜默失敗了，但程式沒有留下明確的錯誤記錄。

**`seen.json` 會無限增長**

目前 seen.json 只加不刪，長期下來會越來越大。建議加入定期清理邏輯，例如只保留最近 90 天的已處理 URL。

**farm.py 沒有實作 CLAUDE.md 提到的「7 天日報語意去重」邏輯**

CLAUDE.md 說「讀取近 7 天的日報 HTML，提取所有已報導的標題，排除已報導主題」，但 farm.py 只用 URL 去重（seen.json），沒有從 docs/digest/*.html 讀取已報導標題做語意比對。這意味著同一個新聞事件若來自不同 URL，可能被重複處理。

### 建議的新來源或調整

**優先恢復 EthDaily 和 Galaxy Research 兩個來源**

近期日報的內容主要取自文字電子報，說明文字來源比 YouTube 逐字稿更適合目前的兩段式摘要格式。EthDaily 和 Galaxy Research 的代碼都還在 config.yml 中（只是被註解掉），建議先測試恢復 EthDaily 的 RSS 抓取，驗證自動化產出品質。

---

## 四、Skill 定義

### 流程銜接問題

**問題一：/digest 步驟 3 的 Bash 程式碼需要手動替換 placeholder**

步驟 3 有三個需要手動替換的 placeholder（`{KEYWORDS}`、`{TITLE}`、`{SUMMARY}`），容易忘記替換導致執行失敗。這段程式碼更適合作為「說明性參考範例」，而不是讓 Claude 直接複製執行的命令。

建議：改寫為說明性文字（「用 farm.py 的 search_discussions 函式，帶入前一步的標題和摘要作為關鍵字」），讓 Claude 根據上下文自行填入正確的值。

**問題二：/publish 的 allowed-tools 設定可能有誤**

allowed-tools 只列了 `mcp__...__search` 和 `mcp__...__fetch`，但步驟 1 說要「查詢資料庫過濾狀態 = 待發布的條目」。若 Notion MCP 沒有對應工具，整個發布流程就會中斷。建議確認實際可用的工具名稱，並更新 allowed-tools。

**問題三：/feedback 缺少 WebSearch 工具**

當規則提取需要確認某詞是否為台灣慣用語時，目前 allowed-tools 只有 Read、Edit、Write，無法搜尋外部資料。建議加入 WebSearch 供確認用語時使用。

### 建議修改

**/digest SKILL.md：簡化步驟 2 的確認等待**

「先提出你打算怎麼切這篇新聞，等使用者確認後再寫正文」這個設計在互動對話中合理，但若使用者只是想快速產出，每次等確認會打斷節奏。建議改為：提出切入角度後若使用者未在 30 秒內回應，則直接進入正文撰寫；或提供「快速模式」旗標讓使用者選擇是否跳過確認。

---

## 優先順序建議

| 順序 | 改善項目 | 預期效果 | 難度 |
|------|---------|---------|------|
| 1 | 在 auto_draft.md 加入 2～3 個精選 few-shot 範例 | 摘要語感和格式一致性大幅提升 | 低 |
| 2 | 確保每則手動日報都執行討論搜尋步驟（或補「相關：」連結） | 符合 CLAUDE.md 規範，每則摘要資訊更完整 | 低 |
| 3 | 明確記錄 Gmail 手動路線與 farm.py 自動化路線的分工，更新 CLAUDE.md | 避免維護混淆 | 低 |
| 4 | 自查清單移至 prompt 末尾，緊跟在文章內容之後 | 模型輸出前能即時對照，減少格式違規 | 低 |
| 5 | 統一 auto_draft.md 和 auto_draft_multi.md 的段落結構描述 | 多則模式下摘要格式更穩定 | 低 |
| 6 | 修正 /publish SKILL.md 的 allowed-tools | 避免發布流程因工具名稱錯誤中斷 | 中 |
| 7 | 為 auto_discussion.md 加入「好討論 vs 差討論」對照範例 | 減少引用品質不佳的討論 | 中 |
| 8 | seen.json 加入定期清理邏輯（保留近 90 天） | 避免長期累積導致效能問題 | 中 |
| 9 | 測試恢復 EthDaily RSS 抓取 | 擴充自動化覆蓋範圍 | 中 |
| 10 | 實作 CLAUDE.md 提到的「7 天日報標題語意去重」邏輯 | 減少跨來源重複報導 | 高 |

---

*此報告由排程任務自動生成（autofarm-self-review），所有建議需經使用者確認後才執行修改。*

## 摘要

本次審查讀取了 3/22、3/23、3/24 三份日報，並完整檢視 `auto_draft.md`、`auto_discussion.md`、`auto_draft_multi.md`、`farm.py`、`config.yml`、三個 SKILL.md 以及 `draft-lessons.md`。發現五個重點改善機會：一、3/22 和 3/23 兩份日報的全部摘要缺少「相關討論」區塊，違反 CLAUDE.md 強制規範，可能源自 DuckDuckGo 搜尋失敗無 fallback；二、「巴基斯坦太陽能」同一故事同時出現在 3/22 和 3/23，顯示去重機制僅比對 URL，無法攔截內容相同但不同連結的重複報導；三、`config.yml` 目前所有啟用來源全為 YouTube 播客，文字電子報（The Defiant、a16z、Milk Road、Exponential View 等）均未進入自動化流程，日報實際靠手動 `/digest` 維持；四、`/digest` SKILL.md 步驟 3 的 Bash 範例程式碼傳入了 `OpenAI` client，但 `farm.py` 實際的 `generate_discussion` 函數簽名已改為接收 `genai.Client`（Gemini）；五、Prompt 缺少嵌入式 few-shot 完整示例，且字數自查指令不夠具體，導致多則摘要系統性超標 220 字。

---

## 一、摘要品質

### 做得好的地方

**3/24 整體最接近規範要求**，有幾個具體亮點值得保留。

第二則（氦氣供應鏈）的數字錨點完整、因果鏈清晰：「供應全球約 34% 的需求」→「南韓從卡達進口 65%」→「南韓工廠負責全球約 80% 的 HBM」，三層數字環環相扣，讀者不需自己補腦，就能理解為什麼卡達被炸會影響 AI 晶片。

第三則（Resolv 駭客）以 Marc Zeller 在 X 上的引述結尾（「策展人產業的設計根本有問題，根本沒有在做真正的策展」），符合 `draft-lessons.md` 的「結尾用引述收尾比自己寫的分析更有力」原則。

全三天摘要的語序均符合中文主題-評論結構，無英文翻譯體。禁用詞（用戶、數據、視頻等）全部清零。無任何加粗。

**3/22 的 402 狀態碼摘要**有一個漂亮的歷史對比開場：「1997 年，HTTP 標準制定者發明了 402 狀態碼，意思是『這個內容要付費』，但當時沒有可行的線上小額支付，這個代碼從未被正式實作。」符合 `draft-lessons.md` 的「先給具體事實，讓讀者自己理解概念」原則。

**今日關聯提示**（黃底側欄）是近期才加入的功能，做得很好——3/24 的「市場失敗與監管推進，本週恰好同步發生」把第 3、4 則串在一起，讓讀者主動建立跨報導的連結。

### 需要改善的地方

**問題一：3/22 與 3/23 的全部摘要缺少「相關討論」區塊（違反強制規範）**

CLAUDE.md 明訂「每則兩段式摘要下方，必須附上一個『相關討論』區塊」，但 3/22（5 則）和 3/23（3 則）的所有故事均無此區塊，只有 3/24（4 則）全數附上。目前沒有任何警示或 fallback。

推測原因：DuckDuckGo 連續搜尋可能被 rate limit，導致某些天的討論搜尋步驟靜默失敗；或搜尋結果完全不相關，模型輸出 `DISCUSSION: NONE`，而系統選擇跳過而非補充「背景」型替代內容。

**問題二：巴基斯坦太陽能同一故事在 3/22 和 3/23 各出現一次**

「一年裝了 17GW 太陽能」這則故事，在 3/22 和 3/23 都出現了（來源均為 Exponential View #566），兩段摘要幾乎內容相同。這是去重失效的直接證據——`seen.json` 以 URL 為鍵，若兩次抓取的是相同電子報但 URL slug 不同，就會雙重處理。

**問題三：多則摘要字數超標**

估算近三天字數，部分摘要明顯超過 220 字（如 3/24 Resolv 攻擊約 267 字，3/23 ERC-8183 約 270 字）。Prompt 的自查清單雖有「字數是否在 220 字以內？→ 超過就壓縮」，但沒有指定計算單位（純漢字？含英數字？）且無強制確認機制。

**問題四：3/23 第二則（伊朗/油價）第一段是通論背景，資訊密度低**

原文第一段：「中東衝突中，能源從來是最鋒利的武器。過去幾十年，化石燃料出口國靠著控制天然氣和石油供給，在地緣政治上握有極大籌碼；一旦局勢緊張，進口依賴型國家就首當其衝。這次伊朗直接打擊卡達的液化天然氣（LNG）設施，把這個邏輯再次推到了極限。」

這段符合 CLAUDE.md 禁止的「制式開頭」模式——「能源從來是最鋒利的武器」是通論觀察，缺乏具體脈絡。CLAUDE.md 要求第一段要讓讀者「馬上知道這則新聞該放在什麼脈絡下理解」，但這段告訴讀者的是眾所周知的地緣政治通論，而非「為什麼卡達的 LNG 設施被炸這件事格外重要」。

修改方向：直接從「卡達的拉斯拉凡設施供應歐洲 XX% 的天然氣，日、韓仰賴它的比例尤高」這類具體事實切入。

**問題五：3/23 巴基斯坦太陽能末句有分析性結尾**

「能源主權從來不只是環保議題；對依賴進口的國家，這是地緣政治的防護罩。」這句話是作者的觀察性結論，違反 CLAUDE.md「禁止分析性收尾」規定。若要保留這個意思，可以改為引用 Azeem Azhar 的原話作結。

**問題六：3/22 HTML 樣式模板與 3/23、3/24 不一致**

3/22 使用舊版模板（Noto Serif TC 作為 body 字型、無 `border-radius` 卡片、無 discussion 區塊 CSS），3/23 和 3/24 使用新版模板（白色圓角卡片、story-group、discussion 樣式完整）。若有人連續瀏覽多份日報，視覺一致性不佳。

---

## 二、Prompt 工程

### 現況 vs Best Practice

`auto_draft.md` 的基本結構良好：有角色定義、RCCF 框架（Role/Context/Constraints/Format）、台灣用語對照表和自查 checklist。`auto_discussion.md` 格式規範明確，引言格式有示例。兩者均有 `{LESSONS}` 佔位符整合改稿記錄。

根據 2025-2026 年的 LLM 摘要品質研究，高效摘要 prompt 有三個關鍵差距：

**差距一：缺乏嵌入式 few-shot 完整示例（最重要）**

目前 `{LESSONS}` 注入的是整份 `draft-lessons.md`（800+ 行、超過 8,000 字），內容是差異分析表和規則說明。研究指出，few-shot 示例對「語氣指紋」的傳遞效果（括弧短評風格、冒號用法、結尾事實收束方式）遠勝於文字規則描述。目前的長文規則清單等同於讓模型「看說明書」，而非「看示範」。

建議在 `auto_draft.md` 輸出格式之前加入 2 則定稿全文示例（可從 `draft-lessons.md` 的「定稿全文（參考）」段落直接取用），格式為：

```markdown
## 示範（嚴格遵守此語氣，不需在輸出中重複此段）

TITLE: Kraken 取得聯準會帳戶，首家不依賴中間銀行的加密交易所
IMPORTANCE: 高

SUMMARY:
中心化交易所若要讓客戶以法定貨幣出入金，需要仰賴少數願意服務加密產業的銀行。例如 Silvergate 和 Signature Bank，過去都各自營運全年無休的即時支付網路。2023 年 3 月，這兩家銀行相繼倒閉，交易所一夕之間失去主要清算管道，但願意接手的機構越來越少。

Kraken Financial 上週宣布取得聯準會帳戶，成為美國史上第一家不再依賴任何中間銀行的加密貨幣交易所。Custodia Bank 在拜登政府時期曾申請但被拒絕。Kraken 申請長達五年，直到川普政府在 2025 年簽署行政命令支持加密產業取得銀行服務後，才總算取得聯準會提供的精簡版支付帳戶。
===
TITLE: Visa 與 Bridge 合作，穩定幣發卡開啟 API 新模式
IMPORTANCE: 中

SUMMARY:
市面上的穩定幣 Visa 卡已經不少，EtherFi、RedotPay 都是常見的選擇。但多數穩定幣 Visa 卡背後，都依賴同一家公司 Rain。這家公司持有 Visa 的主要會員資格（Principal Member），負責發卡、以及後續的監管合規。

不過上週 Visa 宣布與 Bridge 合作，開啟另一種新模式。未來如果想發一張穩定幣 Visa 卡，大致有兩條路可以走：找 Rain 是全端模式，簽約後由他們包辦一條龍服務；找 Bridge 則是 API 模式。Bridge 把 Visa 與卡片贊助銀行 Lead Bank 打包成一個 API 介面，讓想發行穩定幣 Visa 卡的公司可以直接串接。
```

**差距二：字數自查指令不夠具體**

目前自查清單寫的是「字數是否在 220 字以內？→ 超過就壓縮」，但沒有說明計算範圍（純漢字？含英文？含標點？）。建議改為：

```
□ 字數確認：數一次摘要的純漢字個數（不含英文字母、數字、標點符號）。
  如果超過 220，優先刪去第二段的「意義說明」句，保留具體事實句。
  不得用省略號代替刪去的內容。
```

**差距三：`auto_draft_multi.md` 結構描述與 `auto_draft.md` 不一致**

`auto_draft.md` 定義的是「兩段結構（固定）」：第一段背景、第二段事實。`auto_draft_multi.md` 改用「三要素順序」：過去狀況 → 現在事件 → 為什麼會這樣。兩套框架實質相容，但措辭不一致，可能讓模型在多則模式下產生略有不同的段落邏輯。建議將 multi 版本改為相同的「兩段結構」描述，在括號中補充三要素對應關係即可。

**差距四：`{LESSONS}` 佔位符過大**

`draft-lessons.md` 目前有 13 個完整案例加上多段外部風格分析，總長超過 8,000 字。每次呼叫都把這份文件完整注入上下文，理論上稀釋了模型對核心規則的注意力。可考慮建立 `prompts/core_rules.md`，精選最常被違反的 15-20 條規則（從各案例的「提取到的規則」段落抽取），取代整份文件的嵌入。原始 `draft-lessons.md` 仍作為 `/feedback` 的輸入，不影響改稿流程。

---

## 三、工作流程架構

### 效率與品質觀察

**問題一（重大）：config.yml 啟用來源全為 YouTube 播客，文字電子報全停**

`config.yml` 目前啟用的 8 個來源中，7 個是 YouTube 頻道（Tokenized Podcast、Lex Fridman、Acquired、When Shift Happens、The Rollup、Empire），1 個是 RSS Podcast（Cheeky Pint）。所有文字新聞來源均已停用：

```yaml
# --- 以下暫時停用 ---
# - name: "Galaxy Research"   (webpage)
# - name: "EthDaily"          (rss, multi_story)
# - name: "Techmeme Crypto"   (webpage)
# - name: "Citation Needed"   (rss)
```

而查看 3/22～3/24 日報，實際使用的來源全部是 The Defiant、a16z crypto、Bankless、Exponential View、Milk Road、Big Technology、TechCrunch 等文字電子報，標注「來源：Gmail 電子報」。這表示日報的主要內容流程是：手動讀 Gmail → 手動 `/digest`，而非 `farm.py` 的自動化路線。自動路線目前只處理 YouTube 逐字稿，且抓取的內容（Lex Fridman、Acquired 等）風格偏技術/商業訪談，與電子報的金融科技快訊定位有落差。

**問題二：YouTube 逐字稿失敗後，URL 被永久標記為已處理**

```python
if not transcript:
    console.print("  [red]✗ 無法取得逐字稿，跳過[/red]")
    seen.add(item.url)  # ← 問題所在：暫時性失敗被永久記錄
    save_seen(seen)
    continue
```

一旦逐字稿抓取失敗（可能是暫時性的網路問題、API 限速或 YouTube 結構變動），該影片 URL 就加入 `seen.json`，之後永遠不再嘗試。建議改用 `failed.json` 記錄失敗次數，超過 3 次才加入 `seen`。

**問題三：討論搜尋依賴 DuckDuckGo HTML 爬取，無 fallback**

`search_web_discussions` 和 `search_x_discussions` 都是直接爬 DuckDuckGo HTML（`https://html.duckduckgo.com/html/`），這個方法有三個已知問題：(1) 容易被 rate limit，連續搜尋多篇文章時尤其明顯；(2) X 推文在 DuckDuckGo 的索引不完整，特別是加密貨幣相關內容；(3) snippet 只有 500 字，有時不足以提取有意義的觀點。3/22 和 3/23 全日無討論，可能正是此處失敗所致。

**問題四：去重機制只比對 URL，無法偵測相同新聞的不同報導**

巴基斯坦太陽能的故事在 3/22 和 3/23 各出現一次，兩篇均來自 Exponential View #566，但若 URL slug 不同，`seen.json` 就無法攔截。建議在去重層加入標題關鍵詞比對（如比較 TF-IDF 相似度或直接比較中文標題的三個主要關鍵詞）。

**問題五：雙 LLM 架構的 keyword 提取步驟成本不相稱**

`extract_search_keywords` 呼叫 OpenAI gpt-4.1-nano，只是為了從中文標題提取 3-6 個英文關鍵字。這個任務不需要 LLM——直接把原始英文標題（`item.title`）傳入搜尋即可，或用簡單的規則提取。可節省一次 API 呼叫和一個外部依賴。

### 建議的新來源或調整

目前 The Defiant、a16z crypto、Exponential View 等都有公開的 Substack/RSS feed，技術上可以加入 `config.yml` 的自動抓取路線。Galaxy Research 週報（`multi_story: true` 模式）若能修復 `article_selector`，也是高品質的加密分析來源。建議先從 The Defiant RSS 開始試驗，因為其 feed 格式標準，且已在日報中被大量引用。

---

## 四、Skill 定義

### 流程銜接問題

**問題一（重大）：/digest SKILL.md 步驟 3 的 Bash 程式碼傳入了錯誤的 client 類型**

SKILL.md 步驟 3 的示範：

```python
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
discussion = generate_discussion(client, title, summary, combined)
```

但 `farm.py` 中 `generate_discussion` 的函數簽名已改為：

```python
def generate_discussion(gemini: genai.Client, title: str, summary: str, search_results: str) -> str | None:
```

第一個參數需要 `genai.Client`（Gemini），不是 `OpenAI`。若按 SKILL.md 的範例執行，會在 API 呼叫層拋出類型錯誤，導致討論搜尋步驟直接失敗。這很可能是 3/22 和 3/23 手動 `/digest` 也沒有討論區塊的另一個可能原因。

建議修正為：
```python
from google import genai
gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
discussion = generate_discussion(gemini_client, title, summary, combined)
```

**問題二：/publish 和 /digest 的 allowed-tools Notion 工具名稱格式可能失效**

`/digest` 的 `allowed-tools` 寫的是 `mcp__claude_ai_Notion__notion-create-pages`，但目前系統中實際可用的 Notion MCP 工具 ID 格式為 `mcp__f8753195-f932-421e-8c57-ed1fcfcc902a__notion-*`。若工具名稱不匹配，Notion 推送步驟將無法執行。`/publish` 同樣使用 `mcp__claude_ai_Notion__*` 格式，需要一併核對。

**問題三：/publish 未說明討論區塊的處理方式**

步驟 2 的輸出格式只有標題和摘要兩段，沒有提及如何處理 Notion「討論」欄位的內容。Substack 發布時是否附上討論？附的話格式如何排版？這個決策未在 SKILL.md 中記錄，每次發布結果可能不一致。

**問題四：/feedback SKILL.md 過度依賴 `stage_feedback.md`**

`/feedback` 的主體幾乎只有 `!cat prompts/stage_feedback.md`，核心流程完全外包給這個檔案。若 `stage_feedback.md` 遺失或路徑改變，整個 skill 就會失效。建議在 SKILL.md 直接寫入核心步驟：(1) 請使用者貼入修改後版本 (2) 對照草稿逐句分析差異 (3) 提取 3-5 條可操作規則 (4) 追加到 `draft-lessons.md`。

**問題五：/digest 步驟 3 的討論搜尋以 Bash 耦合 farm.py 內部 API**

步驟 3 的 Bash block 直接 `from farm import search_web_discussions, ...`，高度耦合於 `farm.py` 的內部函數命名。一旦 `farm.py` 重構，SKILL.md 就會靜默失效。建議在 `farm.py` 加一個 CLI subcommand（如 `python farm.py search --title "..."` ），讓技能呼叫穩定的命令列介面。

---

## 優先順序建議

| 順序 | 改善項目 | 預期效果 | 難度 |
|------|---------|---------|------|
| 1 | 修復 /digest 步驟 3 的 Gemini client 錯誤 | 讓討論搜尋步驟實際可以執行，解決討論區塊長期缺失的根本原因之一 | 低 |
| 2 | 討論搜尋失敗時補充「相關：」背景交叉引用作為 fallback | 讓所有摘要都有討論區塊，符合 CLAUDE.md 強制規範 | 中 |
| 3 | 核對並修正 /digest 和 /publish 的 Notion MCP 工具名稱 | 確保 Notion 推送步驟正常執行 | 低 |
| 4 | auto_draft.md 加入 2 則 few-shot 完整示例 | 提升語氣貼近度，減少括弧短評、結尾方式等細節的偏差 | 低 |
| 5 | 字數自查改為具體計數指令（純漢字 ≤ 220） | 解決多則摘要系統性字數超標問題 | 低 |
| 6 | YouTube 逐字稿失敗改用 failed.json 記錄，不永久加入 seen | 防止暫時性失敗造成內容永久遺漏 | 低 |
| 7 | 去重加入標題關鍵詞比對，防止同一故事多次報導 | 解決巴基斯坦太陽能等重複問題 | 中 |
| 8 | 評估重新啟用 Galaxy Research 或 The Defiant RSS 自動抓取 | 讓 farm.py 實際為日報供稿，降低手動 /digest 負擔 | 高 |
| 9 | 建立 core_rules.md 精簡 {LESSONS} 佔位符 | 降低每次呼叫的 prompt 長度，可能改善摘要一致性 | 中 |
| 10 | 統一 3/22 舊版 HTML 模板為最新版本 | 視覺一致性，讀者連續瀏覽體驗更好 | 低 |

---

*此報告由排程任務自動生成，所有建議需經使用者確認後才執行修改。*
