from __future__ import annotations

import re
from datetime import datetime
from typing import Dict

import httpx

"""
Fetch current Ofgem default tariff price cap (GB average, Direct Debit)
from the official "Energy price cap explained" page.

This implementation is designed to be:

- Simple
- Robust against future cap changes
- Backwards compatible with build_report.py:
    fetch_ofgem_cap_summary() returns:
      {
        "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
        "electricity_unit_avg": 26.35,   # p/kWh
        "gas_unit_avg": 6.29,            # p/kWh
        "elec_standing_avg": 0.54,       # £/day
        "gas_standing_avg": 0.34,        # £/day
        "source": "live" | "fallback",
        "source_urls": [...],
      }

Data source:
- https://www.ofgem.gov.uk/information-consumers/energy-advice-households/energy-price-cap-explained

Strategy:
1. From the "Between X and Y 20XX, the energy price cap is set at £N per year ..."
   sentence, parse the current cap period.
2. In the same page, locate the Electricity and Gas unit rates + standing charges
   table/text and:
   - for each fuel, take the LAST (most recent) pair of:
       "<x> pence per kWh" + "<y> pence daily standing charge"
   - those correspond to the current period.
3. Convert standing charges from p/day to £/day (2dp) for display.

If anything fails, we fall back to a static config so the daily pipeline
does NOT break.
"""

PRICE_CAP_EXPLAINED_URL = (
    "https://www.ofgem.gov.uk/information-consumers/energy-advice-households/energy-price-cap-explained"
)

# Fallback values (used only if live scraping fails)
FALLBACK_CAP = {
    "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
    "electricity_unit_avg": 26.35,  # p/kWh
    "gas_unit_avg": 6.29,           # p/kWh
    "elec_standing_avg": 0.54,      # £/day
    "gas_standing_avg": 0.34,       # £/day
    "source": "fallback",
    "source_urls": [PRICE_CAP_EXPLAINED_URL],
}


def _strip_tags(html: str) -> str:
    """Very small HTML -> text cleaner."""
    # remove script/style
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    # remove tags
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_period(text: str):
    """
    Parse:
      "Between 1 October and 31 December 2025, the energy price cap is set at £1,755 per year ..."
    into a label string used by the report.
    """
    m = re.search(
        r"Between\s+(\d{1,2})\s+([A-Za-z]+)\s+and\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}),"
        r"\s+the energy price cap is set at £\s*([\d,]+(?:\.\d+)?)\s*per year",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError("Could not locate 'Between ... the energy price cap is set at £...' sentence.")

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

    # "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)"
    start_label = f"{start.day} {start.strftime('%b %Y')}"
    end_label = f"{end.day} {end.strftime('%b %Y')}"
    period_label = f"{start_label} \u2013 {end_label} (Ofgem default tariff cap)"

    return period_label


def _parse_rates(text: str):
    """
    From the plain text of 'Energy price cap explained', extract the latest:
      - Electricity: unit (p/kWh), standing (p/day)
      - Gas: unit (p/kWh), standing (p/day)

    We do this by:
      - Finding all "Electricity <x> pence per kWh ... <y> pence daily standing charge" pairs
      - Finding all "Gas <x> pence per kWh ... <y> pence daily standing charge" pairs
      - Taking the LAST pair for each fuel (the table shows previous + current periods)
    """

    # Electricity: allow "per kWh" or "per kilowatt hour (kWh)"
    elec_pattern = re.compile(
        r"Electricity\s+([\d\.]+)\s+pence per (?:kilowatt hour\s*\(kWh\)|kWh)"
        r"\s+([\d\.]+)\s+pence daily standing charge",
        flags=re.IGNORECASE,
    )
    elec_matches = elec_pattern.findall(text)

    # Gas
    gas_pattern = re.compile(
        r"Gas\s+([\d\.]+)\s+pence per (?:kilowatt hour\s*\(kWh\)|kWh)"
        r"\s+([\d\.]+)\s+pence daily standing charge",
        flags=re.IGNORECASE,
    )
    gas_matches = gas_pattern.findall(text)

    if not elec_matches or not gas_matches:
        raise ValueError(
          f"Failed to parse Electricity/Gas unit & standing rates from explained page. "
          f"Found Electricity={len(elec_matches)}, Gas={len(gas_matches)} pairs."
        )

    # Take the LAST pair = current cap
    elec_unit_str, elec_sc_str = elec_matches[-1]
    gas_unit_str, gas_sc_str = gas_matches[-1]

    elec_unit = float(elec_unit_str)
    elec_sc_p = float(elec_sc_str)
    gas_unit = float(gas_unit_str)
    gas_sc_p = float(gas_sc_str)

    return elec_unit, elec_sc_p, gas_unit, gas_sc_p


def fetch_ofgem_cap_summary() -> Dict:
    """
    Public entrypoint used by build_report.py.

    Returns live Ofgem cap snapshot when possible; otherwise FALLBACK_CAP.
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            resp = client.get(PRICE_CAP_EXPLAINED_URL)
            resp.raise_for_status()
            text = _strip_tags(resp.text)

        period_label = _parse_period(text)
        elec_unit, elec_sc_p, gas_unit, gas_sc_p = _parse_rates(text)

        elec_sc_gbp = round(elec_sc_p / 100.0, 2)
        gas_sc_gbp = round(gas_sc_p / 100.0, 2)

        return {
            "period": period_label,
            "electricity_unit_avg": round(elec_unit, 2),
            "gas_unit_avg": round(gas_unit, 2),
            "elec_standing_avg": elec_sc_gbp,
            "gas_standing_avg": gas_sc_gbp,
            "source": "live",
            "source_urls": [PRICE_CAP_EXPLAINED_URL],
        }

    except Exception as e:
        # Do NOT break the pipeline: return the static fallback.
        # You will still see 'fallback' in latest.json so it's transparent.
        print(f"Ofgem price cap fetch failed, using fallback. Reason: {e}")
        return FALLBACK_CAP.copy()


if __name__ == "__main__":
    import json
    data = fetch_ofgem_cap_summary()
    print(json.dumps(data, indent=2))
