import os
import subprocess
from datetime import datetime

# ---------------------------------------------------------
# 自动 Git 推送函数
# ---------------------------------------------------------
def auto_git_push():
    print("🔄 Running auto Git commit & push...")

    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
        subprocess.run(["git", "push"], check=True)

        print("✅ Git push completed.")

    except subprocess.CalledProcessError:
        print("❌ Git push failed. Maybe no changes to commit or auth issue.")
        print("   Try running manually: git add . && git commit -m 'msg' && git push")


# ---------------------------------------------------------
# 检查环境变量
# ---------------------------------------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ERROR: OPENAI_API_KEY is not set. Run:")
    print('   export OPENAI_API_KEY="your-key"')
    exit(1)

# ---------------------------------------------------------
# 要运行的生成脚本列表
# ---------------------------------------------------------
scripts = [
    "auto_policy.py",
    "auto_news.py",
    "auto_industry.py",
    "auto_energy.py",
]

print("════════════════════════════════════════════════════════════")
print("🔍 Checking AI generation scripts...\n")

for s in scripts:
    script_path = os.path.join("scripts", s)
    if os.path.exists(script_path):
        print(f"✅ Found: {script_path}")
    else:
        print(f"❌ Missing: {script_path}")
        exit(1)

print("════════════════════════════════════════════════════════════")


# ---------------------------------------------------------
# 依次运行所有生成脚本
# ---------------------------------------------------------
for script in scripts:
    print(f"\n🚀 Running {script.replace('.py','').capitalize()} generator...")
    print("════════════════════════════════════════════════════════════")

    subprocess.run(["python3", os.path.join("scripts", script)], check=True)
    print(f"✅ Finished {script.replace('.py','').capitalize()}\n")


print("════════════════════════════════════════════════════════════")
print(f"🎉 All AI content scripts completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("📝 Check new Markdown files under astro-site/src/content/")
print("════════════════════════════════════════════════════════════")

# ---------------------------------------------------------
# 最后自动 Git push
# ---------------------------------------------------------
auto_git_push()
