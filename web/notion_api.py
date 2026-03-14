"""Notion API 封裝：讀寫 AutoFarm 新聞摘要資料庫。"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_VERSION = "2022-06-28"

STATUS_OPTIONS = ["待審閱", "已發布", "略過"]


def _headers() -> dict:
    if not NOTION_API_KEY:
        raise RuntimeError("缺少 NOTION_API_KEY")
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _extract_text(rich_text_list: list) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def _page_to_dict(page: dict) -> dict:
    props = page["properties"]
    return {
        "id": page["id"],
        "title": _extract_text(props.get("標題", {}).get("title", [])),
        "summary": _extract_text(props.get("摘要", {}).get("rich_text", [])),
        "discussion": _extract_text(props.get("討論", {}).get("rich_text", [])),
        "source": (props.get("來源", {}).get("select") or {}).get("name", ""),
        "status": (props.get("狀態", {}).get("select") or {}).get("name", ""),
        "url": props.get("原文連結", {}).get("url", ""),
        "processed": (props.get("處理日期", {}).get("date") or {}).get("start", ""),
        "published": (props.get("發布日期", {}).get("date") or {}).get("start", ""),
    }


def list_articles(status: str = "") -> list[dict]:
    """從 Notion 拉文章列表，可按狀態篩選。"""
    body = {
        "sorts": [{"property": "處理日期", "direction": "descending"}],
        "page_size": 50,
    }
    if status and status in STATUS_OPTIONS:
        body["filter"] = {
            "property": "狀態",
            "select": {"equals": status},
        }

    resp = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=_headers(),
        json=body,
    )
    resp.raise_for_status()
    return [_page_to_dict(p) for p in resp.json()["results"]]


def get_article(page_id: str) -> dict:
    """取得單篇文章。"""
    resp = requests.get(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_headers(),
    )
    resp.raise_for_status()
    return _page_to_dict(resp.json())


def update_status(page_id: str, status: str) -> None:
    """只更新文章狀態。"""
    if status not in STATUS_OPTIONS:
        return
    requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_headers(),
        json={"properties": {"狀態": {"select": {"name": status}}}},
    ).raise_for_status()


def update_article(page_id: str, summary: str, status: str = "") -> dict:
    """更新文章摘要，可選更新狀態。"""
    properties = {
        "摘要": {"rich_text": [{"text": {"content": summary[:2000]}}]},
    }
    if status and status in STATUS_OPTIONS:
        properties["狀態"] = {"select": {"name": status}}

    resp = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_headers(),
        json={"properties": properties},
    )
    resp.raise_for_status()
    return get_article(page_id)
