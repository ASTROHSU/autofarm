#!/usr/bin/env python3
"""
AutoFarm - 自動化新聞摘要 Pipeline
用法：python farm.py --run [--dry-run] [--limit N] [--source NAME]
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

from email.utils import parsedate_to_datetime
import feedparser
import requests
import yaml
from openai import OpenAI
from google import genai
from google.genai import types as genai_types
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from notion_client import Client as NotionClient

load_dotenv()
console = Console()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
SEEN_FILE = DATA_DIR / "seen.json"
PROMPT_FILE = BASE_DIR / "prompts" / "auto_draft.md"
PROMPT_MULTI_FILE = BASE_DIR / "prompts" / "auto_draft_multi.md"
LESSONS_FILE = BASE_DIR / "draft-lessons.md"
CONFIG_FILE = BASE_DIR / "config.yml"
PENDING_FILE = DATA_DIR / "pending.json"
PROMPT_DISCUSSION_FILE = BASE_DIR / "prompts" / "auto_discussion.md"
X_FOLLOWING_FILE = DATA_DIR / "x_following.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Item:
    def __init__(self, title: str, url: str, content: str, source: str, published: str):
        self.title = title
        self.url = url
        self.content = content
        self.source = source
        self.published = published


# ---------------------------------------------------------------------------
# Seen URL tracking
# ---------------------------------------------------------------------------

def load_seen() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(seen: set) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Pending items (for Notion MCP push)
# ---------------------------------------------------------------------------

def load_pending() -> list:
    if PENDING_FILE.exists():
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    return []


def save_pending(items: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

MAX_AGE_DAYS = 7
MAX_WEBPAGE_ITEMS = 3
MAX_YOUTUBE_ITEMS = 5


def is_recent_entry(entry, max_days: int = MAX_AGE_DAYS) -> bool:
    """檢查 feedparser entry 是否在 max_days 天內。"""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return True  # 無日期資訊，保留
    try:
        entry_time = datetime(parsed[0], parsed[1], parsed[2],
                              parsed[3], parsed[4], parsed[5])
        cutoff = datetime.now() - timedelta(days=max_days)
        return entry_time >= cutoff
    except (ValueError, TypeError):
        return True


def fetch_rss(source: dict) -> list[Item]:
    """抓取 RSS feed，回傳 Item 清單（只保留過去 7 天內的文章）。"""
    feed = feedparser.parse(source["url"])
    items = []
    for entry in feed.entries:
        if not is_recent_entry(entry):
            continue
        url = entry.get("link", "")
        if not url:
            continue
        title = entry.get("title", "")
        published = entry.get("published", entry.get("updated", ""))
        # 嘗試從 summary 或 content 拿全文
        content = ""
        if hasattr(entry, "content"):
            content = entry.content[0].get("value", "")
        if not content:
            content = entry.get("summary", "")
        # 如果 RSS 內文太短（< 200 字），嘗試抓原文
        if len(content) < 200:
            content = fetch_article_content(url) or content

        # 如果來源標記為 multi_story，拆分成多則
        if source.get("multi_story"):
            sub_items = split_digest(content, url, source["name"], published)
            items.extend(sub_items)
        else:
            items.append(Item(title=title, url=url, content=content,
                              source=source["name"], published=published))
    return items


def split_digest(html_content: str, base_url: str, source: str,
                 published: str) -> list[Item]:
    """將 digest 類文章（如 EthDaily）按 h2 拆成多則 Item。"""
    soup = BeautifulSoup(html_content, "html.parser")
    skip_sections = {"quick take", "sponsored by", "other news", "sponsored"}
    skip_content_patterns = ["listen to this episode", "spotify"]
    items = []
    seen_titles = set()

    for h2 in soup.find_all("h2"):
        section_title = h2.get_text(strip=True)
        if not section_title or section_title.lower() in skip_sections:
            continue

        # 收集 h2 到下一個 h2 之間的所有內容
        parts = []
        for sib in h2.find_next_siblings():
            if sib.name == "h2":
                break
            text = sib.get_text(strip=True)
            if text:
                parts.append(text)
        body = "\n".join(parts)

        if len(body) < 200 or section_title in seen_titles:
            continue
        # 跳過 podcast/audio 嵌入區塊
        if any(p in body.lower() for p in skip_content_patterns):
            continue
        seen_titles.add(section_title)

        # 提取區塊內第一個外部連結作為原始來源 URL
        story_url = base_url
        for sib in h2.find_next_siblings():
            if sib.name == "h2":
                break
            for a in sib.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") and base_url not in href:
                    story_url = href
                    break
            if story_url != base_url:
                break

        items.append(Item(
            title=section_title,
            url=story_url,
            content=body,
            source=source,
            published=published,
        ))

    return items


def fetch_webpage(source: dict) -> list[Item]:
    """抓取網頁文章清單，回傳 Item 清單。"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoFarm/1.0)"}
    try:
        resp = requests.get(source["url"], headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]抓取失敗 {source['name']}: {e}[/red]")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    selector = source.get("article_selector", "article a")
    links = soup.select(selector)

    items = []
    seen_urls = set()
    for tag in links:
        href = tag.get("href", "")
        if not href or href.startswith("?"):
            continue
        # 補全相對 URL
        if href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(source["url"])
            href = f"{parsed.scheme}://{parsed.netloc}{href}"
        if href in seen_urls:
            continue
        seen_urls.add(href)
        title = tag.get_text(strip=True) or href
        content = fetch_article_content(href) or ""
        items.append(Item(title=title, url=href, content=content,
                          source=source["name"], published=""))
        if len(items) >= MAX_WEBPAGE_ITEMS:
            break
    return items


def fetch_youtube(source: dict) -> list[Item]:
    """抓取 YouTube 頻道最新影片清單。"""
    channel_id = source.get("channel_id", "")
    if not channel_id:
        console.print(f"[red]{source['name']}：缺少 channel_id[/red]")
        return []

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]YouTube 頻道抓取失敗: {e}[/red]")
        return []

    # 解析 videoId 和 title（從頁面 JSON 資料中）
    video_ids = re.findall(r'"videoId":"([^"]+)"', resp.text)
    titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]*)"', resp.text)

    # 去重並保持順序
    seen_ids = set()
    items = []
    for vid, title in zip(video_ids, titles):
        if vid in seen_ids:
            continue
        seen_ids.add(vid)
        video_url = f"https://www.youtube.com/watch?v={vid}"
        items.append(Item(
            title=title,
            url=video_url,
            content="",  # 之後由 transcript 填充
            source=source["name"],
            published="",
        ))
        if len(items) >= MAX_YOUTUBE_ITEMS:
            break

    return items


def fetch_youtube_transcript(video_id: str) -> str | None:
    """用 youtube-transcript-api 取得影片逐字稿。"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id, languages=["en"])
        text = " ".join(seg.text for seg in transcript)
        return text[:30000]
    except Exception as e:
        console.print(f"  [dim]逐字稿取得失敗: {e}[/dim]")
        # fallback: 抓影片頁面 description
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoFarm/1.0)"}
            resp = requests.get(
                f"https://www.youtube.com/watch?v={video_id}",
                headers=headers, timeout=15)
            desc_match = re.search(
                r'"shortDescription":"(.*?)"', resp.text)
            if desc_match:
                desc = desc_match.group(1).replace("\\n", "\n")
                return desc[:30000]
        except Exception:
            pass
        return None


def fetch_article_content(url: str) -> str | None:
    """抓取文章全文（純文字）。"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoFarm/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    # 移除 script / style / nav / footer
    for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
        tag.decompose()

    # 優先找 article 或 main 標籤
    body = soup.find("article") or soup.find("main") or soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # 壓縮連續空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:30000]  # 截斷，避免 token 過多


# ---------------------------------------------------------------------------
# LLM API
# ---------------------------------------------------------------------------

def load_lessons() -> str:
    if LESSONS_FILE.exists():
        return LESSONS_FILE.read_text(encoding="utf-8")
    return "（尚無改稿記錄）"


def load_prompt_template(multi: bool = False) -> str:
    path = PROMPT_MULTI_FILE if multi else PROMPT_FILE
    return path.read_text(encoding="utf-8")


def _build_prompt(item: Item, lessons: str, multi: bool = False) -> str:
    template = load_prompt_template(multi=multi)
    return (
        template
        .replace("{LESSONS}", lessons)
        .replace("{SOURCE}", item.source)
        .replace("{ARTICLE_TITLE}", item.title)
        .replace("{URL}", item.url)
        .replace("{PUBLISHED}", item.published or "未知")
        .replace("{CONTENT}", item.content[:25000])
    )


def call_llm(gemini: genai.Client, item: Item, lessons: str,
             multi: bool = False) -> str:
    """呼叫 Gemini API 產生摘要，回傳原始輸出。"""
    prompt = _build_prompt(item, lessons, multi=multi)
    response = gemini.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.7,
            thinking_config=genai_types.ThinkingConfig(thinking_budget=4096),
        ),
    )
    return response.text or ""


def parse_output(output: str) -> dict | None:
    """從 LLM 輸出解析單則 title、importance 和 summary。"""
    title_match = re.search(r"^TITLE:\s*(.+)$", output, re.MULTILINE)
    summary_match = re.search(r"^SUMMARY:\s*\n([\s\S]+)$", output, re.MULTILINE)

    if not title_match or not summary_match:
        return None

    importance_match = re.search(r"^IMPORTANCE:\s*(.+)$", output, re.MULTILINE)
    importance = importance_match.group(1).strip() if importance_match else "中"
    if importance not in ("高", "中", "低"):
        importance = "中"

    return {
        "title": title_match.group(1).strip(),
        "summary": summary_match.group(1).strip(),
        "importance": importance,
    }


def parse_multi_output(output: str) -> list[dict]:
    """從 LLM 輸出解析多則 STORY 區塊。"""
    stories = re.split(r"={3,}", output)
    results = []
    for chunk in stories:
        result = parse_output(chunk)
        if result:
            results.append(result)
    return results


def generate_summary(gemini: genai.Client, item: Item, lessons: str) -> dict | None:
    """產生單則摘要，回傳 {title, summary} 或 None。"""
    try:
        output = call_llm(gemini, item, lessons)
        result = parse_output(output)
        if not result:
            console.print(f"[yellow]⚠ 解析失敗，原始輸出：\n{output[:300]}[/yellow]")
        return result
    except Exception as e:
        console.print(f"[red]API 錯誤: {e}[/red]")
        return None


def generate_multi_summary(gemini: genai.Client, item: Item,
                           lessons: str) -> list[dict]:
    """產生多則摘要，回傳 [{title, summary}, ...] 或空清單。"""
    try:
        output = call_llm(gemini, item, lessons, multi=True)
        results = parse_multi_output(output)
        if not results:
            console.print(f"[yellow]⚠ 多則解析失敗，原始輸出：\n{output[:300]}[/yellow]")
        return results
    except Exception as e:
        console.print(f"[red]API 錯誤: {e}[/red]")
        return []


# ---------------------------------------------------------------------------
# Discussion search & generation
# ---------------------------------------------------------------------------

def extract_search_keywords(client: OpenAI, title: str,
                            original_title: str = "") -> str:
    """用 LLM 從摘要標題提取英文搜尋短語。"""
    context = f"Original English title: {original_title}\n" if original_title else ""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            max_tokens=50,
            messages=[{"role": "user", "content": (
                f"Extract a concise English search phrase (3-6 words) from "
                f"this news title for finding related discussions on "
                f"Twitter/X and Reddit. Include proper nouns and key terms. "
                f"Do NOT include dollar signs ($). "
                f"Return ONLY the phrase, nothing else.\n\n"
                f"{context}"
                f"Title: {title}"
            )}],
        )
        return response.choices[0].message.content.strip().strip('"')
    except Exception:
        return title


def search_web_discussions(keywords: str) -> list[dict]:
    """用 DuckDuckGo HTML 搜尋相關討論。回傳 [{title, snippet, url}, ...]。"""
    results = []
    # 移除特殊字元避免搜尋引擎問題
    clean_kw = keywords.replace("$", "").replace("#", "")
    queries = [
        f"{clean_kw} crypto",
        f"site:reddit.com {clean_kw}",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    }

    for query in queries:
        try:
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".result"):
                a = item.select_one(".result__a")
                if not a:
                    continue
                href = a.get("href", "")
                # 從 DDG 重定向 URL 中提取實際 URL
                if "uddg=" in href:
                    parsed_qs = urllib.parse.parse_qs(
                        urllib.parse.urlparse(href).query)
                    href = parsed_qs.get("uddg", [href])[0]
                text = a.get_text(strip=True)
                snippet_el = item.select_one(".result__snippet")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                results.append({
                    "title": text,
                    "snippet": snippet[:300],
                    "url": href,
                    "source": "Web",
                })
                if len(results) >= 10:
                    break
        except Exception:
            continue

    return results


def get_x_user_id(username: str, bearer_token: str) -> str | None:
    """用 username 取得 X user ID。"""
    url = f"https://api.x.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("id")
    except Exception as e:
        console.print(f"  [dim]X user ID 查詢失敗: {e}[/dim]")
        return None


def fetch_x_following(user_id: str, bearer_token: str) -> list[str]:
    """分頁取得追蹤清單，回傳 username 列表。"""
    usernames = []
    url = f"https://api.x.com/2/users/{user_id}/following"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {"max_results": 1000, "user.fields": "username"}
    next_token = None

    while True:
        if next_token:
            params["pagination_token"] = next_token
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"  [dim]X 追蹤清單抓取失敗: {e}[/dim]")
            break

        for user in data.get("data", []):
            usernames.append(user["username"].lower())

        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break

    return usernames


def load_x_following(config: dict, bearer_token: str) -> set[str]:
    """讀取 X 追蹤清單快取，超過 7 天自動刷新。"""
    x_settings = config.get("x_settings", {})
    if not x_settings.get("filter_following") or not x_settings.get("username"):
        return set()

    # 嘗試讀快取
    if X_FOLLOWING_FILE.exists():
        cache = json.loads(X_FOLLOWING_FILE.read_text(encoding="utf-8"))
        updated = cache.get("updated", "")
        try:
            days_old = (date.today() - date.fromisoformat(updated)).days
        except ValueError:
            days_old = 999
        if days_old < 7:
            return set(cache.get("usernames", []))

    # 刷新
    console.print(f"  [dim]刷新 X 追蹤清單（@{x_settings['username']}）...[/dim]")
    user_id = get_x_user_id(x_settings["username"], bearer_token)
    if not user_id:
        # 嘗試用舊快取
        if X_FOLLOWING_FILE.exists():
            cache = json.loads(X_FOLLOWING_FILE.read_text(encoding="utf-8"))
            return set(cache.get("usernames", []))
        return set()

    usernames = fetch_x_following(user_id, bearer_token)
    if usernames:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        X_FOLLOWING_FILE.write_text(json.dumps({
            "updated": date.today().isoformat(),
            "usernames": usernames,
        }, ensure_ascii=False), encoding="utf-8")
        console.print(f"  [dim]已快取 {len(usernames)} 個追蹤帳號[/dim]")
    return set(usernames)


def search_x_discussions(keywords: str,
                         following_filter: set[str] | None = None) -> list[dict]:
    """用 DuckDuckGo site:x.com 搜尋相關推文，再用追蹤清單過濾。"""
    results = []
    clean_kw = keywords.replace("$", "").replace("#", "")
    query = f"site:x.com {clean_kw}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    }

    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        console.print(f"  [dim]X 搜尋失敗: {e}[/dim]")
        return []

    for item in soup.select(".result"):
        a = item.select_one(".result__a")
        if not a:
            continue
        href = a.get("href", "")
        if "uddg=" in href:
            parsed_qs = urllib.parse.parse_qs(
                urllib.parse.urlparse(href).query)
            href = parsed_qs.get("uddg", [href])[0]

        # 只保留 x.com 推文連結，從 URL 提取 username
        m = re.match(r"https?://(?:www\.)?x\.com/(\w+)/status/\d+", href)
        if not m:
            continue
        username = m.group(1)

        # 過濾：只保留追蹤對象的推文
        if following_filter and username.lower() not in following_filter:
            continue

        snippet_el = item.select_one(".result__snippet")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        results.append({
            "text": snippet[:500],
            "username": username,
            "url": href,
            "source": "X",
        })
        if len(results) >= 10:
            break

    return results


def search_discussions(openai_client: OpenAI, title: str,
                       original_title: str = "",
                       x_following: set[str] | None = None) -> str:
    """整合 WebSearch + X API 搜尋結果，回傳格式化文字。"""
    keywords = extract_search_keywords(openai_client, title,
                                       original_title=original_title)
    console.print(f"  [dim]搜尋關鍵字：{keywords}[/dim]")

    all_results = []

    # WebSearch
    web_results = search_web_discussions(keywords)
    console.print(f"  [dim]WebSearch 結果：{len(web_results)} 條[/dim]")
    for i, r in enumerate(web_results):
        entry = f"[Web] {r['title']}\n{r['snippet']}\n來源連結：{r['url']}"
        # 前 3 條抓全文以提取引言
        if i < 3 and r["url"]:
            article = fetch_article_content(r["url"])
            if article:
                entry += f"\n\n全文節錄：\n{article[:3000]}"
        all_results.append(entry)

    # X/Twitter（透過 DuckDuckGo site:x.com 搜尋，不消耗 X API 額度）
    x_results = search_x_discussions(keywords, following_filter=x_following)
    for r in x_results:
        all_results.append(
            f"[X] @{r['username']}:\n{r['text']}\n來源連結：{r['url']}"
        )

    if not all_results:
        return ""

    return "\n\n---\n\n".join(all_results)


def generate_discussion(gemini: genai.Client, title: str, summary: str,
                        search_results: str) -> str | None:
    """用 Gemini 從搜尋結果產出討論區塊。"""
    if not search_results:
        return None

    template = PROMPT_DISCUSSION_FILE.read_text(encoding="utf-8")
    prompt = (
        template
        .replace("{TITLE}", title)
        .replace("{SUMMARY}", summary)
        .replace("{SEARCH_RESULTS}", search_results[:15000])
    )

    try:
        response = gemini.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.7,
                thinking_config=genai_types.ThinkingConfig(thinking_budget=4096),
            ),
        )
        output = (response.text or "").strip()
        return parse_discussion(output)
    except Exception as e:
        console.print(f"  [dim]討論產生失敗: {e}[/dim]")
        return None


def parse_discussion(output: str) -> str | None:
    """解析 DISCUSSION: 輸出。回傳討論文字或 None。"""
    if "DISCUSSION: NONE" in output or "DISCUSSION:NONE" in output:
        return None

    match = re.search(r"^DISCUSSION:\s*\n([\s\S]+)$", output, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Fallback: 如果有 bullet points 但沒有 DISCUSSION: 標頭
    if output.startswith("- @") or output.startswith("- "):
        return output.strip()

    return None


# ---------------------------------------------------------------------------
# Local backup
# ---------------------------------------------------------------------------

def save_local(item: Item, summary: dict, discussion: str | None = None) -> None:
    today_str = date.today().isoformat()
    day_dir = OUTPUT_DIR / today_str
    day_dir.mkdir(parents=True, exist_ok=True)

    # 用標題做檔名（過濾不合法字元）
    safe_title = re.sub(r'[^\w\-\u4e00-\u9fff]', '_', summary["title"])[:50]
    filepath = day_dir / f"{safe_title}.md"

    content = f"""# {summary["title"]}

**來源**：{item.source}
**原文**：{item.url}
**發布**：{item.published or '未知'}
**處理**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{summary["summary"]}
"""
    if discussion:
        content += f"\n## 討論\n\n{discussion}\n"

    filepath.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(config: dict, dry_run: bool = False, limit: int = 0,
                 source_filter: str = "", auto_push: bool = False) -> None:
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not openai_key:
        console.print("[red]缺少 OPENAI_API_KEY（關鍵字提取仍需要）[/red]")
        sys.exit(1)
    if not gemini_key:
        console.print("[red]缺少 GEMINI_API_KEY[/red]")
        sys.exit(1)

    openai_client = OpenAI(api_key=openai_key)
    gemini_client = genai.Client(api_key=gemini_key)

    seen = load_seen()
    lessons = load_lessons()
    pending = load_pending()
    total_processed = 0

    # 載入 X 追蹤清單（用於過濾討論推文）
    x_following = set()
    x_token = os.getenv("X_BEARER_TOKEN")
    if x_token and config.get("x_settings", {}).get("filter_following"):
        x_following = load_x_following(config, x_token)

    sources = config.get("sources", [])
    if source_filter:
        sources = [s for s in sources if s["name"] == source_filter]
        if not sources:
            console.print(f"[red]找不到來源：{source_filter}[/red]")
            sys.exit(1)

    for source in sources:
        console.rule(f"[bold]{source['name']}[/bold]")

        if source["type"] == "rss":
            items = fetch_rss(source)
        elif source["type"] == "webpage":
            items = fetch_webpage(source)
        elif source["type"] == "youtube":
            items = fetch_youtube(source)
        else:
            console.print(f"[yellow]不支援的 type: {source['type']}[/yellow]")
            continue

        new_items = [it for it in items if it.url not in seen]
        console.print(f"共 {len(items)} 篇，其中 {len(new_items)} 篇未處理過")

        if limit:
            new_items = new_items[:limit]

        for item in new_items:
            console.print(f"\n[cyan]→ {item.title[:60]}[/cyan]")
            console.print(f"  {item.url}")

            if dry_run:
                console.print(f"  [dim]（dry-run，跳過 LLM 呼叫）[/dim]")
                seen.add(item.url)
                save_seen(seen)
                total_processed += 1
                continue

            # YouTube：抓逐字稿填充 content
            if source["type"] == "youtube" and not item.content:
                video_id = item.url.split("v=")[-1]
                with Progress(SpinnerColumn(),
                              TextColumn("{task.description}"),
                              console=console, transient=True) as progress:
                    progress.add_task("取得逐字稿中...", total=None)
                    transcript = fetch_youtube_transcript(video_id)
                if not transcript:
                    console.print("  [red]✗ 無法取得逐字稿，跳過[/red]")
                    seen.add(item.url)
                    save_seen(seen)
                    continue
                item.content = transcript

            # webpage + multi_story → LLM 拆分多則
            use_multi = (source.get("multi_story")
                         and source["type"] == "webpage")

            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=console, transient=True) as progress:
                progress.add_task("產生摘要中...", total=None)
                if use_multi:
                    summaries = generate_multi_summary(
                        gemini_client, item, lessons)
                else:
                    result = generate_summary(gemini_client, item, lessons)
                    summaries = [result] if result else []

            if not summaries:
                console.print("  [red]✗ 摘要產生失敗，跳過[/red]")
                continue

            for summary in summaries:
                console.print(f"  [green]✓ 標題：{summary['title']}[/green]")
                console.print(f"\n{summary['summary']}\n")

                # 搜尋相關討論
                discussion = None
                with Progress(SpinnerColumn(),
                              TextColumn("{task.description}"),
                              console=console, transient=True) as progress:
                    progress.add_task("搜尋相關討論中...", total=None)
                    search_results = search_discussions(
                        openai_client, summary["title"],
                        original_title=item.title,
                        x_following=x_following or None)
                    if search_results:
                        discussion = generate_discussion(
                            gemini_client, summary["title"],
                            summary["summary"], search_results)

                if discussion:
                    console.print(f"  [green]✓ 討論：[/green]")
                    console.print(f"{discussion}\n")
                else:
                    console.print(f"  [dim]（無相關討論）[/dim]")

                # 存本地備份
                save_local(item, summary, discussion=discussion)

                # 加入待推送清單（等 MCP 推送到 Notion）
                pending.append({
                    "title": summary["title"],
                    "summary": summary["summary"],
                    "importance": summary.get("importance", "中"),
                    "discussion": discussion or "",
                    "source": item.source,
                    "url": item.url,
                    "published": item.published,
                    "processed": date.today().isoformat(),
                })
                save_pending(pending)

            seen.add(item.url)
            save_seen(seen)
            total_processed += 1

            if limit and total_processed >= limit:
                break

        if limit and total_processed >= limit:
            break

    console.rule()
    console.print(f"[bold green]完成，共處理 {total_processed} 篇[/bold green]")

    if pending and auto_push:
        console.print(f"[cyan]自動推送 {len(pending)} 篇到 Notion...[/cyan]")
        pushed = push_to_notion(pending)
        if pushed == len(pending):
            pending.clear()
            save_pending(pending)
            console.print(f"[green]已全部推送，pending 已清空[/green]")
        else:
            console.print(f"[yellow]推送 {pushed}/{len(pending)} 篇，部分失敗[/yellow]")
    elif pending:
        console.print(f"[yellow]待推送到 Notion：{len(pending)} 篇（加 --push-notion 自動推送）[/yellow]")


# ---------------------------------------------------------------------------
# Notion push
# ---------------------------------------------------------------------------

NOTION_SOURCE_OPTIONS = {
    "Galaxy Research", "EthDaily", "Techmeme Crypto",
    "Citation Needed", "Tokenized Podcast",
    "Cheeky Pint", "Lex Fridman", "Acquired",
    "When Shift Happens", "The Rollup", "Empire",
    "Other",
}


def push_to_notion(pending: list[dict]) -> int:
    """將 pending 清單推送到 Notion 資料庫，回傳成功數。"""
    notion_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not notion_key or not db_id:
        console.print("[red]缺少 NOTION_API_KEY 或 NOTION_DATABASE_ID[/red]")
        return 0

    notion = NotionClient(auth=notion_key)
    pushed = 0

    for item in pending:
        source = item.get("source", "Other")
        if source not in NOTION_SOURCE_OPTIONS:
            source = "Other"

        importance = item.get("importance", "中")
        if importance not in ("高", "中", "低"):
            importance = "中"

        properties = {
            "標題": {"title": [{"text": {"content": item["title"]}}]},
            "摘要": {"rich_text": [{"text": {"content": item["summary"][:2000]}}]},
            "來源": {"select": {"name": source}},
            "重要性": {"select": {"name": importance}},
            "原文連結": {"url": item.get("url", "")},
            "狀態": {"select": {"name": "待審閱"}},
            "處理日期": {"date": {"start": item.get("processed", date.today().isoformat())}},
        }

        if item.get("discussion"):
            properties["討論"] = {
                "rich_text": [{"text": {"content": item["discussion"][:2000]}}]
            }

        if item.get("published"):
            pub = item["published"]
            # 將 RFC 2822 日期（RSS 常見格式）轉為 ISO 8601
            try:
                pub = parsedate_to_datetime(pub).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass
            properties["發布日期"] = {"date": {"start": pub}}

        try:
            notion.pages.create(parent={"database_id": db_id},
                                properties=properties)
            console.print(f"  [green]✓ 推送：{item['title'][:40]}[/green]")
            pushed += 1
        except Exception as e:
            console.print(f"  [red]✗ 推送失敗：{item['title'][:40]} — {e}[/red]")

    return pushed


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AutoFarm 自動化新聞摘要")
    parser.add_argument("--run", action="store_true", help="執行 pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="試跑，不呼叫 LLM")
    parser.add_argument("--limit", type=int, default=0,
                        help="每次最多處理幾篇（0 = 不限）")
    parser.add_argument("--source", type=str, default="",
                        help="只處理指定來源（對應 config.yml 的 name）")
    parser.add_argument("--push-notion", action="store_true",
                        help="處理完自動推送到 Notion")
    args = parser.parse_args()

    if not args.run:
        parser.print_help()
        sys.exit(0)

    if not CONFIG_FILE.exists():
        console.print(f"[red]找不到 {CONFIG_FILE}[/red]")
        sys.exit(1)

    config = yaml.safe_load(CONFIG_FILE.read_text())
    run_pipeline(config, dry_run=args.dry_run, limit=args.limit,
                 source_filter=args.source, auto_push=args.push_notion)


if __name__ == "__main__":
    main()
