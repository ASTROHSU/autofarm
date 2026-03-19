"""AutoFarm Web — FastAPI 主程式。"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from web.notion_api import list_articles, get_article, update_article, update_status
from web.feedback import run_feedback, polish_text

BASE_DIR = Path(__file__).parent
LESSONS_FILE = BASE_DIR.parent / "draft-lessons.md"

app = FastAPI(title="AutoFarm")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ---------------------------------------------------------------------------
# 頁面
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/articles")
async def api_list_articles(status: str = "", importance: str = ""):
    articles = list_articles(status, importance)
    return {"articles": articles}


@app.get("/api/articles/{page_id}")
async def api_get_article(page_id: str):
    article = get_article(page_id)
    return article


@app.put("/api/articles/{page_id}")
async def api_update_article(page_id: str, request: Request):
    body = await request.json()
    edited_summary = body.get("summary", "")
    new_status = body.get("status", "")

    # 取得原稿做比對
    original = get_article(page_id)
    original_summary = original["summary"]

    # 更新 Notion
    updated = update_article(page_id, edited_summary, new_status)

    # 如果摘要有改動，觸發 feedback
    feedback_result = None
    if original_summary.strip() != edited_summary.strip():
        feedback_result = run_feedback(
            title=original["title"],
            original=original_summary,
            edited=edited_summary,
        )

    return {
        "article": updated,
        "feedback": feedback_result,
    }


@app.post("/api/articles/batch-status")
async def api_batch_status(request: Request):
    body = await request.json()
    page_ids = body.get("page_ids", [])
    status = body.get("status", "")
    for pid in page_ids:
        update_status(pid, status)
    return {"updated": len(page_ids)}


@app.post("/api/articles/{page_id}/polish")
async def api_polish_article(page_id: str, request: Request):
    body = await request.json()
    user_text = body.get("text", "")
    previous_ai_text = body.get("previous_ai_text", "")

    # 讀取 lessons
    lessons = ""
    if LESSONS_FILE.exists():
        lessons = LESSONS_FILE.read_text(encoding="utf-8")

    # 如果使用者有改動（vs 上一次 AI 版本），先學習
    feedback_result = None
    if previous_ai_text and previous_ai_text.strip() != user_text.strip():
        article = get_article(page_id)
        feedback_result = run_feedback(
            title=article["title"],
            original=previous_ai_text,
            edited=user_text,
        )
        # 重新讀取 lessons（剛更新過）
        lessons = LESSONS_FILE.read_text(encoding="utf-8")

    # AI 潤稿
    polished = polish_text(user_text, lessons)

    return {
        "polished": polished,
        "feedback": feedback_result,
    }


@app.get("/api/rules")
async def api_get_rules():
    if LESSONS_FILE.exists():
        content = LESSONS_FILE.read_text(encoding="utf-8")
    else:
        content = ""
    return {"content": content}


@app.post("/api/publish")
async def api_publish():
    articles = list_articles(status="待發布")
    if not articles:
        return {"draft": "沒有待發布的文章。"}

    parts = []
    for a in articles:
        summary = a["summary"].replace("<br><br>", "\n\n").replace("<br>", "\n")
        discussion = a.get("discussion", "").replace("<br><br>", "\n\n").replace("<br>", "\n").strip()
        section = f"## {a['title']}\n\n{summary}"
        if discussion:
            section += f"\n\n{discussion}"
        parts.append(section)

    draft = "\n\n---\n\n".join(parts)
    return {"draft": draft, "count": len(articles)}


# ---------------------------------------------------------------------------
# 啟動
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
