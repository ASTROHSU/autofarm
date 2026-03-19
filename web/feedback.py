"""Feedback 模組：比對 AI 原稿與使用者修改版，提取規則並更新 draft-lessons.md。"""

import os
from datetime import date
from pathlib import Path
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

load_dotenv()

LESSONS_FILE = Path(__file__).parent.parent / "draft-lessons.md"

FEEDBACK_PROMPT = """你是一位繁體中文新聞編輯的寫作教練。

使用者已修改了 AI 產出的新聞摘要。請比對兩個版本，分析差異並提取可操作的規則。

## AI 原稿
{original}

## 使用者修改版
{edited}

## 輸出格式

請用以下格式輸出：

### 差異分析

| AI 原稿片段 | 使用者修改 | 學到的規則 |
|---|---|---|
| （逐項列出每個改動） | （對應的修改） | （可操作的規則） |

### 提取到的規則

（列出所有可在下次寫稿時直接套用的規則，每條一行，用 - 開頭）

注意：
- 不評論修改好不好，只客觀分析差異
- 規則要具體可操作，例如「避免用 X，改用 Y」
- 如果有多次出現的模式，優先提取
- 使用台灣繁體中文
"""


def analyze_diff(original: str, edited: str) -> str:
    """呼叫 Gemini 分析兩版本差異，回傳分析結果。"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = FEEDBACK_PROMPT.format(original=original, edited=edited)
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.7,
            thinking_config=genai_types.ThinkingConfig(thinking_budget=2048),
        ),
    )
    return response.text or ""


def append_to_lessons(title: str, original: str, edited: str, analysis: str) -> None:
    """將這次的 feedback 記錄追加到 draft-lessons.md。"""
    today = date.today().isoformat()
    entry = f"""

---

## 案例：{title}（{today}，前端 feedback）

---

### AI 潤飾版 vs 使用者定稿

{analysis}

"""
    with open(LESSONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def run_feedback(title: str, original: str, edited: str) -> str:
    """完整 feedback 流程：分析 + 寫入 lessons。回傳分析結果。"""
    if original.strip() == edited.strip():
        return "原稿與修改版相同，無差異。"

    analysis = analyze_diff(original, edited)
    append_to_lessons(title, original, edited, analysis)
    return analysis


# ---------------------------------------------------------------------------
# AI 潤稿
# ---------------------------------------------------------------------------

POLISH_PROMPT = """你是一位繁體中文新聞編輯。使用者正在修改一則新聞摘要，請幫他修順。

## 已學到的寫作偏好

{lessons}

## 撰寫規範

- 字數：120～220 字（兩段合計，嚴格不超過 220 字）
- 格式：純文字，無小標題，無條列式清單
- 段落：固定兩段，每段 2～4 句
- 語氣：隱形第一人稱，像是跟懂行的朋友說明
- 不使用加粗
- 嚴格使用台灣繁體中文（使用者→O、用戶→X、網路→O、網絡→X）
- 禁止分析性收尾（「此舉或將...」「進一步推動...」「顯示出...」→ 全刪）
- 禁止制式開頭（「隨著...的發展」「近年來」）
- 結尾是事實或觀察，不是結論

## 使用者目前的版本

{user_text}

## 注意

- 保留使用者的觀點和資訊選擇，只修順文字
- 不要加入使用者沒有的資訊
- 不要改變段落結構（維持兩段）
- 修順的重點是：語氣、用字、句子節奏、中文語感
- 只輸出修順後的版本，不需要解釋或標注改了什麼
"""


def polish_text(user_text: str, lessons: str) -> str:
    """呼叫 Gemini 潤稿，回傳修順後的文字。"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = POLISH_PROMPT.format(user_text=user_text, lessons=lessons)
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.7,
            thinking_config=genai_types.ThinkingConfig(thinking_budget=4096),
        ),
    )
    return (response.text or "").strip()
