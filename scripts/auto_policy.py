import os
from datetime import datetime
from openai import OpenAI

# ✅ 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 📁 输出路径
output_dir = "astro-site/src/content/policy"
os.makedirs(output_dir, exist_ok=True)

# 🧠 生成提示
today = datetime.now().strftime("%Y-%m-%d")
prompt = f"""
Write a **UK energy policy article** in Markdown format about the latest government energy policy or program as of today.

Follow this structure:

## Overview
Briefly introduce the topic and its policy background.

## Key Points
Summarize the main elements of the policy, such as investment targets, renewable goals, timeframes, or institutions involved.

## Impact on the UK Energy Market
Explain how this affects UK households, businesses, or the overall energy transition.

## Expert Analysis
Include insights or interpretations based on current UK energy context and global trends.

## Sources
List 2–3 real credible UK government or media sources (Ofgem, BEIS, GOV.UK, BBC).

Use **Markdown formatting** for headings, bullet points, and bold keywords.
Make sure every paragraph is separated by a blank line.
"""

print("🧠 Generating AI policy article...")

# 🚀 调用 OpenAI 模型
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a UK energy policy expert writing for a public energy data website."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
)

article_content = response.choices[0].message.content.strip()

# 🧹 删除首行 "# Title" 避免重复显示
if article_content.startswith("# "):
    article_content = "\n".join(article_content.split("\n")[1:]).strip()

# 🧱 frontmatter 元数据
title = "UK Energy Policy Update " + today
description = "Latest update on UK energy policy developments and regulatory changes."
frontmatter = f"""---
title: "{title}"
date: "{today}"
description: "{description}"
---

"""

# 💾 输出 Markdown
filename = f"{today}-auto-policy.md"
filepath = os.path.join(output_dir, filename)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(frontmatter + article_content)

print(f"✅ Generated: {filepath}")
