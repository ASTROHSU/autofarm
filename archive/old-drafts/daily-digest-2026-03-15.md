# 每日資訊彙整｜2026.03.15（六）

來源：Gmail 電子報 + X 動態牆 + Facebook
涵蓋時間：3/14 ~ 3/15

---

## Tech / AI

### [Anthropic 與五角大廈的對峙浮上檯面](https://www.newyorker.com/)

[Anthropic](https://www.anthropic.com/) 是七名 OpenAI 離職員工創立的 AI 公司，一直強調安全與負責任的 AI 開發。他們拒絕讓五角大廈將 [Claude](https://claude.ai/) 用於完全自主武器或大規模監控，這在 AI 業界算是罕見的硬立場。

不過事情的發展頗為諷刺：國防部長 Hegseth 因此將 Anthropic 列為「供應鏈風險」並從聯邦系統中封鎖，但據報導隔天就在伊朗攻擊的目標選定中使用了 Claude。[The New Yorker 本週刊出的長篇報導](https://mail.google.com/mail/u/0/#all/19cec474bf035f38)，揭露了這場合約談判背後的拉鋸。

### [Claude Code 春假活動：非尖峰時段使用量加倍](https://x.com/pirrer/status/2033042582553727319)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) 是 Anthropic 的命令列開發工具，月費 $100 起，使用量一直是開發者在意的問題。不少人反映用量常常不到一半就觸頂，也有人因此考慮升級到 [$200 的 Max 方案](https://x.com/freeshiuan/status/2033033394284826649)。

Anthropic 宣布 3 月 13 日到 27 日的「春假」活動，非尖峰時段（美東下午 2 點到隔天早上 8 點）使用量上限加倍，週末則全天加倍。這背後的邏輯是：Claude Code 的用量集中在美國白天，離峰時段的算力本來就有餘裕。

### [ERC-8183：鏈上 AI Agent 商務的新標準草案](https://mail.google.com/mail/u/0/#all/19cec731070c890f)

AI Agent 之間要在鏈上做交易，目前沒有共通的基礎設施，每個平台各搞一套託管邏輯，導致聲譽和交易紀錄被鎖在各自的圍牆花園裡。[Virtuals Protocol](https://www.virtuals.io/) 和[以太坊基金會](https://ethereum.foundation/)的 dAI 團隊看到了這個問題。

兩方合作提出了 [ERC-8183](https://eips.ethereum.org/EIPS/eip-8183) 草案，核心是一個「Job」原語：Client 發出任務 + 託管付款，Provider 執行後交付，Evaluator（可以是 AI 裁判、DAO 或 ZK 驗證器）確認後自動放款。這個標準還能跟 [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) 的 Agent 身份系統搭配，讓每筆完成的 Job 變成可攜帶的鏈上聲譽訊號。

### [x402 願望清單：五個值得打造的微支付產品](https://mail.google.com/mail/u/0/#all/19cec731070c890f)

[x402](https://www.x402.org/) 是把加密貨幣微支付整合進 HTTP 協定的機制，讓 AI Agent 可以用「按次付費」的方式取用各種 API 和資料來源。概念很美，但到目前為止實際應用還不多，還在等殺手級產品出現。

[Bankless Mindshare 週報](https://mail.google.com/mail/u/0/#all/19cec731070c890f)列出了五個他們認為最有潛力的方向：Skills 技能市場端點、生態系新聞聚合、開發者活動追蹤、媒體預測績效評分、以及安全審計追蹤器。核心觀點是：x402 最適合「有人把碎片化資料整合成有價值的東西」這種場景，策展者吃一次整合成本，呼叫者按次付費。

### [RentAHuman.ai 的「AI 僱用人類」被踢爆是場空氣](https://x.com/hosseeb/status/2033003455150002656)

[RentAHuman.ai](https://rentahuman.ai/) 前陣子爆紅，號稱讓 AI 在平台上發布賞金任務、僱用人類來完成。這個概念之所以吸引眼球，是因為它翻轉了「人類僱用 AI」的敘事，聽起來像是 AGI 時代的預兆。

[Dragonfly](https://www.dragonfly.xyz/) 合夥人 [Haseeb](https://x.com/hosseeb/status/2033003455150002656) 指出，這個 vibe coded 的應用程式不但洩漏了資料庫認證，實際資料更顯示 11,023 筆賞金中只有 13 筆真的被兌現過。所謂「AI 在僱用人類」，其實絕大多數都是 AI bot 在自己跟自己玩。

---

## Crypto / Web3

### [$5,000 萬穩定幣一筆交易變成 $36,000 的 AAVE](https://thedefiant.io/news/defi/whale-swaps-usd50-million-in-stablecoins-for-just-usd36-000-of-aave)

DeFi 交易介面的使用者體驗一直是個問題，但通常大家討論的是手續費或確認速度，很少有人想到「滑價」能嚴重到幾乎歸零。[Aave](https://aave.com/) 創辦人 [Stani Kulechov](https://x.com/StaniKulechov/status/2032960303613325687) 證實，這名交易者在收到極端滑價警告後仍然確認了交易。

具體來說：一名不明身份的錢包透過 Aave 介面、經由 [CoW Protocol](https://cow.fi/) 支援的前端，將 $5,040 萬 USDT 換成了僅值 $36,000 的 AAVE 代幣——99% 以上的價值在一次交易中蒸發。[CoW DAO 已發布事後檢討報告](https://x.com/CoWSwap/status/2032959625054634334)，這起事件也讓社群重新討論 DeFi 前端是否該設計更強的防呆機制。

### [以太坊基金會發布「EF Mandate」引發社群爭議](https://x.com/BillHughesDC/status/2032815114911457601)

[以太坊基金會](https://ethereum.foundation/)（EF）一直是以太坊生態中最特殊的存在：不是擁有者，不是統治者，自我定位為「管家」。但過去幾年社群對 EF 的批評越來越多，認為他們產出太多意識形態文件、太少實際行動。

本週 EF 發布了新的「Mandate」文件，宣示以抗審查、開源、隱私、安全（CROPS）為核心願景。[Bankless 的 David Hoffman](https://mail.google.com/mail/u/0/#all/19ced1ad1fd02720) 直言他對這類文件已經疲乏，擔心這代表 EF 放棄了「極大化以太坊價值」的路線，回到只做硬核密碼龐克的東西。[Bill Hughes 則認為](https://x.com/BillHughesDC/status/2032815114911457601) EF 的強大來自一群互相競爭又互補的管理者網絡，而非單一機構。

### [BlackRock 推出 ETHB 質押 ETH ETF，首日進帳 $4,300 萬](https://thedefiant.io/news/tradfi-and-fintech/blackrock-ethb-staked-etf-day-one-trading-usd43m-inflows)

[BlackRock](https://www.blackrock.com/) 的 iShares 比特幣 ETF 已經是市場上規模最大的加密 ETF，但以太坊 ETF 的進展一直相對緩慢。差別在於：比特幣 ETF 只需要持有 BTC，以太坊 ETF 如果能加上質押收益，對機構投資人的吸引力會大幅提升。

BlackRock 本週在 [Nasdaq](https://www.nasdaq.com/) 上市了 iShares Staked Ethereum Trust ETF（代號 ETHB），首日就吸引了 $4,300 萬的資金流入。同一時間，以太坊基金會也宣布使用 [DVT-lite 技術](https://ethereum.org/en/staking/dvt/) 質押了 72,000 顆 ETH，等於用行動表態支持質押生態的去中心化。

### [以太坊基金會再度 OTC 出售 5,000 ETH](https://x.com/EmberCN/status/2032977182608470186)

以太坊基金會的賣幣一直是社群敏感話題，每次大額出售都會引發「基金會不看好 ETH」的猜測。去年七月他們就曾以 OTC 方式賣幣給財庫公司，這次又來了。

凌晨時段，EF 以每顆 $2,043 的價格，透過 OTC 將 5,000 ETH（約 $1,021 萬）賣給 [BitMNR](https://bitmnr.com/)。同時根據 [ultrasoundmoney](https://ultrasound.money/) 的資料，自 Merge 以來以太坊的流通供應量已增加超過 100 萬顆 ETH，[年化通膨率約 0.24%](https://x.com/WuBlockchain/status/2033040598161306110)，「超音波貨幣」的敘事持續承壓。

### [CLARITY 法案若四月底前未過委員會，2026 年通過機率極低](https://x.com/intangiblecoins/status/2032819073479045281)

CLARITY 是美國國會針對穩定幣監管的立法提案，目前的爭議焦點在穩定幣的定義與監管框架。加密產業一直將這項法案視為最有可能在本屆國會通過的友善立法之一。

[Galaxy Research](https://www.galaxy.com/research/) 的 [Alex Thorn](https://x.com/intangiblecoins/status/2032819073479045281) 指出，如果 CLARITY 在四月底前沒能通過委員會，2026 年通過的機率會變得極低。這件事必須在五月初上參議院會議，而會議上討論的時間所剩無幾，每過一天通過的機率就在下降。

### [加密借貸市場從高點縮減 36%](https://x.com/artemis/status/2032819073479045281)

DeFi 借貸在去年十月達到高峰，當時主要協議的存款總額約 $1,250 億。這波成長主要由槓桿需求驅動，跟整體加密市場的投機氛圍高度相關。

自十月以來，存款已降至 $796 億，縮減 36%。降幅集中在幾個大協議：[Aave](https://aave.com/) 減少 $276 億、[Spark](https://spark.fi/) 減少 $54 億、[Euler](https://euler.finance/) 減少 $26 億、[Fluid](https://fluid.instadapp.io/) 減少 $24 億。[Ethena](https://ethena.fi/) 的部署資本同樣下滑，槓桿需求明顯退潮。

---

## 國際金融 / 市場

### [加密市場因伊朗局勢升溫而回吐漲幅](https://thedefiant.io/news/markets/crypto-rally-fizzles-on-iran-escalation-fears)

全球市場本週原本在反彈軌道上，比特幣一度觸及 $74,000，多數風險資產走高。地緣政治緊張看似已被市場消化，避險情緒暫時退場。

但週五傳出五角大廈正向中東增派兵力和軍艦，暗示對伊朗衝突可能升級，加密市場隨即回吐大部分漲幅。值得注意的是，這波避險中傳統的安全資產表現也不正常——石油飆升、黃金反而沒撐住、債券遭拋售，只有美元承接了避險資金。

### [CFTC 啟動預測市場全面審查](https://thedefiant.io/news/regulation/cftc-launches-sweeping-review-of-prediction-markets)

預測市場（如 [Polymarket](https://polymarket.com/)）在去年美國大選期間爆紅，但監管框架一直模糊不清。[CFTC](https://www.cftc.gov/) 過去對預測市場的態度搖擺不定，有時允許、有時打壓，業者需要更明確的規則。

CFTC 本週發布了「預先提議規則制定通知」（ANPRM），公開徵求意見，探討現有衍生品法律應如何適用於預測市場。同時市場監督部門也發布了交易所指引。這是 CFTC 首次以如此全面的方式處理預測市場，對 Polymarket 等平台的合規前景影響重大。

---

*Facebook 動態牆因技術限制僅載入一則貼文（Jing Fang Chen），內容為一般社群分享，無科技/金融相關討論，故未納入本次彙整。*
