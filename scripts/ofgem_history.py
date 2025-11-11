# scripts/ofgem_history.py

"""
Manual record of recent Ofgem default tariff cap periods (GB average, Direct Debit).
Values are typical unit rates incl. VAT in p/kWh.

This file is intentionally short and human-editable.
Update when Ofgem announces new caps so the history chart and comparisons stay useful.
"""

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
    # When new caps are announced, append here:
    # {
    #     "period": "1 Oct 2024 – 31 Dec 2024",
    #     "label": "Oct–Dec 2024",
    #     "electricity_unit_avg": ...,
    #     "gas_unit_avg": ...,
    # },
]
