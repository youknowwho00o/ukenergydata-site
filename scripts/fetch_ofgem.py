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

I
