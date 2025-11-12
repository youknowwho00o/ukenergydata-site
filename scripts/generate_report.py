import json
import datetime
import os

# 模拟今日数据（后面可以改成抓 Ofgem 或 API）
electricity = 25.73
gas = 6.33
summary = "UK energy prices remain stable with mild downward pressure expected into Q1 2026."

# 获取今天日期
today = datetime.date.today().strftime("%Y-%m-%d")

# 生成 JSON 内容
report = {
    "date": today,
    "electricity": electricity,
    "gas": gas,
    "summary": summary
}

# 确保目录存在
output_dir = os.path.join("astro-site", "src", "content", "reports")
os.makedirs(output_dir, exist_ok=True)

# 保存 JSON 文件
file_path = os.path.join(output_dir, f"{today}.json")
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"✅ Report generated: {file_path}")
