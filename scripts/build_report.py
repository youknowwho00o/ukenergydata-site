from pathlib import Path
from datetime import datetime
from typing import Dict

from .fetch_ofgem import fetch_ofgem_cap_summary
from .fetch_octopus import fetch_agile_rates_for_today, summarize_agile

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"


def ensure_reports_index():
    """
    若 reports/index.html 不存在，创建一个简单的列表页骨架。
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    index_file = REPORTS_DIR / "index.html"
    if not index_file.exists():
        index_file.write_text(
            "<!DOCTYPE html><html><head>"
            "<meta charset='utf-8'/>"
            "<title>UK Energy Data – Daily Reports</title>"
            "<style>"
            "body{font-family:system-ui,-apple-system,BlinkMacSystemFont,sans-serif;"
            "background:#020712;color:#f5f5f7;padding:24px;max-width:800px;margin:0 auto;}"
            "a{color:#35c1ff;text-decoration:none;}"
            "a:hover{text-decoration:underline;}"
            "h1{font-size:24px;margin-bottom:4px;}"
            "ul{padding-left:18px;}"
            "</style></head><body>"
            "<h1>Daily Energy Price Reports</h1>"
            "<p>Auto-generated snapshots of UK energy prices.</p>"
            "<ul id='list'></ul>"
            "<script>"
            "fetch('./').then(r=>r.text()).then(()=>{});"
            "</script>"
            "</body></html>",
            encoding="utf-8",
        )


def append_report_link(date_str: str):
    """
    在 reports/index.html 中追加一条报告链接（若不存在时）。
    非严格 HTML parser，只做简单字符串插入。
    """
    index_file = REPORTS_DIR / "index.html"
    if not index_file.exists():
        ensure_reports_index()

    html = index_file.read_text(encoding="utf-8")
    marker = "<ul id='list'>"
    link_line = f"<li><a href='{date_str}.html'>{date_str} – Daily report</a></li>"

    if link_line in html:
        return

    if marker in html:
        parts = html.split(marker)
        html = parts[0] + marker + "\n" + link_line + parts[1]
    else:
        # 极端兜底：直接在末尾加
        html = html.replace("</body>", f"<ul>{link_line}</ul></body>")

    index_file.write_text(html, encoding="utf-8")


def build_daily_report():
    REPORTS_DIR.mkdir(exist_ok=True)
    ensure_reports_index()

    today = datetime.utcnow().date().isoformat()
    outfile = REPORTS_DIR / f"{today}.html"

    ofgem = fetch_ofgem_cap_summary()
    agile_raw = fetch_agile_rates_for_today()
    agile = summarize_agile(agile_raw)

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # 简单 HTML 报告
    lines = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'/>",
        f"<title>UK Energy Data – Daily Report {today}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,BlinkMacSystemFont,sans-serif;"
        "background:#020712;color:#f5f5f7;padding:24px;max-width:800px;margin:0 auto;}",
        "h1{font-size:24px;margin-bottom:4px;}",
        "h2{font-size:18px;margin-top:18px;}",
        "p,li{font-size:13px;line-height:1.6;}",
        "a{color:#35c1ff;text-decoration:none;}",
        "a:hover{text-decoration:underline;}",
        "code{font-size:12px;background:#111827;padding:2px 4px;border-radius:4px;}",
        "</style>",
        "</head><body>",
        f"<h1>Daily Energy Price Report – {today}</h1>",
        f"<p>Auto-generated at <code>{generated_at}</code>.</p>",
        "<h2>Ofgem price cap snapshot (sample)</h2>",
        f"<p>Period: <strong>{ofgem['period']}</strong></p>",
        f"<ul>",
        f"<li>Electricity unit rate (avg): {ofgem['electricity_unit_avg']} p/kWh</li>",
        f"<li>Gas unit rate (avg): {ofgem['gas_unit_avg']} p/kWh</li>",
        f"<li>Electricity standing charge (avg): £{ofgem['elec_standing_avg']}/day</li>",
        f"<li>Gas standing charge (avg): £{ofgem['gas_standing_avg']}/day</li>",
        "</ul>",
        "<h2>Octopus Agile electricity – today</h2>",
    ]

    if agile["has_data"]:
        lines += [
            "<ul>",
            f"<li>Average rate: <strong>{agile['avg']:.3f} p/kWh</strong></li>",
            f"<li>Lowest half-hour: {agile['low']:.3f} p/kWh</li>",
            f"<li>Highest half-hour: {agile['high']:.3f} p/kWh</li>",
            "</ul>",
            "<p>Cheapest slots:</p>",
            "<ul>",
        ]
        for slot in agile["cheapest_slots"]:
            lines.append(f"<li>{slot}</li>")
        lines.append("</ul>")
    else:
        lines.append("<p>Agile data not available for this day.</p>")

    lines += [
        "<h2>Notes</h2>",
        "<ul>",
        "<li>All values are approximate and for informational use only.</li>",
        "<li>Ofgem figures shown here are placeholders until live parsing is enabled.</li>",
        "<li>Agile rates are fetched from the official Octopus public API when available.</li>",
        "</ul>",
        "<p><a href='./index.html'>&larr; Back to all reports</a></p>",
        "<p><a href='../index.html'>&larr; Back to main dashboard</a></p>",
        "</body></html>",
    ]

    outfile.write_text("\n".join(lines), encoding="utf-8")

    append_report_link(today)
    print(f"[ok] generated report: {outfile}")
