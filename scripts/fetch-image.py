#!/usr/bin/env python3
"""
fetch-image.py — 三層圖片取得策略
1. Open Graph image (og:image)
2. 文章內第一張 <img>
3. Gemini API 生圖（fallback）

用法：
  # 處理 feed.json 中所有缺圖且 importance_score >= 閾值的項目
  python scripts/fetch-image.py --feed docs/feed.json --threshold 8

  # 處理單一 URL
  python scripts/fetch-image.py --url "https://example.com/article" --title "標題" --output test.jpg

環境變數：
  GEMINI_API_KEY — 第三層 Gemini 生圖時需要
"""

from __future__ import annotations
import argparse, json, os, sys, time, re, hashlib, pathlib
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────
#  常數
# ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
}
TIMEOUT = 12  # seconds
MIN_IMG_WIDTH = 400  # 小於此寬度的 img 不要
IMG_DIR = "docs/images"  # 圖片存放目錄（相對於 repo root）
GEMINI_MODEL = "gemini-2.5-flash-image"
ASPECT_RATIO = "16:9"

# ──────────────────────────────────────────────
#  第一層：Open Graph image
# ──────────────────────────────────────────────
def fetch_og_image(url: str) -> str | None:
    """嘗試從 URL 取得 og:image。回傳圖片 URL 或 None。"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 優先 og:image
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            img_url = tag["content"].strip()
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = urljoin(url, img_url)
            if _is_valid_image_url(img_url):
                return img_url

        # 備選 twitter:image
        tag = soup.find("meta", attrs={"name": "twitter:image"})
        if not tag:
            tag = soup.find("meta", property="twitter:image")
        if tag and tag.get("content"):
            img_url = tag["content"].strip()
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = urljoin(url, img_url)
            if _is_valid_image_url(img_url):
                return img_url

    except Exception as e:
        print(f"  [OG] 抓取失敗: {e}")
    return None


# ──────────────────────────────────────────────
#  第二層：文章內第一張大圖
# ──────────────────────────────────────────────
def fetch_first_article_image(url: str) -> str | None:
    """從文章 HTML 中找第一張合理大小的 <img>。"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 找 <article> 或 main content 區塊
        content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_=re.compile(r"(post|article|content|entry)", re.I))
            or soup.body
        )
        if not content:
            return None

        for img in content.find_all("img", src=True):
            src = img["src"].strip()
            if not src or src.startswith("data:"):
                continue

            # 跳過小 icon / logo
            w = img.get("width", "")
            if w and w.isdigit() and int(w) < MIN_IMG_WIDTH:
                continue

            # 跳過常見 logo / avatar 路徑
            if any(kw in src.lower() for kw in ["logo", "avatar", "icon", "favicon", "badge", "button"]):
                continue

            # 解析為完整 URL
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = urljoin(url, src)
            elif not src.startswith("http"):
                src = urljoin(url, src)

            if _is_valid_image_url(src):
                return src

    except Exception as e:
        print(f"  [IMG] 抓取失敗: {e}")
    return None


# ──────────────────────────────────────────────
#  第三層：Gemini API 生圖
# ──────────────────────────────────────────────
def generate_gemini_image(title: str, summary: str, item_id: str) -> str | None:
    """呼叫 Gemini API 生成配圖，存到 IMG_DIR，回傳相對路徑。"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  [GEMINI] 沒有 GEMINI_API_KEY，跳過生圖")
        return None

    # 從 summary 去掉 HTML tags
    clean_summary = re.sub(r"<[^>]+>", "", summary or "")[:300]

    prompt = (
        f"Create a professional, editorial-style illustration for a news article.\n"
        f"Title: {title}\n"
        f"Context: {clean_summary}\n\n"
        f"Style requirements:\n"
        f"- Clean, modern editorial illustration\n"
        f"- Muted color palette, no garish colors\n"
        f"- No text or words in the image\n"
        f"- Horizontal/landscape orientation (16:9)\n"
        f"- Suitable as a news article hero image\n"
        f"- Abstract or symbolic representation, not literal"
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=ASPECT_RATIO,
                ),
            ),
        )

        # 存檔
        os.makedirs(IMG_DIR, exist_ok=True)
        filename = _safe_filename(item_id) + ".png"
        filepath = os.path.join(IMG_DIR, filename)

        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                import base64
                img_bytes = part.inline_data.data
                if isinstance(img_bytes, str):
                    img_bytes = base64.b64decode(img_bytes)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                print(f"  [GEMINI] 已生成: {filepath}")
                return filepath

    except ImportError:
        print("  [GEMINI] 需要安裝 google-genai: pip install google-genai")
    except Exception as e:
        print(f"  [GEMINI] 生圖失敗: {e}")
    return None


# ──────────────────────────────────────────────
#  驗證圖片 URL
# ──────────────────────────────────────────────
def _is_valid_image_url(url: str) -> bool:
    """快速檢查 URL 是否像是有效圖片。"""
    if not url or not url.startswith("http"):
        return False
    # 排除太小的 placeholder / tracking pixel
    if "1x1" in url or "pixel" in url.lower() or "spacer" in url.lower():
        return False
    return True


def _verify_image_accessible(url: str) -> bool:
    """確認圖片可存取且夠大。先試 HEAD，失敗就試部分 GET。"""
    # 已知可信 CDN 直接放行（它們通常擋 HEAD 但圖是好的）
    trusted_cdns = ["cdn.sanity.io", "cdn.thedefiant.io", "fortune.com",
                    "techcrunch.com", "coindesk.com", "theblock.co",
                    "cloudflare.com", "imgur.com", "wp.com"]
    parsed = urlparse(url)
    if any(cdn in parsed.netloc for cdn in trusted_cdns):
        return True

    try:
        # 先試 HEAD
        r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            content_type = r.headers.get("content-type", "")
            if "image" in content_type or "octet-stream" in content_type:
                size = int(r.headers.get("content-length", 0))
                if size == 0 or size >= 5000:
                    return True

        # HEAD 失敗就用部分 GET 確認
        r2 = requests.get(url, headers={**HEADERS, "Range": "bytes=0-1023"},
                          timeout=8, allow_redirects=True)
        if r2.status_code in (200, 206):
            ct = r2.headers.get("content-type", "")
            if "image" in ct or len(r2.content) > 100:
                return True

    except:
        pass
    return False


def _safe_filename(s: str) -> str:
    """把 item_id 轉成安全的檔名。"""
    # 取前 60 字元，不安全的字元換成 -
    safe = re.sub(r"[^\w\-]", "-", s)[:60]
    # 加上 hash 避免衝突
    h = hashlib.md5(s.encode()).hexdigest()[:8]
    return f"{safe}-{h}"


# ──────────────────────────────────────────────
#  主流程：兩層 fallback
# ──────────────────────────────────────────────
def resolve_image(url: str, title: str, summary: str, item_id: str) -> dict:
    """
    嘗試兩層策略取得圖片。
    回傳 {"image": url_or_path, "source": "og"|"gemini"|None}
    """
    # 第一層：OG image
    print(f"  [1/2] 嘗試 Open Graph...")
    og = fetch_og_image(url)
    if og and _verify_image_accessible(og):
        print(f"  [1/2] ✓ OG image: {og[:80]}")
        return {"image": og, "source": "og"}
    elif og:
        print(f"  [1/2] ✗ OG image 存在但無法存取: {og[:80]}")
    else:
        print(f"  [1/2] ✗ 找不到 OG image")

    # 第二層：Gemini 生圖
    print(f"  [2/2] 嘗試 Gemini 生圖...")
    gemini_path = generate_gemini_image(title, summary, item_id)
    if gemini_path:
        return {"image": gemini_path, "source": "gemini"}

    print(f"  [×] 兩層都失敗")
    return {"image": None, "source": None}


# ──────────────────────────────────────────────
#  批次處理 feed.json
# ──────────────────────────────────────────────
def process_feed(feed_path: str, threshold: int = 8, dry_run: bool = False,
                 force: bool = False, limit: int = 0):
    """
    掃描 feed.json，對 importance_score >= threshold 且缺圖的項目執行三層策略。
    --force: 即使已有 image 也重新抓
    --limit: 最多處理幾則（0 = 不限）
    """
    with open(feed_path) as f:
        data = json.load(f)

    processed = 0
    results = {"og": 0, "article": 0, "gemini": 0, "failed": 0, "skipped": 0}

    for item in data["items"]:
        score = item.get("importance_score", 0)
        if score < threshold:
            continue

        has_image = bool(item.get("image"))
        if has_image and not force:
            results["skipped"] += 1
            continue

        if limit and processed >= limit:
            break

        title = item.get("title", "")
        url = item.get("url", "")
        summary = item.get("summary", "")
        item_id = item.get("id", "unknown")

        print(f"\n{'='*60}")
        print(f"處理: {title[:50]}")
        print(f"URL:  {url[:70]}")
        print(f"分數: {score}  現有圖片: {'有' if has_image else '無'}")

        result = resolve_image(url, title, summary, item_id)

        if result["image"]:
            if not dry_run:
                item["image"] = result["image"]
                item["_image_source"] = result["source"]
            results[result["source"]] += 1
            print(f"  → 成功 ({result['source']})")
        else:
            results["failed"] += 1
            print(f"  → 失敗")

        processed += 1
        time.sleep(1)  # 避免太快被擋

    # 寫回
    if not dry_run and processed > 0:
        with open(feed_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n已寫回 {feed_path}")

    print(f"\n{'='*60}")
    print(f"結果統計:")
    print(f"  OG image:  {results['og']}")
    print(f"  文章圖片:  {results['article']}")
    print(f"  Gemini:    {results['gemini']}")
    print(f"  失敗:      {results['failed']}")
    print(f"  已有圖跳過: {results['skipped']}")


# ──────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="三層圖片取得策略")
    parser.add_argument("--feed", help="feed.json 路徑，批次處理模式")
    parser.add_argument("--threshold", type=int, default=8, help="最低 importance_score（預設 8）")
    parser.add_argument("--url", help="單一文章 URL")
    parser.add_argument("--title", default="", help="文章標題（搭配 --url）")
    parser.add_argument("--output", default="test.png", help="輸出路徑（搭配 --url）")
    parser.add_argument("--dry-run", action="store_true", help="只印結果不寫入")
    parser.add_argument("--force", action="store_true", help="即使已有 image 也重新抓")
    parser.add_argument("--limit", type=int, default=0, help="最多處理幾則（0=不限）")
    args = parser.parse_args()

    if args.feed:
        process_feed(args.feed, threshold=args.threshold, dry_run=args.dry_run,
                     force=args.force, limit=args.limit)
    elif args.url:
        result = resolve_image(args.url, args.title, "", "test")
        print(f"\n結果: {json.dumps(result, ensure_ascii=False)}")
    else:
        parser.print_help()
