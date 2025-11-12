from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

from .fetch_ofgem import fetch_ofgem_cap_summary
from .fetch_octopus import fetch_agile_rates_for_today, summarize_agile
from .ofgem_history import OFGEM_CAP_HISTORY

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"

<<<<<<< HEAD
# Ofgem typical domestic consumption values (TDCV), dual fuel, Direct Debit
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
TDCV_ELEC_KWH = 2700
TDCV_GAS_KWH = 11500


def ensure_reports_index() -> None:
<<<<<<< HEAD
    """
    Ensure reports/index.html exists with a styled list skeleton.
    Safe to call every run.
    """
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
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
    :root {
      --bg: #020817;
      --bg-card: #070f23;
      --border-subtle: rgba(148, 163, 253, 0.16);
      --accent: #38bdf8;
      --text-main: #e5e7eb;
      --text-subtle: #9ca3af;
      --radius-xl: 20px;
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, -system-ui, sans-serif;
    }
    body {
      margin: 0;
      padding: 24px 18px 32px;
      font-family: var(--font-sans);
      background: radial-gradient(circle at top, #020817 0, #000 55%);
      color: var(--text-main);
    }
    .page { max-width: 960px; margin: 0 auto; }
    .brand { display: flex; align-items: center; gap: 8px; }
    .dot { width: 9px; height: 9px; border-radius: 999px; background: var(--accent); box-shadow: 0 0 10px var(--accent); }
    h1 { font-size: 22px; margin: 0; }
    .subtitle { font-size: 12px; color: var(--text-subtle); margin-top: 4px; }
    nav { margin-top: 8px; font-size: 12px; display: flex; gap: 14px; }
    nav a { color: var(--text-subtle); text-decoration: none; }
    nav a:hover { text-decoration: underline; }
    nav a.active { color: var(--accent); }
    .card {
      background: var(--bg-card);
      border-radius: var(--radius-xl);
      border: 1px solid var(--border-subtle);
      padding: 14px 14px 10px;
      margin-top: 10px;
    }
    .card-title { font-size: 14px; font-weight: 600; margin: 0 0 4px; }
    .card-text { font-size: 11px; color: var(--text-subtle); margin: 0 0 4px; }
    ul#reports-list {
      list-style: none;
      padding-left: 0;
      margin: 4px 0 0;
      font-size: 12px;
    }
    ul#reports-list li {
      padding: 6px 8px;
      border-radius: 10px;
      border: 1px solid rgba(148,163,253,0.18);
      background: rgba(5,10,25,0.98);
      margin-bottom: 5px;
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: baseline;
    }
    ul#reports-list a { color: var(--accent); }
    ul#reports-list a:hover { text-decoration: underline; }
    .meta { font-size: 10px; color: var(--text-subtle); white-space: nowrap; }
    footer {
      margin-top: 18px;
      font-size: 9px;
      color: var(--text-subtle);
    }
    @media (max-width: 640px) {
      body { padding: 18px 12px 24px; }
      ul#reports-list li { flex-direction: column; align-items: flex-start; }
      .meta { margin-top: 2px; }
    }
  </style>
</head>
<body>
<div class="page">
  <header>
    <div class="brand">
      <div class="dot"></div>
      <h1>Daily Energy Price Reports</h1>
    </div>
    <div class="subtitle">
      Archived daily snapshots of Ofgem price cap levels and Octopus Agile data.
      Generated automatically from public sources.
    </div>
    <nav>
      <a href="../index.html">&larr; Back to dashboard</a>
      <a href="index.html" class="active">Reports archive</a>
      <a href="https://github.com/youknowwho00o/ukenergydata-site" target="_blank" rel="noopener">Source on GitHub</a>
    </nav>
  </header>
  <section class="card">
    <div class="card-title">Browse daily snapshots</div>
    <p class="card-text">
      Each report is a static HTML file containing the Ofgem cap snapshot, Octopus Agile summary
      and the calculated typical-bill estimate for that day.
    </p>
    <ul id="reports-list">
    </ul>
  </section>
  <footer>
    &copy; ukenergydata.co.uk · Auto-generated from public data sources.
  </footer>
</div>
</body>
</html>
"""
    index_file.write_text(html, encoding="utf-8")


def compute_typical_bill(ofgem: Dict) -> Optional[Dict]:
<<<<<<< HEAD
    """Compute typical dual-fuel bill under current cap using Ofgem TDCV."""
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    try:
        elec_unit_p = float(ofgem["electricity_unit_avg"])
        gas_unit_p = float(ofgem["gas_unit_avg"])
        elec_sc = float(ofgem["elec_standing_avg"])
        gas_sc = float(ofgem["gas_standing_avg"])
    except Exception:
        return None

    elec_unit = elec_unit_p / 100.0
    gas_unit = gas_unit_p / 100.0

    elec_annual = elec_unit * TDCV_ELEC_KWH + elec_sc * 365.0
    gas_annual = gas_unit * TDCV_GAS_KWH + gas_sc * 365.0
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


def build_cap_history_with_current(ofgem: Dict) -> List[Dict]:
<<<<<<< HEAD
    """
    Take manual OFGEM_CAP_HISTORY and append current cap if not already present.
    """
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    history: List[Dict] = [dict(h) for h in OFGEM_CAP_HISTORY]

    current = {
        "period": ofgem.get("period"),
        "label": ofgem.get("period"),
        "electricity_unit_avg": ofgem.get("electricity_unit_avg"),
        "gas_unit_avg": ofgem.get("gas_unit_avg"),
    }

    if current["period"] and current["electricity_unit_avg"] and current["gas_unit_avg"]:
        if not any(h.get("period") == current["period"] for h in history):
            history.append(current)

    return [
        h for h in history
        if h.get("electricity_unit_avg") is not None and h.get("gas_unit_avg") is not None
    ]


def compute_cap_changes(history: List[Dict]) -> Optional[Dict]:
<<<<<<< HEAD
    """
    Using history where last entry is current period,
    compute change vs previous period and vs peak.
    """
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    if len(history) < 2:
        return None

    prev = history[-2]
    curr = history[-1]

    def pct(curr_v: float, prev_v: float) -> Optional[float]:
        try:
            if prev_v <= 0:
                return None
            return round((curr_v - prev_v) / prev_v * 100.0, 1)
        except Exception:
            return None

    elec_change = pct(curr["electricity_unit_avg"], prev["electricity_unit_avg"])
    gas_change = pct(curr["gas_unit_avg"], prev["gas_unit_avg"])

    peak = max(history, key=lambda h: h["electricity_unit_avg"])
    peak_label = peak.get("label") or peak.get("period")
    peak_elec_change = pct(curr["electricity_unit_avg"], peak["electricity_unit_avg"])

    return {
        "prev_label": prev.get("label") or prev.get("period"),
        "elec_vs_prev_pct": elec_change,
        "gas_vs_prev_pct": gas_change,
        "peak_label": peak_label,
        "elec_vs_peak_pct": peak_elec_change,
    }


def append_report_link(date_str: str, ofgem: Dict, agile: Dict, typical_bill: Optional[Dict]) -> None:
<<<<<<< HEAD
    """
    Insert today's report link into reports/index.html, newest first.
    """
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    index_file = REPORTS_DIR / "index.html"
    if not index_file.exists():
        ensure_reports_index()

    html = index_file.read_text(encoding="utf-8")
    marker = '<ul id="reports-list">'
    if marker not in html:
        return

<<<<<<< HEAD
    # Build meta summary
=======
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    parts = []
    eu = ofgem.get("electricity_unit_avg")
    gu = ofgem.get("gas_unit_avg")
    if eu and gu:
        parts.append(f"{eu:.2f}p elec / {gu:.2f}p gas")
    if typical_bill and typical_bill.get("dual_annual_gbp"):
        parts.append(f"typical ~£{typical_bill['dual_annual_gbp']:.0f}/yr")
    if agile.get("has_data") and agile.get("avg") is not None:
        parts.append(f"Agile {agile['avg']:.2f}p")

    meta = " · ".join(parts) if parts else ""
    line = f'<li><a href="{date_str}.html">{date_str}</a>'
    if meta:
        line += f'<span class="meta">{meta}</span>'
    line += "</li>"

    if line in html:
        return

    before, after = html.split(marker, 1)
    new_html = before + marker + "\n    " + line + after
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

    cap_history = build_cap_history_with_current(ofgem)
    cap_change = compute_cap_changes(cap_history)

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # --- HTML REPORT ---
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

    if cap_change:
        lines += [
            "<p>",
            f"Compared with <strong>{cap_change['prev_label']}</strong>: ",
            "electricity ",
            ("+" if (cap_change['elec_vs_prev_pct'] or 0) > 0 else ""),
            f"{cap_change['elec_vs_prev_pct']}%, ",
            "gas ",
            ("+" if (cap_change['gas_vs_prev_pct'] or 0) > 0 else ""),
            f"{cap_change['gas_vs_prev_pct']}%.",
            "</p>",
        ]
        if cap_change.get("elec_vs_peak_pct") is not None:
            lines += [
                "<p>",
                f"Electricity unit rate is {cap_change['elec_vs_peak_pct']}% ",
                f"vs the peak period ({cap_change['peak_label']}).",
                "</p>",
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

    lines += [
        "<h2>Notes</h2>",
        "<ul>",
        "<li>All values are approximate and for informational use only.</li>",
        "<li>Ofgem figures are scraped from official publications; always check Ofgem before quoting.</li>",
        "<li>Agile rates come from the public Octopus Energy API when available.</li>",
        "</ul>",
        "<p><a href='index.html'>&larr; Back to reports index</a></p>",
        "<p><a href='../index.html'>&larr; Back to main dashboard</a></p>",
        "</body>",
        "</html>",
    ]

    outfile.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] generated report: {outfile}")

<<<<<<< HEAD
    # latest.json
=======
    # --- latest.json for dashboard ---
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    DATA_DIR.mkdir(exist_ok=True)
    latest: Dict = {
        "date": today,
        "generated_at_utc": generated_at,
        "ofgem": ofgem,
        "agile": agile,
    }
    if typical_bill:
        latest["typical_bill"] = typical_bill
    if cap_change:
        latest["ofgem"]["change"] = cap_change

    latest_path = DATA_DIR / "latest.json"
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    print(f"[ok] wrote {latest_path}")

<<<<<<< HEAD
    # history json for frontend chart
=======
    # --- write cap history json for trend chart ---
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    history_path = DATA_DIR / "ofgem_history.json"
    history_path.write_text(json.dumps(cap_history, indent=2), encoding="utf-8")
    print(f"[ok] wrote {history_path}")

<<<<<<< HEAD
    # update reports index
=======
    # --- update reports index ---
>>>>>>> 4448ace (Add Astro frontend project (before rebase))
    append_report_link(today, ofgem, agile, typical_bill)
