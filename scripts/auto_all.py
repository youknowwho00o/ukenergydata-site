import os
import subprocess
from datetime import datetime

SCRIPTS = [
    "auto_policy.py",
    "auto_news.py",
    "auto_industry.py",
    "auto_energy.py",
]

separator = "═" * 60

def run_script(script_name):
    print(f"\n🚀 Running {script_name.replace('.py','')} generator...")
    print(separator)

    try:
        subprocess.run(["python3", os.path.join("scripts", script_name)], check=True)
        print(f"✅ Finished {script_name}\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR running {script_name}: {e}\n")
        return False


def auto_git_push():
    print(separator)
    print("🔄 Running auto Git commit & push...")

    try:
        subprocess.run(["git", "add", "."], check=True)
        msg = f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)

        subprocess.run(["git", "push"], check=True)
        print("🚀 Git push complete!")
    except subprocess.CalledProcessError:
        print("⚠️ Git push skipped — maybe no changes or auth error.")


if __name__ == "__main__":
    print(separator)
    print("🔍 Checking AI generation scripts...\n")

    for script in SCRIPTS:
        print(f"→ Checking: scripts/{script}")
        if not os.path.exists(os.path.join("scripts", script)):
            print(f"   ❌ Missing: {script}")
        else:
            print(f"   ✅ Found: {script}")

    print(separator)

    # Run all content generators
    success_count = 0
    for s in SCRIPTS:
        ok = run_script(s)
        if ok:
            success_count += 1

    print(separator)
    print(f"🎉 Completed {success_count}/{len(SCRIPTS)} scripts at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(separator)

    # Auto push to Git
    auto_git_push()
    print(separator)