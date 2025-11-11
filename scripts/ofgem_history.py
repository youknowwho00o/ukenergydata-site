# scripts/ofgem_history.py

"""
Manual record of recent Ofgem default tariff cap periods (GB average, Direct Debit).
Values are typical unit rates incl. VAT in p/kWh.

This file is intentionally short and human-editable.
Update when Ofgem announces new caps so the history chart and comparisons stay useful.
"""

import json
from pathlib import Path

# --- Manual records of historical caps ---
OFGEM_CAP_HISTORY = [
    {
        "period": "1 Jul 2023 – 30 Sep 2023",
        "label": "Jul–Sep 2023",
        "electricity_unit_avg": 30.11,
        "gas_unit_avg": 7.51,
    },
    {
        "period": "1 Oct 2023 – 31 Dec 2023",
        "label": "Oct–Dec 2023",
        "electricity_unit_avg": 27.35,
        "gas_unit_avg": 6.89,
    },
    {
        "period": "1 Jan 2024 – 31 Mar 2024",
        "label": "Jan–Mar 2024",
        "electricity_unit_avg": 28.62,
        "gas_unit_avg": 7.42,
    },
    {
        "period": "1 Apr 2024 – 30 Jun 2024",
        "label": "Apr–Jun 2024",
        "electricity_unit_avg": 24.50,
        "gas_unit_avg": 6.04,
    },
    {
        "period": "1 Jul 2024 – 30 Sep 2024",
        "label": "Jul–Sep 2024",
        "electricity_unit_avg": 22.36,
        "gas_unit_avg": 5.48,
    },
    {
        "period": "1 Oct 2024 – 31 Dec 2024",
        "label": "Oct–Dec 2024",
        "electricity_unit_avg": 25.73,
        "gas_unit_avg": 6.33,
    },
]

# --- Write JSON file for frontend ---
def write_history_json():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)

    outfile = data_dir / "ofgem_history.json"
    outfile.write_text(
        json.dumps(OFGEM_CAP_HISTORY, indent=2),
        encoding="utf-8"
    )
    print(f"[ok] wrote {outfile}")

# --- Allow manual run ---
if __name__ == "__main__":
    write_history_json()
