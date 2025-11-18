import os
import base64
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORY = "industry"
TITLE_PREFIX = "UK Energy Industry Insights"
COVER_DIR = f"astro-site/public/{CATEGORY}"
CONTENT_DIR = f"astro-site/src/content/{CATEGORY}"
IMAGE_SIZE = "1536x1024"

os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(CONTENT_DIR, exist_ok=True)


def generate_cover_image(date_str: str) -> str:
    print("🖼  Generating AI cover image (industry)...")

    prompt = (
        "dark futuristic UK energy industry theme — power plants, offshore wind, "
        "electricity infrastructure, neon blue and green energy lines, no text."
    )

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=IMAGE_SIZE,
    )

    image_base64 = result.data[0].b64_json
    filename = f"{date_str}-cover.png"
    save_path = os.path.join(COVER_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(base64.b64decode(image_base64))

    print(f"✅ Cover saved: {save_path}")
    return filename


def generate_industry_article():
    today = datetime.now().strftime("%Y-%m-%d")
    md_filename = f"{today}-auto-industry.md"
    md_path = os.path.join(CONTENT_DIR, md_filename)

    cover_filename = generate_cover_image(today)
    cover_url = f"/{CATEGORY}/{cover_filename}"

    print("🧠 Generating AI industry article...")

    prompt = f"""
Write a detailed UK energy industry analysis report for {today}.
Include:
- electricity generation mix
- renewables growth (wind, solar)
- grid infrastructure developments
- wholesale market trends
- industry investment signals
Tone: expert, analytical.
"""

    result = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    article = result.output_text

    md = f"""---
title: "{TITLE_PREFIX} {today}"
date: "{today}"
cover: "{cover_url}"
---

{article}
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ Markdown saved: {md_path}")
    print("🎉 Industry generation complete!")


if __name__ == "__main__":
    generate_industry_article()