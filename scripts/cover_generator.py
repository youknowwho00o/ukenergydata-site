# cover_generator.py
import os
import base64
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Allowed sizes:
# "1024x1024", "1024x1536", "1536x1024", "auto"
DEFAULT_SIZE = "1536x1024"   # Wide cover — consistent for all categories

PROMPTS = {
    "policy": "dark futuristic UK energy policy visualization – government buildings glowing with blue neons, energy grid lines, no text, cinematic lighting.",
    "news": "dark futuristic UK energy breaking news visualization – electric grid, glowing energy nodes, clean no-text newsroom style.",
    "industry": "dark futuristic UK energy industry visualization – wind farms, power stations, grid networks glowing blue, no text.",
    "energy-saving": "dark futuristic UK home energy efficiency visualization – smart home, glowing green/blue energy flow, no text."
}

def generate_cover_image(category: str, date_str: str) -> str:
    """Generate and save AI cover for any category"""
    print(f"🖼 Generating cover image for {category}...")

    prompt = PROMPTS.get(category, PROMPTS["news"])

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=DEFAULT_SIZE,
    )

    image_base64 = result.data[0].b64_json

    # Build save path
    out_dir = f"astro-site/public/{category}"
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{date_str}-cover.png"
    filepath = f"{out_dir}/{filename}"

    # Save file
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(image_base64))

    print(f"✅ Cover saved: {filepath}")
    return filename