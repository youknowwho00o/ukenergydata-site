from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import httpx

"""
Auto-fetch Ofgem default tariff price cap (Direct Debit, GB average).

Public API (backwards compatible with your existing build_report.py)
-------------------------------------------------------------------
fetch_ofgem_cap_summary() -> Dict:
    {
        "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
        "electricity_unit_avg": 26.35,   # p/kWh
        "gas_unit_avg": 6.29,            # p/kWh
        "elec_standing_avg": 0.54,       # £/day  (rounded)
        "gas_standing_avg": 0.34,        # £/day  (rounded)
        "source": "live" | "fallback",
        "source_urls": [...],            # for debugging / transparency
    }

If live scraping fails for any reason, returns the FALLBACK_CAP values
(similar to your previous hard-coded CURRENT_CAP) with source="fallback".

Implementation strategy
-----------------------
1. From Ofgem "Energy price cap explained" page, detect the *current* cap period
   and the typical dual-fuel annual bill headline.
2. Use the cap overview / news listing to locate the corresponding
   "Changes to energy price cap between ..." (or "... rates ...") news page.
3. From that news page, regex the Direct Debit GB-average:
      - electricity unit rate (p/kWh) and standing charge (p/day)
      - gas unit rate (p/kWh) and standing charge (p/day)
4. Convert standing charges to £/day to match your existing summary schema.

No external dependencies beyond httpx + stdlib.
"""

PRICE_CAP_EXPLAINED_URL = (
    "https://www.ofgem.gov.uk/information-consumers/energy-advice-households/energy-price-cap-explained"
)
PRICE_CAP_ROOT_URL = (
    "https://www.ofgem.gov.uk/energy-regulation/domestic-and-non-domestic/"
    "energy-pricing-rules/energy-price-cap"
)
OFGEM_BASE = "https://www.ofgem.gov.uk"

# Fallback: keep this up to date manually if you want a sensible default
FALLBACK_CAP = {
    "period": "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)",
    "electricity_unit_avg": 26.35,  # p/kWh
    "gas_unit_avg": 6.29,           # p/kWh
    "elec_standing_avg": 0.54,      # £/day (53.68 p/day)
    "gas_standing_avg": 0.34,       # £/day (34.03 p/day)
    "source": "fallback",
    "source_urls": [],
}

LOG = logging.getLogger(__name__)


@dataclass
class CapPeriod:
    start: datetime
    end: datetime
    annual_bill: Optional[float]

    @property
    def label(self) -> str:
        # Example: "1 Oct 2025 – 31 Dec 2025 (Ofgem default tariff cap)"
        s = f"{self.start.day} {self.start.strftime('%b %Y')}"
        e = f"{self.end.day} {self.end.strftime('%b %Y')}"
        return f"{s} – {e} (Ofgem default tariff cap)"


def _clean_text(html: str) -> str:
    # strip scripts & styles
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.I | re.S)
    # strip tags
    text = re.sub(r"<[^>]+>", " ", html)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_current_period_from_explained(text: str) -> CapPeriod:
    """
    Look for the headline sentence, e.g.:

      "Between 1 October and 31 December 2025, the energy price cap is set at £1,755 per year ..."

    and turn that into a CapPeriod object.
    """
    m = re.search(
        r"Between\s+(\d{1,2})\s+([A-Za-z]+)\s+and\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}),"
        r"\s+the energy price cap is set at £\s*([\d,]+(?:\.\d+)?)\s*per year",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError("Could not locate current cap period sentence on 'price cap explained' page.")

    sd, sm, ed, em, year, annual = m.groups()
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
    annual_bill = float(annual.replace(",", ""))

    return CapPeriod(start=start, end=end, annual_bill=annual_bill)


def _try_candidate_news_url(period: CapPeriod, client: httpx.Client) -> Optional[str]:
    """
    Try Ofgem's standard slug pattern:
      /news/changes-energy-price-cap-between-<sd>-<month>-and-<ed>-<month>-<year>
    """
    start = period.start
    end = period.end
    sm = start.strftime("%B").lower()
    em = end.strftime("%B").lower()
    path = f"/news/changes-energy-price-cap-between-{start.day}-{sm}-and-{end.day}-{em}-{end.year}"
    url = OFGEM_BASE + path
    try:
        r = client.get(url, timeout=15.0)
        if r.status_code < 400:
            return url
    except Exception:
        pass
    return None


def _find_news_url(period: CapPeriod, client: httpx.Client) -> str:
    """
    Find the news page describing this cap period.
    Strategy:
      1. Try the standard slug pattern.
      2. Fallback: scan the main Energy price cap page for a link whose text
         contains 'Changes to energy price cap between' or 'Energy price cap rates'
         plus the period's year, and pick the first.
    """
    # 1) candidate URL by convention
    candidate = _try_candidate_news_url(period, client)
    if candidate:
        return candidate

    # 2) scan root page
    try:
        r = client.get(PRICE_CAP_ROOT_URL, timeout=15.0)
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch price cap root page: {e}") from e

    html = r.text
    # very lightweight anchor scan
    links = re.findall(
        r'href="(/news/[^"]+)"[^>]*>([^<]+)</a>',
        html,
        flags=re.IGNORECASE,
    )

    wanted_year = period.end.year
    candidates = []

    for href, label in links:
        label_l = label.lower()
        if "price cap" not in label_l:
            continue
        if "changes to energy price cap between" in label_l or "energy price cap rates" in label_l:
            if str(wanted_year) in label_l or str(wanted_year) in href:
                candidates.append(OFGEM_BASE + href)

    if candidates:
        return candidates[0]

    # If absolutely nothing matched, last resort: first price-cap-related news link
    for href, label in links:
        if "price cap" in label.lower():
            return OFGEM_BASE + href

    raise RuntimeError("Could not find any suitable price cap news link on root page.")


def _parse_rates_from_news(text: str) -> Tuple[float, float, float, float]:
    """
    Given cleaned text from the news page, extract:
      elec_unit_p, gas_unit_p, elec_sc_p_per_day, gas_sc_p_per_day

    We look for Ofgem's standard wording for Direct Debit, GB average.
    """
    # Electricity
    m_e = re.search(
        r"pay for your electricity[^.]*?Direct Debit[^.]*?on average\s+([\d\.]+)"
        r"\s+pence per kilowatt hour[^.]*?daily standing charge is\s+([\d\.]+)\s+pence per day",
        text,
        flags=re.IGNORECASE,
    )
    # Gas
    m_g = re.search(
        r"pay for your gas[^.]*?Direct Debit[^.]*?on average\s+([\d\.]+)"
        r"\s+pence per kilowatt hour[^.]*?daily standing charge is\s+([\d\.]+)\s+pence per day",
        text,
        flags=re.IGNORECASE,
    )

    if not (m_e and m_g):
        raise ValueError("Failed to locate Direct Debit GB-average unit/standing rates on news page.")

    elec_unit = float(m_e.group(1))
    elec_sc = float(m_e.group(2))
    gas_unit = float(m_g.group(1))
    gas_sc = float(m_g.group(2))

    return elec_unit, gas_unit, elec_sc, gas_sc


def fetch_ofgem_cap_summary() -> Dict:
    """
    Main entrypoint used by build_report.py.

    Returns a dict (see module docstring) using live Ofgem data when possible.
    Falls back to FALLBACK_CAP if anything goes wrong.
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            # 1) Get current period from "price cap explained"
            r = client.get(PRICE_CAP_EXPLAINED_URL)
            r.raise_for_status()
            explained_text = _clean_text(r.text)
            period = _parse_current_period_from_explained(explained_text)

            # 2) Find matching news page URL
            news_url = _find_news_url(period, client)

            # 3) Parse rates from that news page
            r2 = client.get(news_url)
            r2.raise_for_status()
            news_text = _clean_text(r2.text)
            elec_unit, gas_unit, elec_sc_p, gas_sc_p = _parse_rates_from_news(news_text)

        # Convert standing charge from p/day to £/day (round to 2dp for display)
        elec_sc_gbp = round(elec_sc_p / 100.0, 2)
        gas_sc_gbp = round(gas_sc_p / 100.0, 2)

        return {
            "period": period.label,
            "electricity_unit_avg": round(elec_unit, 2),
            "gas_unit_avg": round(gas_unit, 2),
            "elec_standing_avg": elec_sc_gbp,
            "gas_standing_avg": gas_sc_gbp,
            "source": "live",
            "source_urls": [
                PRICE_CAP_EXPLAINED_URL,
                PRICE_CAP_ROOT_URL,
                news_url,
            ],
        }

    except Exception as e:
        # Don't break the daily pipeline; just log and return fallback.
        LOG.warning("Ofgem price cap fetch failed, using fallback. Reason: %s", e)
        return FALLBACK_CAP.copy()


if __name__ == "__main__":
    # Simple manual test helper
    import json

    logging.basicConfig(level=logging.INFO)
    data = fetch_ofgem_cap_summary()
    print(json.dumps(data, indent=2))
