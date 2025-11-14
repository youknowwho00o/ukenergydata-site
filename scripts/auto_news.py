import os
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

output_dir = "astro-site/src/content/news"
os.makedirs(output_dir, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
prompt = f"""
Write a **UK energy news update** in Markdown format about current events, announcements, or market trends
relevant to the UK energy industry as of today.

Follow this structure:

## Headline Summary
Give a short summary of the key news event.

## Details
Describe what happened, who is involved, and why it matters.

## Context
Provide background context or related developments.

## Implications
Discuss what this might mean for energy policy, consumers, or companies.

## Sources
List 2–3 credible UK sources (Ofgem, GOV.UK, BBC, The Guardian).

Use Markdown formatting and ensure clean paragraph spacing.
"""

print("🧠 Generating AI news article...")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are an energy journalist reporting on UK energy market developments."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
)

article_content = response.choices[0].message.content.strip()
if article_content.startswith("# "):
    article_content = "\n".join(article_content.split("\n")[1:]).strip()

title = f"UK Energy News Update {today}"
description = "Latest UK energy market headlines and industry updates."
frontmatter = f"""---
title: "{title}"
date: "{today}"
description: "{description}"
---

"""

filename = f"{today}-auto-news.md"
filepath = os.path.join(output_dir, filename)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(frontmatter + article_content)

print(f"✅ Generated: {filepath}")
