from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict

from .fetch_ofgem import fetch_ofgem_cap_summary
from .fetch_octopus import fetch_agile_rates_for_today, summarize_agile

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"

# Ofgem "typical household" annual usage (TDCV) – dual fuel, Direct Debit
# Source: Ofgem Average gas and electricity use explained.
# https://www.ofgem.gov.uk/information-consumers/energy-advice-households/average-gas-and-electricity-use-explained
TDCV_ELEC_KWH = 2700
TDCV_GAS_KWH = 11500


def ensure_reports_index() -> None:
    """
    Ensure reports/index.html exists with a simple listing skeleton.
    Only creates the file if missing; safe to call on every run.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    index_file = REPORTS_DIR / "index.html"

    if index_file.exists():
        return

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>UK Energy Data – Daily Reports Archive</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body {
      margin: 0;
      padding: 24px 18px 32px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, -system-ui, sans-serif;
      background: #020817;
      color: #e5e7eb;
    }
    a { color: #38bdf8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .page { max-width: 960px; margin: 0 auto; }
    h1 {
      font-size: 22px;
      margin-bottom: 6px;
    }
    p.desc {
      font-size: 13px;
      color: #9ca3af;
      margin-top: 0;
      margin-bottom: 14px;
    }
    ul {
      list-style: none;
      padding-left: 0;
      margin: 0;
      font-size: 13px;
    }
    li {
      padding: 7px 9px;
      border-radius: 10px;
      background: rgba(15,23,42,0.96);
      border: 1px solid rgba(148,163,253,0.16);
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
      gap: 10px;
    }
    .meta {
      font-size: 11px;
      color: #9ca3af;
    }
    .back {
      font-size: 11px;
      margin-top: 16px;
      color: #9ca3af;
    }
  </style>
</head>
<body>
<div class="page">
  <h1>UK Energy Data – Daily Reports</h1>
  <p class="desc">
    Auto-generated daily snapshots of Ofgem price cap and Octopus Agile data.
  </p>
  <ul id="reports-list">
  </ul>
  <div class="back">
    &larr; <a href="../index.html">Back to main dashboard</a>
  </div>
</div>
</body>
</html>
"""
    index_file.write_text(html, encoding="utf-8")


def append_report_link(date_str: str, ofgem: Dict, agile: Dict, typical_bill: Dict | None) -> None:
    """
    Append a line for the given date into reports/index.html, if not already present.
    Very small HTML manipulation: looks for <ul id="reports-list"> ... </ul>.
    """
    index_file = REPORTS_DIR / "index.html"
    if not index_file.exists():
        ensure_reports_index()

    html = index_file.read_text(encoding="utf-8")

    marker_start = '<ul id="reports-list">'
    marker_end = '</ul>'

    if marker_start not in html or marker_end not in html:
        # Fallback: do not break the file, just bail out quietly.
        return

    # Build a short meta summary for the archive line
    ofgem_ele = ofgem.get("electricity_unit_avg")
    ofgem_gas = ofgem.get("gas_unit_avg")
    agile_avg = agile.get("avg") if agile.get("has_data") else None

    parts = []
    if ofgem_ele and ofgem_gas:
        parts.append(f"Cap: {ofgem_ele:.2f}p elec / {ofgem_gas:.2f}p gas")
    if typical_bill and typical_bill.get("dual_annual_gbp"):
        parts.append(f"Typical bill ~£{typical_bill['dual_annual_gbp']:.0f}/yr")
    if agile_avg:
        parts.append(f"Agile avg {agile_avg:.2f}p")

    meta = " · ".join(parts) if parts else ""

    line = f'<li><a href="{date_str}.html">{date_str} – Daily report</a>'
    if meta:
        line += f'<span class="meta">{meta}</span>'
    line += "</li>"

    if line in html:
        return

    before, after = html.split(marker_start, 1)
    list_content, rest = after.split(marker_end, 1)

    # insert new line at top (most recent first)
    list_lines = [l for l in list_content.strip().splitlines() if l.strip()]
    list_lines.insert(0, "  " + line)
    new_list = "\n".join(list_lines) + "\n"

    new_html = before + marker_start + "\n" + new_list + marker_end + rest
    index_file.write_text(new_html, encoding="utf-8")


def compute_typical_bill(ofgem: Dict) -> Dict | None:
    """
    Compute an approximate typical dual-fuel bill under the current cap,
    using Ofgem TDCV (2,700 kWh elec, 11,500 kWh gas) and GB-average Direct Debit
    unit rates + standing charges from `ofgem`.

    Returns a dict or None if inputs are missing.
    """
    try:
        elec_unit_p = float(ofgem["electricity_unit_avg"])
        gas_unit_p = float(ofgem["gas_unit_avg"])
        elec_sc_gbp_per_day = float(ofgem["elec_standing_avg"])
        gas_sc_gbp_per_day = float(ofgem["gas_standing_avg"])
    except Exception:
        return None

    # convert to £
    elec_unit = elec_unit_p / 100.0
    gas_unit = gas_unit_p / 100.0

    elec_annual = elec_unit * TDCV_ELEC_KWH + elec_sc_gbp_per_day * 365.0
    gas_annual = gas_unit * TDCV_GAS_KWH + gas_sc_gbp_per_day * 365.0
    dual_annual = elec_annual + gas_annual
    dual_monthly = dual_annual / 12.0

    return {
        "tdcv": {
            "electricity_kwh": TDCV_ELEC_KWH,
            "gas_kwh": TDCV_GAS_KWH,
        },
        "elec_annual_gbp": round(elec_annual, 2),
        "gas_annual_gbp": round(gas_annual, 2),
        "dual_annual_gbp": round(dual_annual, 2),
        "dual_monthly_gbp": round(dual_monthly, 2),
        "note": (
            "Approximate bill for a typical dual-fuel household on the GB-average "
            "Ofgem default tariff cap (Direct Debit), based on Ofgem TDCV. "
            "Actual bills vary with usage and region."
        ),
    }


def build_daily_report() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    ensure_reports_index()

    today = datetime.utcnow().date().isoformat()
    outfile = REPORTS_DIR / f"{today}.html"

    ofgem = fetch_ofgem_cap_summary()
    agile_raw = fetch_agile_rates_for_today()
    agile = summarize_agile(agile_raw)
    typical_bill = compute_typical_bill(ofgem)

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # --- Build simple standalone HTML report ---
    lines = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        f"  <meta charset=\"UTF-8\" />",
        f"  <title>UK Energy Data – Daily Report {today}</title>",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />",
        "</head>",
        "<body>",
        f"<h1>Daily Energy Price Report – {today}</h1>",
        f"<p>Auto-generated at <code>{generated_at}</code>.</p>",
        "<h2>Ofgem price cap snapshot</h2>",
        f"<p><strong>Period:</strong> {ofgem['period']}</p>",
        "<ul>",
        f"  <li>Electricity unit rate (GB avg): {ofgem['electricity_unit_avg']} p/kWh</li>",
        f"  <li>Gas unit rate (GB avg): {ofgem['gas_unit_avg']} p/kWh</li>",
        f"  <li>Electricity standing charge (GB avg): £{ofgem['elec_standing_avg']}/day</li>",
        f"  <li>Gas standing charge (GB avg): £{ofgem['gas_standing_avg']}/day</li>",
        "</ul>",
    ]

    if typical_bill:
        lines += [
            "<h3>Typical household bill (dual fuel, Direct Debit)</h3>",
            "<p>",
            f"Approximate annual bill: <strong>£{typical_bill['dual_annual_gbp']:.0f}</strong> ",
            f"(~£{typical_bill['dual_monthly_gbp']:.0f} per month) ",
            f"based on {typical_bill['tdcv']['electricity_kwh']} kWh electricity and "
            f"{typical_bill['tdcv']['gas_kwh']} kWh gas per year.",
            "</p>",
        ]

    lines += [
        "<h2>Octopus Agile electricity – today</h2>",
    ]

    if agile["has_data"]:
        lines += [
            "<ul>",
            f"  <li>Average rate: {agile['avg']:.3f} p/kWh</li>",
            f"  <li>Lowest half-hour: {agile['low']:.3f} p/kWh</li>",
            f"  <li>Highest half-hour: {agile['high']:.3f} p/kWh</li>",
            "</ul>",
            "<p>Cheapest slots:</p>",
            "<ul>",
        ]
        for slot in agile["cheapest_slots"]:
            lines.append(f"  <li>{slot}</li>")
        lines.append("</ul>")
    else:
        lines += [
            "<p>Agile data not available for this day.</p>",
        ]

    lines += [
        "<h2>Notes</h2>",
        "<ul>",
        "<li>All values are approximate and for informational use only.</li>",
        "<li>Ofgem figures are scraped from official publications; cross-check before quoting.</li>",
        "<li>Agile rates are fetched from the official Octopus public API when available.</li>",
        "</ul>",
        '<p><a href="index.html">&larr; Back to all reports</a></p>',
        '<p><a href="../index.html">&larr; Back to main dashboard</a></p>',
        "</body>",
        "</html>",
    ]

    outfile.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] generated report: {outfile}")

    # --- latest.json for dashboard consumption ---
    DATA_DIR.mkdir(exist_ok=True)
    latest = {
        "date": today,
        "generated_at_utc": generated_at,
        "ofgem": ofgem,
        "agile": agile,
    }
    if typical_bill:
        latest["typical_bill"] = typical_bill

    (DATA_DIR / "latest.json").write_text(
        json.dumps(latest, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] wrote {DATA_DIR / 'latest.json'}")

    # update archive index
    append_report_link(today, ofgem, agile, typical_bill)
