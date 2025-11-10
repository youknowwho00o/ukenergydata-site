from typing import Dict

# 占位数据：确保自动化流程先能跑通。
# 之后可根据最新 Ofgem 文档改成真实爬虫 / CSV 解析。

def fetch_ofgem_cap_summary() -> Dict:
    """
    Return a simple snapshot of the current Ofgem price cap.
    Values are SAMPLE ONLY for now.
    """
    return {
        "period": "Sample period – replace with live Ofgem data",
        "electricity_unit_avg": 26.17,  # p/kWh
        "gas_unit_avg": 6.02,           # p/kWh
        "elec_standing_avg": 0.53,      # £/day
        "gas_standing_avg": 0.32,       # £/day
    }
