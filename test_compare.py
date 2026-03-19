"""GPT-4.1 vs Gemini 3.1 Pro 摘要品質比較腳本"""

import os, sys, textwrap
from pathlib import Path
from openai import OpenAI
from google import genai

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
os.chdir(Path(__file__).parent)
from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load prompt template + lessons
lessons = Path("draft-lessons.md").read_text(encoding="utf-8")
template = Path("prompts/auto_draft.md").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Test article (use a real recent article)
# ---------------------------------------------------------------------------
TEST_ARTICLE = {
    "source": "Galaxy Research",
    "title": "Aave DAO's $22.5M 'Alignment' Proposal Goes to Vote",
    "url": "https://www.galaxy.com/insights/research/weekly-top-stories-241",
    "published": "2026-03-14",
    "content": textwrap.dedent("""\
        Aave Labs has proposed a sweeping governance overhaul called "Aave Will Win,"
        which is currently up for vote. The proposal restructures the relationship
        between Aave DAO and Aave Labs, aiming to better align incentives.

        Key terms include an upfront payment of $5M in stablecoins and 75,000 AAVE
        tokens, unlocking over two years, plus an additional $17.5M earmarked for
        new product development under the Aave umbrella. The total package of roughly
        $22.5M represents over 10% of the DAO's $171M treasury.

        The reform focuses on a longstanding challenge: misalignment between token
        holders and the core development team on responsibilities and revenue sharing.
        Previously, Aave and protocols like Uniswap relied on token buybacks to
        strengthen alignment, but the approach often resulted in indiscriminate
        high-price purchases that drained funds without meaningful structural change.

        This time, Aave Labs is proposing direct profit distribution and structural
        reorganization. If passed, the relationship between token holder returns and
        governance rights would become more explicit, potentially setting a template
        for other major DeFi protocols facing similar alignment issues.
    """),
}

# Build prompt
prompt = (
    template
    .replace("{LESSONS}", lessons)
    .replace("{SOURCE}", TEST_ARTICLE["source"])
    .replace("{ARTICLE_TITLE}", TEST_ARTICLE["title"])
    .replace("{URL}", TEST_ARTICLE["url"])
    .replace("{PUBLISHED}", TEST_ARTICLE["published"])
    .replace("{CONTENT}", TEST_ARTICLE["content"])
)

# ---------------------------------------------------------------------------
# Call both models
# ---------------------------------------------------------------------------
print("=" * 60)
print("正在呼叫 GPT-4.1 ...")
print("=" * 60)

gpt_response = openai_client.chat.completions.create(
    model="gpt-4.1",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
)
gpt_output = gpt_response.choices[0].message.content

print(gpt_output)
print()

gemini_models = [
    ("Gemini 2.5 Pro", "gemini-2.5-pro"),
    ("Gemini 3.1 Pro", "gemini-3.1-pro-preview"),
]

gemini_outputs = {}
for label, model_id in gemini_models:
    print("=" * 60)
    print(f"正在呼叫 {label} ...")
    print("=" * 60)
    resp = gemini_client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=genai.types.GenerateContentConfig(max_output_tokens=1024),
    )
    output = resp.text or "(empty)"
    gemini_outputs[label] = output
    print(output)
    print()

# ---------------------------------------------------------------------------
# Side-by-side summary
# ---------------------------------------------------------------------------
print("=" * 60)
print("字數比較")
print("=" * 60)
print(f"GPT-4.1：{len(gpt_output)} 字")
for label, output in gemini_outputs.items():
    print(f"{label}：{len(output)} 字")
