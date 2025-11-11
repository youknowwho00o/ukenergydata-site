from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict

import httpx

"""
Fetch current Ofgem default tariff price cap (GB average, Direct Debit).

This script is designed to be:

- Simple: single source page ("Energy price cap explained").
- Robust: tolerant to wording changes by using patterns and latest entries.
- Safe: if live fetch fails, it falls back to previous live data from data/latest.json,
        and only then to static fallback constants.
- Compatible: fetch_ofgem_cap_summary() returns exactly what build_report.py expects.

Returned dict:
{
  "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
  "electricity_unit_avg": 25.73,   # p/kWh
  "gas_unit_avg": 6.33,            # p/kWh
  "elec_standing_avg": 0.51,       # £/day
  "gas_standing_avg": 0.30,        # £/day
  "source": "live" | "live-cache" | "fallback",
  "source_urls": [...]
}
"""

PRICE_CAP_EXPLAINED_URL = (
    "https://www.ofgem.gov.uk/information-consumers/energy-advice-households/energy-price-cap-explained"
)

# Static fallback (only used作为最后兜底)
FALLBACK_CAP = {
    "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
    "electricity_unit_avg": 25.73,
    "gas_unit_avg": 6.33,
    "elec_standing_avg": 0.51,
    "gas_standing_avg": 0.30,
    "source": "fallback",
    "source_urls": [PRICE_CAP_EXPLAINED_URL],
}


def _strip_tags(html: str) -> str:
    """Very small HTML → text cleaner."""
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_period(text: str) -> str:
    """
    Parse sentence like:
      "Between 1 October and 31 December 2025, the energy price cap is set at £1,755 per year ..."
    into:
      "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)"
    """
    m = re.search(
        r"Between\s+(\d{1,2})\s+([A-Za-z]+)\s+and\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}),"
        r"\s+the energy price cap is set at £\s*([\d,]+(?:\.\d+)?)\s*per year",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError("Could not find 'Between ... the energy price cap is set at £...' sentence on Ofgem page.")

    sd, sm, ed, em, year, _annual = m.groups()
    year_i = int(year)

    def parse_date(day: str, month: str) -> datetime:
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(f"{day} {month} {year_i}", fmt)
            except ValueError:
                continue
        raise ValueError(f"Invalid date: {day} {month} {year_i}")

    start = parse_date(sd, sm)
    end = parse_date(ed, em)

    start_label = f"{start.day} {start.strftime('%b %Y')}"
    end_label = f"{end.day} {end.strftime('%b %Y')}"
    return f"{start_label} \u2013 {end_label} (Ofgem default tariff cap)"


def _parse_rates(text: str):
    """
    From the plain text of "Energy price cap explained", extract the latest:
      - Electricity: unit (p/kWh), standing (p/day)
      - Gas: unit (p/kWh), standing (p/day)

    Approach:
      - Find all pairs for Electricity:
          "Electricity <x> pence per kWh ... <y> pence daily standing charge"
      - Find all pairs for Gas:
          "Gas <x> pence per kWh ... <y> pence daily standing charge"
      - The last pair for each is the current cap.
    """

    elec_pattern = re.compile(
        r"Electricity\s+([\d\.]+)\s+pence per (?:kilowatt hour\s*\(kWh\)|kWh)"
        r"\s+([\d\.]+)\s+pence daily standing charge",
        flags=re.IGNORECASE,
    )
    gas_pattern = re.compile(
        r"Gas\s+([\d\.]+)\s+pence per (?:kilowatt hour\s*\(kWh\)|kWh)"
        r"\s+([\d\.]+)\s+pence daily standing charge",
        flags=re.IGNORECASE,
    )

    elec_matches = elec_pattern.findall(text)
    gas_matches = gas_pattern.findall(text)

    if not elec_matches or not gas_matches:
        raise ValueError(
            f"Failed to parse cap rates from Ofgem explained page "
            f"(found Electricity={len(elec_matches)}, Gas={len(gas_matches)} pairs)."
        )

    elec_unit_s, elec_sc_s = elec_matches[-1]
    gas_unit_s, gas_sc_s = gas_matches[-1]

    elec_unit = float(elec_unit_s)
    elec_sc_p = float(elec_sc_s)
    gas_unit = float(gas_unit_s)
    gas_sc_p = float(gas_sc_s)

    return elec_unit, elec_sc_p, gas_unit, gas_sc_p


def _try_load_previous_live() -> Dict | None:
    """
    If live fetch fails, try to reuse yesterday's live Ofgem section from data/latest.json.
    Returns a normalized summary dict or None.
    """
    root = Path(__file__).resolve().parents[1]
    latest_path = root / "data" / "latest.json"
    if not latest_path.exists():
        return None

    try:
        import json

        with latest_path.open("r", encoding="utf-8") as f:
            latest = json.load(f)
    except Exception:
        return None

    prev = latest.get("ofgem") or latest.get("ofgem_price_cap")
    if not prev:
        return None

    if prev.get("source") not in ("live", "live-cache"):
        return None

    # 支持旧结构 & 新结构
    period = (
        prev.get("period")
        or prev.get("current_price_cap", {}).get("period", {}).get("label")
        or FALLBACK_CAP["period"]
    )

    # 电/气单价
    elec_unit = (
        prev.get("electricity_unit_avg")
        or prev.get("electricity_direct_debit_gb_average", {}).get("unit_rate_p_per_kwh")
    )
    gas_unit = (
        prev.get("gas_unit_avg")
        or prev.get("gas_direct_debit_gb_average", {}).get("unit_rate_p_per_kwh")
    )

    # 站费（可能是 £/day 或 p/day，尽量识别）
    elec_sc = prev.get("elec_standing_avg")
    gas_sc = prev.get("gas_standing_avg")

    if elec_sc is None:
        v = prev.get("electricity_direct_debit_gb_average", {}).get("standing_charge_p_per_day")
        elec_sc = (float(v) / 100.0) if v is not None else None

    if gas_sc is None:
        v = prev.get("gas_direct_debit_gb_average", {}).get("standing_charge_p_per_day")
        gas_sc = (float(v) / 100.0) if v is not None else None

    if not all([elec_unit, gas_unit, elec_sc, gas_sc]):
        return None

    return {
        "period": period,
        "electricity_unit_avg": float(elec_unit),
        "gas_unit_avg": float(gas_unit),
        "elec_standing_avg": float(elec_sc),
        "gas_standing_avg": float(gas_sc),
        "source": "live-cache",
        "source_urls": prev.get("source_urls", [PRICE_CAP_EXPLAINED_URL]),
    }


def fetch_ofgem_cap_summary() -> Dict:
    """
    Public entrypoint used by build_report.py.

    1. Try live scrape from Ofgem.
    2. If fail → try reuse previous live data from latest.json (source=live-cache).
    3. If still fail → use static FALLBACK_CAP.
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            resp = client.get(PRICE_CAP_EXPLAINED_URL)
            resp.raise_for_status()
            text = _strip_tags(resp.text)

        period = _parse_period(text)
        elec_unit, elec_sc_p, gas_unit, gas_sc_p = _parse_rates(text)

        elec_sc_gbp = round(elec_sc_p / 100.0, 2)
        gas_sc_gbp = round(gas_sc_p / 100.0, 2)

        return {
            "period": period,
            "electricity_unit_avg": round(elec_unit, 2),
            "gas_unit_avg": round(gas_unit, 2),
            "elec_standing_avg": elec_sc_gbp,
            "gas_standing_avg": gas_sc_gbp,
            "source": "live",
            "source_urls": [PRICE_CAP_EXPLAINED_URL],
        }

    except Exception as e:
        print(f"Ofgem price cap fetch failed, trying cached latest.json. Reason: {e}")
        cached = _try_load_previous_live()
        if cached:
            print("Reusing previous live Ofgem cap from latest.json (source=live-cache).")
            return cached

        print("Using static fallback Ofgem cap values.")
        return FALLBACK_CAP.copy()


if __name__ == "__main__":
    import json

    data = fetch_ofgem_cap_summary()
    print(json.dumps(data, indent=2))
