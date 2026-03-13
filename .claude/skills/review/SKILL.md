---
name: review
description: 對兩段式摘要進行語言審核（台灣用語 + 語氣一致性）
argument-hint: （選填：指定特別要注意的審核方向）
allowed-tools: Read
---

!`cat prompts/stage4_review.md`

---

$ARGUMENTS 審核目前對話中的兩段式摘要，完成後如有需要修正，直接輸出修正後的完整版本。
