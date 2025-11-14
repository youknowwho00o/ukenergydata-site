import os
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

output_dir = "astro-site/src/content/energy-saving"
os.makedirs(output_dir, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
prompt = f"""
Write a **UK energy-saving guide** in Markdown format that provides practical advice to help households
and businesses reduce energy use and carbon emissions.

Follow this structure:

## Introduction
Explain the motivation for energy saving and its importance in the UK context.

## Practical Tips
List 5–7 actionable tips for saving energy at home or at work.

## Benefits
Describe both financial and environmental benefits.

## Government Support
Mention relevant UK programs, grants, or incentives.

## Sources
Include credible references (GOV.UK, Ofgem, Energy Saving Trust).

Use Markdown formatting with lists and spacing for easy reading.
"""

print("🧠 Generating AI energy-saving guide...")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a UK energy efficiency advisor writing practical guides."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
)

article_content = response.choices[0].message.content.strip()
if article_content.startswith("# "):
    article_content = "\n".join(article_content.split("\n")[1:]).strip()

title = f"UK Energy Saving Guide {today}"
description = "Daily UK guide on reducing energy use and improving efficiency."
frontmatter = f"""---
title: "{title}"
date: "{today}"
description: "{description}"
---

"""

filename = f"{today}-auto-energy.md"
filepath = os.path.join(output_dir, filename)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(frontmatter + article_content)

print(f"✅ Generated: {filepath}")
