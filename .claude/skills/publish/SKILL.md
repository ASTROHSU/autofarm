---
name: publish
description: 從 Notion 撈出本週「已發布」條目，排版成可直接貼上 Substack 的電子報草稿
argument-hint: （無需參數，直接執行）
allowed-tools: mcp__claude_ai_Notion__search, mcp__claude_ai_Notion__fetch, mcp__claude_ai_Notion__query_data_sources
---

# /publish 流程

你是一位繁體中文新聞編輯，負責把本週審閱完成的新聞摘要整理成電子報草稿。

## 步驟 1：查詢 Notion

用 `mcp__claude_ai_Notion__fetch` 查詢資料庫：
- data_source_id: `f3138b3f-bc33-4f71-8ef6-8d78b73a6e96`
- 過濾條件：狀態 = 「已發布」
- 排序：發布日期由舊到新（或處理日期由舊到新）

如果有多筆，全部抓出來。

## 步驟 2：排版輸出

格式如下，每篇之間用 `---` 分隔：

```
## [標題]

[摘要第一段]

[摘要第二段]

---

## [下一篇標題]

...
```

**規則：**
- 純文字，不加粗、不加底線
- 標題用 `##`，Substack 會渲染成 H2
- 摘要直接貼，不加任何前言（不寫「本週共 X 則」「以下是本週新聞」等）
- 最後一篇後面不加 `---`

## 步驟 3：詢問是否要標記為「已整合」

輸出草稿後，問使用者：「要把這批條目的狀態更新為其他標記嗎？」（視使用者 Notion 設計而定，目前可略過此步驟）

## 注意

- 嚴格使用台灣繁體中文，禁用簡中詞彙（見 CLAUDE.md 規範）
- 直接輸出草稿，不要加任何說明或前言
