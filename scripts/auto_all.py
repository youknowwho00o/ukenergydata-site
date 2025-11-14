import os
import subprocess
from datetime import datetime

# === 项目配置 ===
scripts = [
    ("Policy", "auto_policy.py"),
    ("News", "auto_news.py"),
    ("Industry", "auto_industry.py"),
    ("Energy Saving", "auto_energy.py"),
]

separator = "═" * 60

# === 检查 API Key ===
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
    print("👉 请先运行：")
    print('$env:OPENAI_API_KEY="your-key-here"')
    exit(1)

# === 检查脚本存在性 ===
print(separator)
print("🔍 Checking AI generation scripts...\n")
for name, script in scripts:
    path = os.path.join("scripts", script)
    if not os.path.exists(path):
        print(f"⚠️  Missing: {path}")
    else:
        print(f"✅ Found: {path}")
print(separator)

# === 执行所有子脚本 ===
for name, script in scripts:
    print(f"\n🚀 Running {name} generator...")
    print(separator)
    try:
        subprocess.run(["python", os.path.join("scripts", script)], check=True)
        print(f"✅ Finished {name}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run {script}: {e}\n")

print(separator)
print(f"🎉 All AI content scripts completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("📝 Check new Markdown files under astro-site/src/content/")
print(separator)
