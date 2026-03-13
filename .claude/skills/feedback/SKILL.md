---
name: feedback
description: 對照 Claude 草稿與使用者修改版，提取寫作偏好規則並更新 draft-lessons.md
argument-hint: （選填：直接貼入你修改後的最終版本）
allowed-tools: Read, Edit
---

!`cat prompts/stage_feedback.md`

---

請先讀取 draft-lessons.md 了解目前已累積的規則：

!`cat draft-lessons.md`

---

$ARGUMENTS 若使用者已貼入修改後的版本，直接開始分析。若沒有，詢問：「請把你修改後的最終版本貼在這裡。」
