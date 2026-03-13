---
name: parse
description: 解析 NotebookLM 研究報告，提取結構化事實清單與兩份讀者清單
argument-hint: （選填：直接貼入報告內容）
allowed-tools: Read
---

!`cat prompts/stage1_parse.md`

---

$ARGUMENTS 若使用者已貼入報告內容，直接開始解析。若沒有，詢問：「請把 NotebookLM 產出的報告貼在這裡。」
