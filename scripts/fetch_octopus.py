import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import zoneinfo

UK_TZ = "Europe/London"

# 示例 Agile 产品与费率代码
# 如后续你用真实账户，可按 Octopus 官方文档替换为当前有效产品代码
AGILE_PRODUCT_CODE = "AGILE-FLEX-22-11-25"
AGILE_TARIFF_CODE = "E-1R-AGILE-FLEX-22-11-25-C"


def fetch_agile_rates_for_today() -> List[Dict]:
    """
    拉取今天（英国本地时间）的 Octopus Agile 半小时电价。
    返回列表元素格式：
    {
      "valid_from": "...",
      "valid_to": "...",
      "value_inc_vat": 12.345
    }
    若失败返回 []（上层逻辑会兜底）
    """
    try:
        tz = zoneinfo.ZoneInfo(UK_TZ)
        now_uk = datetime.now(tz)
        start = now_uk.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        params = {
            "period_from": start.astimezone(timezone.utc).isoformat(),
            "period_to": end.astimezone(timezone.utc).isoformat(),
            "page_size": 5000,
        }

        base = "https://api.octopus.energy/v1"
        url = (
            f"{base}/products/{AGILE_PRODUCT_CODE}"
            f"/electricity-tariffs/{AGILE_TARIFF_CODE}/standard-unit-rates/"
        )

        r = httpx.get(url, params=params, timeout=20.0)
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except Exception:
        return []


def summarize_agile(rates: List[Dict]) -> Dict:
    """
    根据半小时价格列表做简单统计。
    """
    if not rates:
        return {
            "has_data": False,
            "avg": None,
            "low": None,
            "high": None,
            "cheapest_slots": [],
        }

    prices = [float(r["value_inc_vat"]) for r in rates]
    low = min(prices)
    high = max(prices)
    avg = sum(prices) / len(prices)

    # 找出若干最便宜的时间段
    sorted_rates = sorted(rates, key=lambda r: float(r["value_inc_vat"]))
    cheapest_slots = []
    for r in sorted_rates[:5]:
        price = float(r["value_inc_vat"])
        frm = r["valid_from"].replace("T", " ").replace("Z", "")
        to = r["valid_to"].replace("T", " ").replace("Z", "")
        cheapest_slots.append(
            f"{frm} — {to} · {price:.2f} p/kWh"
        )

    return {
        "has_data": True,
        "avg": round(avg, 3),
        "low": round(low, 3),
        "high": round(high, 3),
        "cheapest_slots": cheapest_slots,
    }
