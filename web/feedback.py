"""Feedback 模組：比對 AI 原稿與使用者修改版，提取規則並更新 draft-lessons.md。"""

import os
from datetime import date
from pathlib import Path
from openai import OpenAI
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
    """呼叫 LLM 分析兩版本差異，回傳分析結果。"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = FEEDBACK_PROMPT.format(original=original, edited=edited)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


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
