from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from .fetch_ofgem import fetch_ofgem_cap_summary
from .fetch_octopus import fetch_agile_rates_for_today, summarize_agile

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"

# Ofgem typical domestic consumption values (TDCV), dual fuel, Direct Debit
# Ref: Ofgem "Average gas and electricity use explained"
TDCV_ELEC_KWH = 2700
TDCV_GAS_KWH = 11500


def ensure_reports_index() -> None:
    """
    Ensure reports/index.html exists with a simple list skeleton.
    Only creates once; safe to call every run.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    index_file = REPORTS_DIR / "index.html"
    if index_file.exists():
        return

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>UK Energy Data – Daily Reports</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: #020712;
      color: #f5f5f7;
      padding: 24px;
      max-width: 900px;
      margin: 0 auto;
    }
    h1 {
      font-size: 24px;
      margin-bottom: 4px;
    }
    p {
      font-size: 13px;
      color: #9ca3af;
      margin-top: 0;
      margin-bottom: 16px;
    }
    a {
      color: #35c1ff;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
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
      background: rgba(10, 16, 32, 0.98);
      border: 1px solid rgba(148, 163, 253, 0.18);
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: baseline;
    }
    .meta {
      font-size: 11px;
      color: #9ca3af;
      white-space: nowrap;
    }
    .back {
      margin-top: 16px;
      font-size: 11px;
      color: #9ca3af;
    }
  </style>
</head>
<body>
  <h1>Daily Energy Price Reports</h1>
  <p>Auto-generated snapshots of Ofgem price cap and Octopus Agile data.</p>
  <ul id="reports-list">
  </ul>
  <div class="back">
    &larr; <a href="../index.html">Back to main dashboard</a>
  </div>
</body>
</html>
"""
    index_file.write_text(html, encoding="utf-8")


def compute_typical_bill(ofgem: Dict) -> Optional[Dict]:
    """
    Compute an approximate typical dual-fuel bill under the current cap.

    - Uses Ofgem TDCV: 2700 kWh elec, 11500 kWh gas per year
    - Uses GB-average Direct Debit unit + standing rates from `ofgem`.
    - Returns None if required fields are missing.
    """
    try:
        elec_unit_p = float(ofgem["electricity_unit_avg"])
        gas_unit_p = float(ofgem["gas_unit_avg"])
        elec_sc_gbp_per_day = float(ofgem["elec_standing_avg"])
        gas_sc_gbp_per_day = float(ofgem["gas_standing_avg"])
    except Exception:
        return None

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


def append_report_link(date_str: str, ofgem: Dict, agile: Dict, typical_bill: Optional[Dict]) -> None:
    """
    Insert a line for this report into reports/index.html (if not already present).
    Shows a small meta summary (cap + typical bill + Agile avg).
    """
    index_file = REPORTS_DIR / "index.html"
    if not index_file.exists():
        ensure_reports_index()

    html = index_file.read_text(encoding="utf-8")
    marker_start = '<ul id="reports-list">'
    marker_end = '</ul>'

    if marker_start not in html or marker_end not in html:
        # broken template; don't risk corrupting
        return

    # build meta text
    parts = []
    elec = ofgem.get("electricity_unit_avg")
    gas = ofgem.get("gas_unit_avg")
    if elec and gas:
        parts.append(f"Cap {elec:.2f}p elec / {gas:.2f}p gas")
    if typical_bill and typical_bill.get("dual_annual_gbp"):
        parts.append(f"Typical ~£{typical_bill['dual_annual_gbp']:.0f}/yr")
    if agile.get("has_data") and agile.get("avg") is not None:
        parts.append(f"Agile {agile['avg']:.2f}p")

    meta = " · ".join(parts) if parts else ""
    line = f'<li><a href="{date_str}.html">{date_str} – Daily report</a>'
    if meta:
        line += f'<span class="meta">{meta}</span>'
    line += "</li>"

    if line in html:
        return

    before, rest = html.split(marker_start, 1)
    list_block, after = rest.split(marker_end, 1)

    # keep most-recent-first
    rows = [r for r in list_block.strip().splitlines() if r.strip()]
    rows.insert(0, "    " + line)
    new_list = "\n".join(rows) + ("\n" if rows else "")

    new_html = before + marker_start + "\n" + new_list + marker_end + after
    index_file.write_text(new_html, encoding="utf-8")


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

    # --- HTML daily report ---
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8' />",
        f"  <title>UK Energy Data – Daily Report {today}</title>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0' />",
        "  <style>",
        "    body{font-family:system-ui,-apple-system,BlinkMacSystemFont,sans-serif;",
        "         background:#020712;color:#f5f5f7;padding:24px;max-width:900px;margin:0 auto;}",
        "    h1{font-size:24px;margin-bottom:4px;}",
        "    h2{font-size:18px;margin-top:18px;}",
        "    h3{font-size:16px;margin-top:14px;}",
        "    p,li{font-size:13px;line-height:1.6;}",
        "    a{color:#35c1ff;text-decoration:none;}",
        "    a:hover{text-decoration:underline;}",
        "    code{font-size:12px;background:#111827;padding:2px 4px;border-radius:4px;}",
        "  </style>",
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
        tb = typical_bill
        lines += [
            "<h3>Typical dual-fuel household bill (Ofgem TDCV)</h3>",
            "<p>",
            f"Based on {tb['tdcv']['electricity_kwh']} kWh electricity and "
            f"{tb['tdcv']['gas_kwh']} kWh gas per year:",
            "</p>",
            "<ul>",
            f"  <li>Electricity: £{tb['elec_annual_gbp']:.2f} per year</li>",
            f"  <li>Gas: £{tb['gas_annual_gbp']:.2f} per year</li>",
            f"  <li><strong>Total: £{tb['dual_annual_gbp']:.2f} per year "
            f"(~£{tb['dual_monthly_gbp']:.2f} per month)</strong></li>",
            "</ul>",
            "<p><em>"
            "This is an indicative bill for a typical dual-fuel customer on a default tariff. "
            "Actual costs depend on region, meter type and real consumption."
            "</em></p>",
        ]

    # --- Agile section ---
    lines += ["<h2>Octopus Agile electricity – today</h2>"]
    if agile["has_data"]:
        lines += [
            "<ul>",
            f"  <li>Average rate: {agile['avg']:.3f} p/kWh</li>",
            f"  <li>Lowest half-hour: {agile['low']:.3f} p/kWh</li>",
            f"  <li>Highest half-hour: {agile['high']:.3f} p/kWh</li>",
            "</ul>",
            "<p>Cheapest half-hour slots:</p>",
            "<ul>",
        ]
        for slot in agile["cheapest_slots"]:
            lines.append(f"  <li>{slot}</li>")
        lines.append("</ul>")
    else:
        lines.append("<p>Agile data not available for this day.</p>")

    # --- Notes ---
    lines += [
        "<h2>Notes</h2>",
        "<ul>",
        "<li>All values are approximate and for informational use only.</li>",
        "<li>Ofgem figures are scraped from official publications; check Ofgem before quoting.</li>",
        "<li>Agile rates come from the public Octopus Energy API when available.</li>",
        "</ul>",
        "<p><a href='index.html'>&larr; Back to reports index</a></p>",
        "<p><a href='../index.html'>&larr; Back to main dashboard</a></p>",
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

    latest_path = DATA_DIR / "latest.json"
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    print(f"[ok] wrote {latest_path}")

    # --- update reports index ---
    append_report_link(today, ofgem, agile, typical_bill)
