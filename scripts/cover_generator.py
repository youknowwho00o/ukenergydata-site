import os
import base64
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 共用封面图生成器
def generate_cover_image(prompt_category: str, date_str: str):
    """
    prompt_category: "policy" | "news" | "industry" | "energy"
    date_str: YYYY-MM-DD
    """

    prompts = {
        "policy": "Futuristic dark energy policy theme, UK government energy transition, glowing blue grid, abstract power system shapes, modern digital landscape, high contrast, clean composition, no text.",
        "news": "Breaking energy news visual, dark futuristic map of UK, glowing data lines, energy network pulses, dynamic motion, cyber-digital style, no text.",
        "industry": "UK energy industry overview, power plants silhouettes, turbines + grid visualization, neon blue/orange glow, dark background, sleek tech aesthetic, no text.",
        "energy": "Modern home energy efficiency, soft neon green/blue, smart meter glow, eco-tech theme, minimal, dark background, no text.",
    }

    prompt = prompts[prompt_category]

    output_dir = "astro-site/public/covers"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{date_str}-{prompt_category}.jpg"
    filepath = os.path.join(output_dir, filename)

    print(f"🖼 Generating cover image for {prompt_category}...")

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1792x1024"
    )

    image_base64 = result.data[0].b64_json

    with open(filepath, "wb") as f:
        f.write(base64.b64decode(image_base64))

    print(f"✅ Cover saved: {filepath}")

    return f"/covers/{filename}"