#!/usr/bin/env python3
"""
deploy.py — 將每日摘要部署到 GitHub Pages（git push 版）

用法：
  python3 deploy.py /path/to/daily-digest-2026-03-18.html

此腳本會：
1. 讀取 daily-digest HTML 檔
2. 將內容包裝成 GitHub Pages 格式（加上導覽列、共用 CSS）
3. 透過 git clone → commit → push 推送到 ASTROHSU/digest repo
4. 自動更新 index.html（首頁日期清單）

需要環境變數或 .env 檔：
  GITHUB_TOKEN — GitHub Personal Access Token (repo scope)
"""

import os
import sys
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# --- 設定 ---
REPO_OWNER = "ASTROHSU"
REPO_NAME = "digest"
REPO_URL_TEMPLATE = "https://x-access-token:{}@github.com/{}/{}.git"
BRANCH = "main"
SITE_DIR = Path(os.path.abspath(__file__)).parent
WORK_DIR = Path("/tmp/digest-deploy")

def get_github_token():
    """從環境變數或 .env 檔讀取 token"""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    search_paths = [
        SITE_DIR / ".env",
        SITE_DIR.parent / ".env",
    ]
    for p in Path("/sessions").glob("*/mnt/autofarm/digest-site/.env"):
        search_paths.append(p)
    for p in Path("/sessions").glob("*/mnt/autofarm/.env"):
        search_paths.append(p)
    for env_file in search_paths:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("錯誤：找不到 GITHUB_TOKEN。請設定環境變數或建立 .env 檔。")
    sys.exit(1)

def run(cmd, cwd=None):
    """執行 shell 指令（自動遮蔽 token）"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0 and "nothing to commit" not in result.stdout + result.stderr:
        # 遮蔽 token 避免洩漏
        safe_cmd = re.sub(r'x-access-token:[^@]+@', 'x-access-token:***@', cmd)
        safe_err = re.sub(r'x-access-token:[^@]+@', 'x-access-token:***@', result.stderr)
        safe_err = re.sub(r'https://[^@]+@github\.com', 'https://***@github.com', safe_err)
        print(f"指令失敗: {safe_cmd}")
        print(safe_err)
    return result

def extract_date_from_filename(filepath):
    """從檔名提取日期"""
    match = re.search(r'daily-digest-(\d{4})-(\d{2})-(\d{2})', filepath)
    if not match:
        print(f"錯誤：無法從檔名解析日期 — {filepath}")
        sys.exit(1)
    return match.group(1), match.group(2), match.group(3)

def extract_articles_and_footer(html):
    """從完整 HTML 中提取文章和 footer"""
    articles = re.findall(r'<article>.*?</article>', html, re.DOTALL)
    footer_match = re.search(r'<footer>.*?</footer>', html, re.DOTALL)
    footer = footer_match.group(0) if footer_match else ''
    return articles, footer

def find_existing_dates(repo_dir):
    """掃描 repo 中所有已有的日期頁面"""
    dates = []
    for html_file in Path(repo_dir).glob("20*/*/*.html"):
        parts = html_file.parts
        # .../2026/03/18.html
        try:
            year = parts[-3]
            month = parts[-2]
            day = html_file.stem
            if re.match(r'^\d{4}$', year) and re.match(r'^\d{2}$', month) and re.match(r'^\d{2}$', day):
                dates.append((year, month, day))
        except (IndexError, ValueError):
            pass
    return sorted(dates)

def get_adjacent(dates, year, month, day):
    """找出前後天"""
    target = (year, month, day)
    prev_link = None
    next_link = None
    for i, d in enumerate(dates):
        if d == target:
            if i > 0:
                py, pm, pd = dates[i-1]
                prev_link = f"/{REPO_NAME}/{py}/{pm}/{pd}.html"
            if i < len(dates) - 1:
                ny, nm, nd = dates[i+1]
                next_link = f"/{REPO_NAME}/{ny}/{nm}/{nd}.html"
            break
    return prev_link, next_link

def build_digest_page(articles, footer, year, month, day, prev_link, next_link):
    """將摘要內容包裝成完整的 GitHub Pages 頁面"""
    date_obj = datetime(int(year), int(month), int(day))
    weekday_names = ['一', '二', '三', '四', '五', '六', '日']
    weekday = weekday_names[date_obj.weekday()]
    date_display = f"{year} 年 {int(month)} 月 {int(day)} 日（{weekday}）"

    prev_html = f'<a href="{prev_link}">← 前一天</a>' if prev_link else '<span class="nav-disabled">← 前一天</span>'
    next_html = f'<a href="{next_link}">後一天 →</a>' if next_link else '<span class="nav-disabled">後一天 →</span>'

    articles_html = '\n\n'.join(articles)

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日摘要 — {date_display}</title>
  <link rel="stylesheet" href="/{REPO_NAME}/style.css">
</head>
<body>

<nav class="digest-nav">
  {prev_html}
  <a href="/{REPO_NAME}/">所有日期</a>
  {next_html}
</nav>

<main class="digest-body">
  <h1>每日新聞摘要</h1>
  <p class="date-line">{date_display}</p>

{articles_html}

{footer}
</main>

</body>
</html>'''

def build_index(dates):
    """建立首頁"""
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                   '七月', '八月', '九月', '十月', '十一月', '十二月']
    weekday_names = ['一', '二', '三', '四', '五', '六', '日']

    months = {}
    for y, m, d in dates:
        key = f"{y}-{m}"
        if key not in months:
            months[key] = []
        months[key].append((y, m, d))

    groups_html = ''
    for month_key in sorted(months.keys(), reverse=True):
        entries = months[month_key]
        y, m = month_key.split('-')
        month_label = f"{y} 年{month_names[int(m)-1]}"

        cards_html = ''
        for yy, mm, dd in sorted(entries, reverse=True):
            date_obj = datetime(int(yy), int(mm), int(dd))
            weekday = weekday_names[date_obj.weekday()]
            cards_html += f'''    <a class="day-card" href="/{REPO_NAME}/{yy}/{mm}/{dd}.html">
      <span class="day-date">{int(dd)} 日（{weekday}）</span>
      <span class="day-meta">{yy}.{mm}.{dd}</span>
    </a>\n'''

        groups_html += f'''  <div class="month-group">
    <div class="month-label">{month_label}</div>
{cards_html}  </div>\n'''

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日新聞摘要</title>
  <link rel="stylesheet" href="/{REPO_NAME}/style.css">
</head>
<body>

<header class="index-header">
  <h1>每日新聞摘要</h1>
  <p>自動掃描電子報與 YouTube 頻道，以繁體中文產出兩段式摘要。</p>
</header>

<main class="digest-list">
{groups_html}</main>

</body>
</html>'''

def main():
    if len(sys.argv) < 2:
        print("用法: python3 deploy.py /path/to/daily-digest-YYYY-MM-DD.html [additional-html-files...]")
        sys.exit(1)

    token = get_github_token()
    repo_url = REPO_URL_TEMPLATE.format(token, REPO_OWNER, REPO_NAME)

    # 清理工作目錄
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)

    # Clone repo
    print("📥 Cloning repo...")
    result = run(f'git clone {repo_url} {WORK_DIR}')
    if result.returncode != 0 and "empty repository" not in result.stderr:
        print("❌ Clone 失敗")
        sys.exit(1)

    # 設定 git
    run('git config user.email "mingnhsu@gmail.com"', cwd=WORK_DIR)
    run('git config user.name "ASTROHSU"', cwd=WORK_DIR)

    # 如果是空 repo，建立初始 commit
    if not (WORK_DIR / ".git" / "refs" / "heads" / BRANCH).exists():
        run(f'git checkout -b {BRANCH}', cwd=WORK_DIR)

    # 複製 CSS
    css_src = SITE_DIR / "style.css"
    if css_src.exists():
        shutil.copy2(css_src, WORK_DIR / "style.css")

    # 處理所有傳入的 HTML 檔案
    for digest_path in sys.argv[1:]:
        if not os.path.exists(digest_path):
            print(f"⚠️ 跳過找不到的檔案：{digest_path}")
            continue

        year, month, day = extract_date_from_filename(digest_path)
        print(f"📅 處理 {year}/{month}/{day}...")

        raw_html = Path(digest_path).read_text(encoding="utf-8")
        articles, footer = extract_articles_and_footer(raw_html)
        print(f"📰 {len(articles)} 篇文章")

        # 建立目錄
        page_dir = WORK_DIR / year / month
        page_dir.mkdir(parents=True, exist_ok=True)

        # 暫時先寫入，導覽列後面統一處理
        (page_dir / f"{day}.html").write_text(
            "PLACEHOLDER", encoding="utf-8"
        )

        # 儲存文章資料供後續使用
        (page_dir / f"{day}.articles.tmp").write_text(
            "\n<!-- ARTICLE_SEP -->\n".join(articles), encoding="utf-8"
        )
        (page_dir / f"{day}.footer.tmp").write_text(footer, encoding="utf-8")

    # 掃描所有日期
    all_dates = find_existing_dates(WORK_DIR)

    # 重建每個頁面（含正確的前後導覽）
    for year, month, day in all_dates:
        page_dir = WORK_DIR / year / month
        tmp_articles = page_dir / f"{day}.articles.tmp"
        tmp_footer = page_dir / f"{day}.footer.tmp"

        if tmp_articles.exists():
            articles = tmp_articles.read_text(encoding="utf-8").split("\n<!-- ARTICLE_SEP -->\n")
            footer = tmp_footer.read_text(encoding="utf-8") if tmp_footer.exists() else ""
        else:
            # 已有頁面，讀取現有 HTML
            existing = (page_dir / f"{day}.html").read_text(encoding="utf-8")
            articles_raw = re.findall(r'<article>.*?</article>', existing, re.DOTALL)
            articles = articles_raw
            footer_match = re.search(r'<footer>.*?</footer>', existing, re.DOTALL)
            footer = footer_match.group(0) if footer_match else ""

        prev_link, next_link = get_adjacent(all_dates, year, month, day)
        page_html = build_digest_page(articles, footer, year, month, day, prev_link, next_link)
        (page_dir / f"{day}.html").write_text(page_html, encoding="utf-8")

    # 清理暫存檔
    for tmp in WORK_DIR.glob("**/*.tmp"):
        tmp.unlink()

    # 建立 index
    index_html = build_index(all_dates)
    (WORK_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Git add, commit, push
    run('git add -A', cwd=WORK_DIR)

    dates_str = ", ".join(f"{y}-{m}-{d}" for y, m, d in all_dates if
                          any(sys.argv[i] and f"{y}-{m}-{d}" in sys.argv[i] for i in range(1, len(sys.argv))))
    commit_msg = f"📰 更新摘要：{dates_str or 'update'}"

    result = run(f'git commit -m "{commit_msg}"', cwd=WORK_DIR)
    if "nothing to commit" in (result.stdout + result.stderr):
        print("ℹ️ 沒有新內容需要推送")
    else:
        print("🚀 推送到 GitHub...")
        push_result = run(f'git push -u origin {BRANCH}', cwd=WORK_DIR)
        if push_result.returncode == 0:
            print("✅ 推送成功！")
        else:
            print("❌ 推送失敗")
            print(push_result.stderr)
            sys.exit(1)

    # 清理
    shutil.rmtree(WORK_DIR, ignore_errors=True)

    print(f"\n🌐 首頁：https://{REPO_OWNER.lower()}.github.io/{REPO_NAME}/")
    for digest_path in sys.argv[1:]:
        if os.path.exists(digest_path):
            y, m, d = extract_date_from_filename(digest_path)
            print(f"📄 {y}/{m}/{d}：https://{REPO_OWNER.lower()}.github.io/{REPO_NAME}/{y}/{m}/{d}.html")

if __name__ == "__main__":
    main()
