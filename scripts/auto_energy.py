import os
import base64
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORY = "energy-saving"
TITLE_PREFIX = "UK Energy Saving Guide"
COVER_DIR = f"astro-site/public/{CATEGORY}"
CONTENT_DIR = f"astro-site/src/content/{CATEGORY}"
IMAGE_SIZE = "1536x1024"

os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(CONTENT_DIR, exist_ok=True)


def generate_cover_image(date_str: str) -> str:
    print("🖼  Generating AI cover image (energy-saving)...")

    prompt = (
        "dark futuristic home energy efficiency theme — heat pumps, insulation, smart meters, "
        "glowing green energy lines, low-carbon home design, no text."
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


def generate_energy_article():
    today = datetime.now().strftime("%Y-%m-%d")
    md_filename = f"{today}-auto-energy.md"
    md_path = os.path.join(CONTENT_DIR, md_filename)

    cover_filename = generate_cover_image(today)
    cover_url = f"/{CATEGORY}/{cover_filename}"

    print("🧠 Generating AI energy-saving guide...")

    prompt = f"""
Write a UK home energy-saving guide for {today}.
Include:
- top methods to reduce electricity and gas usage
- heat pump advice
- insulation recommendations
- smart meter insights
- cost savings estimates
Tone: practical, helpful, consumer-friendly.
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
    print("🎉 Energy-saving generation complete!")


if __name__ == "__main__":
    generate_energy_article()