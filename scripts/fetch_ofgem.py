from typing import Dict
from datetime import date

# 手动维护的当前 Cap 配置（示例：请上线前按 Ofgem 官网更新）
CURRENT_CAP = {
    "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
    "electricity_unit_avg": 24.50,  # p/kWh
    "gas_unit_avg": 5.90,           # p/kWh
    "elec_standing_avg": 0.53,      # £/day
    "gas_standing_avg": 0.32,       # £/day
}


def fetch_ofgem_cap_summary() -> Dict:
    """
    返回当前适用的默认价格上限摘要。
    数据手动来自 Ofgem 官方 'Default tariff cap' 公告。
    """
    # 将来可以在这里做自动抓取最新 cap。
    return CURRENT_CAP
