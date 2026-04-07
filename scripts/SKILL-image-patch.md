# SKILL.md 修改：新增「第四步半：取得新聞配圖」

在第四步（製作圖表）和第五步（整理社群討論）之間，插入以下段落：

---

## 第四步半：取得新聞配圖（必做）

每則 importance_score ≥ 8 的新聞都必須有配圖。使用 `scripts/fetch-image.py` 執行三層 fallback 策略：

```bash
python scripts/fetch-image.py --feed docs/feed.json --threshold 8
```

### 三層策略

1. **Open Graph image（og:image）：** 從新聞來源 URL 的 HTML meta tag 取得。零成本、速度最快。
2. **文章內第一張圖片：** 解析文章 HTML，找 `<article>` 或 `<main>` 區塊內第一張寬度 ≥ 400px 的 `<img>`。會自動跳過 logo、avatar、icon。
3. **Gemini API 生圖（fallback）：** 前兩層都失敗時，根據標題和摘要呼叫 Gemini API 生成 16:9 橫式配圖，存到 `docs/images/` 目錄。需要 `GEMINI_API_KEY` 環境變數。

### 生圖 prompt 原則

- 風格：乾淨、現代的編輯式插圖（editorial illustration）
- 色調：低飽和，不刺眼
- 不要在圖片中放任何文字
- 用抽象或象徵性的方式表達主題，不要太字面
- 橫式 16:9

### 注意事項

- 已有圖片的項目會自動跳過（除非加 `--force`）
- Gemini 生成的圖片存在 `docs/images/` 目錄，image 欄位填本地路徑
- 每次請求之間間隔 1 秒，避免被來源網站擋
- 如果三層都失敗，該項目不填 image 欄位（不會硬塞一張 logo 充數）

---

同時在第七步（推送到 GitHub）的 cp 指令中加上 images 目錄：

```bash
# 如果有 Gemini 生成的圖片，一起複製過去
if [ -d /Users/staarrr/autofarm/docs/images ]; then
  cp -r /Users/staarrr/autofarm/docs/images docs/images
fi
```

git add 也要加上 `docs/images/`：

```bash
git add docs/feed.json docs/feed.js docs/index.html docs/images/
```
