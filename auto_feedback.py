#!/usr/bin/env python3
"""
auto_feedback.py — 被動學習模組

功能：
1. 儲存原稿：摘要產出時呼叫 save_original()，存一份到 data/originals/
2. 比對差異：呼叫 diff_and_learn()，自動比對原稿與修改版
3. 更新字典：偵測到用字替換時，自動新增到 word-map.yml
4. 套用字典：摘要產出前呼叫 apply_word_map()，程式化替換用字

用法：
  # 存原稿（在摘要產出後立即呼叫）
  python auto_feedback.py save <file_path>

  # 比對原稿與修改版，自動學習
  python auto_feedback.py diff <file_path>

  # 套用 word-map.yml 替換
  python auto_feedback.py apply <file_path>

  # 顯示目前字典統計
  python auto_feedback.py stats
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

BASE_DIR = Path(__file__).parent
ORIGINALS_DIR = BASE_DIR / "data" / "originals"
WORD_MAP_FILE = BASE_DIR / "word-map.yml"
LESSONS_FILE = BASE_DIR / "draft-lessons.md"

ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)


def load_word_map() -> dict:
    """讀取 word-map.yml，回傳扁平化的 {禁用詞: 替換詞} dict"""
    if not WORD_MAP_FILE.exists():
        return {}
    with open(WORD_MAP_FILE, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    flat = {}
    for category, mappings in raw.items():
        if isinstance(mappings, dict):
            for k, v in mappings.items():
                if isinstance(v, str) and not v.startswith("("):
                    flat[k] = v
    return flat


def save_original(file_path: str):
    """將檔案複製一份到 data/originals/，檔名加上時間戳"""
    src = Path(file_path)
    if not src.exists():
        print(f"❌ 檔案不存在：{file_path}")
        sys.exit(1)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = ORIGINALS_DIR / f"{src.stem}_{ts}{src.suffix}"
    shutil.copy2(src, dest)
    print(f"✅ 原稿已儲存：{dest.name}")
    return dest


def find_original(file_path: str) -> Path | None:
    """找到對應的最新原稿"""
    src = Path(file_path)
    stem = src.stem
    candidates = sorted(
        ORIGINALS_DIR.glob(f"{stem}_*{src.suffix}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def extract_text_from_html(html: str) -> str:
    """從 HTML 中提取純文字（簡易版，不依賴 bs4）"""
    # 移除 style/script 標籤內容
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    # 移除 HTML 標籤
    text = re.sub(r"<[^>]+>", "\n", text)
    # 清理空白
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", "", text)
    return text.strip()


def diff_and_learn(file_path: str):
    """比對原稿與修改版，提取用字差異"""
    src = Path(file_path)
    original = find_original(file_path)

    if not original:
        print(f"⚠️ 找不到 {src.name} 的原稿，跳過比對")
        return

    # 讀取兩個版本
    orig_text = original.read_text(encoding="utf-8")
    curr_text = src.read_text(encoding="utf-8")

    # 如果是 HTML，提取純文字比對
    if src.suffix == ".html":
        orig_text = extract_text_from_html(orig_text)
        curr_text = extract_text_from_html(curr_text)

    if orig_text.strip() == curr_text.strip():
        print("✅ 沒有差異，不需要學習")
        return

    # 用 difflib 找出差異
    orig_lines = orig_text.splitlines()
    curr_lines = curr_text.splitlines()

    diff = list(difflib.unified_diff(orig_lines, curr_lines, lineterm=""))

    if not diff:
        print("✅ 沒有差異，不需要學習")
        return

    # 提取用字替換（找到 -/+ 配對）
    word_changes = []
    removals = []
    additions = []

    for line in diff:
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            removals.append(line[1:].strip())
        elif line.startswith("+"):
            additions.append(line[1:].strip())

    # 嘗試配對相似的行，找出具體用字替換
    for rem in removals:
        best_match = None
        best_ratio = 0.6  # 最低相似度門檻
        for add in additions:
            ratio = difflib.SequenceMatcher(None, rem, add).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = add
        if best_match:
            # 找出這一行中具體被替換的詞
            s = difflib.SequenceMatcher(None, rem, best_match)
            for tag, i1, i2, j1, j2 in s.get_opcodes():
                if tag == "replace":
                    old_word = rem[i1:i2].strip()
                    new_word = best_match[j1:j2].strip()
                    if old_word and new_word and len(old_word) < 20 and len(new_word) < 20:
                        word_changes.append((old_word, new_word))

    if word_changes:
        print(f"\n📝 偵測到 {len(word_changes)} 個用字替換：")
        for old, new in word_changes:
            print(f"   「{old}」→「{new}」")

        # 詢問是否加入字典
        print(f"\n這些替換已記錄。執行 'python auto_feedback.py update-dict' 可加入 word-map.yml")

        # 寫入暫存檔，供後續確認
        pending_file = ORIGINALS_DIR / "pending_words.txt"
        with open(pending_file, "a", encoding="utf-8") as f:
            f.write(f"\n# {datetime.now().isoformat()} — {src.name}\n")
            for old, new in word_changes:
                f.write(f"{old}: {new}\n")
    else:
        print("📝 偵測到結構性差異，但沒有明確的用字替換")

    # 輸出 diff 摘要
    changed_lines = len([l for l in diff if l.startswith("+") or l.startswith("-")])
    print(f"\n📊 差異統計：{changed_lines} 行有變動")
    print(f"   原稿：{original.name}")
    print(f"   修改版：{src.name}")


def apply_word_map(file_path: str):
    """讀取檔案，套用 word-map.yml 替換，寫回"""
    word_map = load_word_map()
    if not word_map:
        print("⚠️ word-map.yml 為空或不存在")
        return

    src = Path(file_path)
    text = src.read_text(encoding="utf-8")
    original_text = text

    count = 0
    for old_word, new_word in word_map.items():
        if old_word in text:
            occurrences = text.count(old_word)
            text = text.replace(old_word, new_word)
            count += occurrences
            print(f"   替換「{old_word}」→「{new_word}」（{occurrences} 處）")

    if count > 0:
        src.write_text(text, encoding="utf-8")
        print(f"\n✅ 共替換 {count} 處")
    else:
        print("✅ 沒有需要替換的用字")


def show_stats():
    """顯示字典和原稿統計"""
    word_map = load_word_map()
    originals = list(ORIGINALS_DIR.glob("*"))
    originals = [f for f in originals if f.suffix in (".html", ".md")]

    print(f"📖 word-map.yml：{len(word_map)} 條替換規則")
    print(f"📁 data/originals/：{len(originals)} 份原稿")

    if originals:
        latest = max(originals, key=lambda p: p.stat().st_mtime)
        print(f"   最新原稿：{latest.name}")


def main():
    parser = argparse.ArgumentParser(description="autofarm 被動學習模組")
    parser.add_argument("action", choices=["save", "diff", "apply", "stats"])
    parser.add_argument("file", nargs="?", help="目標檔案路徑")
    args = parser.parse_args()

    if args.action == "stats":
        show_stats()
    elif args.action == "save":
        if not args.file:
            print("❌ 請提供檔案路徑")
            sys.exit(1)
        save_original(args.file)
    elif args.action == "diff":
        if not args.file:
            print("❌ 請提供檔案路徑")
            sys.exit(1)
        diff_and_learn(args.file)
    elif args.action == "apply":
        if not args.file:
            print("❌ 請提供檔案路徑")
            sys.exit(1)
        apply_word_map(args.file)


if __name__ == "__main__":
    main()
