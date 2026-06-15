from __future__ import annotations

from html import escape
from typing import Any

from venus.airtable_export import build_airtable_sync_package


def build_dashboard_html(payload: dict[str, Any]) -> dict[str, Any]:
    package = build_airtable_sync_package(payload)
    tables = {table["name"]: table for table in package["tables"]}
    summary = _dashboard_summary(package, tables)
    html = _render_dashboard(package, tables, summary)
    return {
        "html": html,
        "summary": summary,
        "external_actions": [],
    }


def _dashboard_summary(
    package: dict[str, Any],
    tables: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    comments = _records(tables, "Comments")
    products = _records(tables, "Products")
    competitors = _records(tables, "Competitors")
    opportunities = _records(tables, "Monitoring Opportunities")

    return {
        "table_count": package["summary"]["table_count"],
        "record_count": package["summary"]["record_count"],
        "high_risk_comments": sum(
            1 for record in comments if record["fields"].get("Approval Level", 0) >= 3
        ),
        "high_risk_products": sum(
            1 for record in products if record["fields"].get("Risk Level") == "high"
        ),
        "competitor_count": len(competitors),
        "opportunity_count": len(opportunities),
        "dry_run": package["dry_run"],
    }


def _render_dashboard(
    package: dict[str, Any],
    tables: dict[str, dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    base = package["base"]
    safety_notes = package["sync_boundary"]["notes"]
    sections = [
        _render_table_section(tables, "Hotspots", ["Topic", "Type", "Score", "Controversy", "Is Top Topic"]),
        _render_table_section(tables, "Products", ["Product", "Risk Level", "Evidence Confidence", "Forbidden Claims"]),
        _render_table_section(tables, "Comments", ["Comment ID", "Risk", "Approval Level", "Intent", "Text"]),
        _render_competitor_section(tables),
        _render_table_section(
            tables,
            "Monitoring Opportunities",
            ["Action Type", "Priority", "Based On", "Recommendation"],
        ),
        _render_table_section(tables, "Approvals", ["Action Type", "Approval Level", "Status", "Reviewer"]),
    ]

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Venus Operations Dashboard</title>",
            "<style>",
            _css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="shell">',
            '<header class="topbar">',
            "<div>",
            '<p class="eyebrow">Venus / Local dry-run</p>',
            "<h1>Venus Operations Dashboard</h1>",
            f"<p>{_e(base['description'])}</p>",
            "</div>",
            '<div class="status-pill" id="external-actions-empty">external_actions: []</div>',
            "</header>",
            _render_kpis(summary),
            _render_visual_summary(tables),
            *sections,
            '<section class="panel">',
            "<h2>Sources And Safety</h2>",
            '<div class="note-grid">',
            f"<p><strong>Base:</strong> {_e(base['name'])}</p>",
            f"<p><strong>Namespace:</strong> {_e(base['namespace'])}</p>",
            *[f"<p>{_e(note)}</p>" for note in safety_notes],
            "<p>Current source is local imported sample data, not live Douyin or live Airtable.</p>",
            "</div>",
            "</section>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def _render_kpis(summary: dict[str, Any]) -> str:
    cards = [
        ("Tables", summary["table_count"], "Airtable-ready operating surfaces"),
        ("Records", summary["record_count"], "Rows available for review"),
        ("High-Risk Comments", summary["high_risk_comments"], "Need approval before public reply"),
        ("High-Risk Products", summary["high_risk_products"], "Need careful evidence language"),
        ("Competitors", summary["competitor_count"], "Accounts in current monitor"),
        ("Opportunities", summary["opportunity_count"], "Action ideas queued"),
    ]
    return "\n".join(
        [
            '<section class="kpi-grid" aria-label="Dashboard summary">',
            *[
                (
                    '<article class="kpi-card">'
                    f"<span>{_e(label)}</span>"
                    f"<strong>{_e(value)}</strong>"
                    f"<p>{_e(caption)}</p>"
                    "</article>"
                )
                for label, value, caption in cards
            ],
            "</section>",
        ]
    )


def _render_visual_summary(tables: dict[str, dict[str, Any]]) -> str:
    competitors = _records(tables, "Competitors")
    products = _records(tables, "Products")
    comments = _records(tables, "Comments")
    max_score = max(
        [float(record["fields"].get("Growth Signal Score", 0)) for record in competitors] or [1]
    )
    bars = []
    for record in competitors:
        fields = record["fields"]
        score = float(fields.get("Growth Signal Score", 0))
        bars.append(_bar(str(fields.get("Handle", "")), score, max_score, "score"))
    high_risk_products = sum(1 for record in products if record["fields"].get("Risk Level") == "high")
    approval_gated = sum(1 for record in comments if record["fields"].get("Approval Level", 0) >= 3)
    bars.append(_bar("High-risk products", high_risk_products, max(high_risk_products, 1), "count"))
    bars.append(_bar("Approval-gated comments", approval_gated, max(approval_gated, 1), "count"))
    return "\n".join(
        [
            '<section class="panel">',
            "<h2>Signal Overview</h2>",
            '<div class="bar-stack">',
            *bars,
            "</div>",
            "</section>",
        ]
    )


def _bar(label: str, value: float, maximum: float, suffix: str) -> str:
    width = 0 if maximum <= 0 else min(100, max(4, value / maximum * 100))
    display = f"{value:.1f}" if isinstance(value, float) and not value.is_integer() else str(int(value))
    return (
        '<div class="bar-row">'
        f"<span>{_e(label)}</span>"
        '<div class="bar-track">'
        f'<div class="bar-fill" style="width: {width:.1f}%"></div>'
        "</div>"
        f"<strong>{_e(display)} {_e(suffix)}</strong>"
        "</div>"
    )


def _render_competitor_section(tables: dict[str, dict[str, Any]]) -> str:
    return _render_table_section(
        tables,
        "Competitors",
        ["Handle", "Growth Signal Score", "Avg Completion Rate", "Avg Engagement Rate", "Ad Ratio", "Live Hours"],
    )


def _render_table_section(
    tables: dict[str, dict[str, Any]],
    table_name: str,
    fields: list[str],
) -> str:
    table = tables.get(table_name, {"records": []})
    rows = table.get("records", [])
    return "\n".join(
        [
            '<section class="panel">',
            f"<h2>{_e(table_name)}</h2>",
            '<div class="table-wrap">',
            "<table>",
            "<thead><tr>",
            *[f"<th>{_e(field)}</th>" for field in fields],
            "</tr></thead>",
            "<tbody>",
            *[_render_row(record, fields) for record in rows],
            _empty_row(fields) if not rows else "",
            "</tbody>",
            "</table>",
            "</div>",
            "</section>",
        ]
    )


def _render_row(record: dict[str, Any], fields: list[str]) -> str:
    values = record.get("fields", {})
    return "\n".join(
        [
            "<tr>",
            *[f"<td>{_e(_format_value(values.get(field, '')))}</td>" for field in fields],
            "</tr>",
        ]
    )


def _empty_row(fields: list[str]) -> str:
    return f'<tr><td colspan="{len(fields)}" class="empty">No records yet</td></tr>'


def _records(tables: dict[str, dict[str, Any]], table_name: str) -> list[dict[str, Any]]:
    return list(tables.get(table_name, {}).get("records") or [])


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f7f4ef;
  --ink: #1f2933;
  --muted: #667085;
  --line: #d9d2c5;
  --panel: #fffdf9;
  --accent: #2f7d75;
  --accent-soft: #dcefeb;
  --risk: #b4432f;
}
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.5;
}
.shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 44px;
}
.topbar {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  border-bottom: 1px solid var(--line);
  padding-bottom: 20px;
}
.eyebrow {
  margin: 0 0 4px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  font-size: 30px;
  letter-spacing: 0;
}
h2 {
  margin: 0 0 14px;
  font-size: 18px;
  letter-spacing: 0;
}
p {
  margin: 6px 0 0;
  color: var(--muted);
}
.status-pill {
  flex: 0 0 auto;
  border: 1px solid var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 700;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin: 22px 0;
}
.kpi-card,
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.kpi-card {
  padding: 14px;
  min-height: 116px;
}
.kpi-card span {
  color: var(--muted);
  font-size: 13px;
}
.kpi-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
}
.kpi-card p {
  font-size: 12px;
}
.panel {
  margin-top: 14px;
  padding: 18px;
}
.bar-stack {
  display: grid;
  gap: 10px;
}
.bar-row {
  display: grid;
  grid-template-columns: minmax(130px, 220px) 1fr minmax(72px, auto);
  gap: 12px;
  align-items: center;
  font-size: 13px;
}
.bar-track {
  height: 12px;
  background: #ece6dc;
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: var(--accent);
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th,
td {
  border-bottom: 1px solid var(--line);
  padding: 9px 8px;
  text-align: left;
  vertical-align: top;
}
th {
  color: var(--muted);
  font-weight: 700;
}
.empty {
  color: var(--muted);
  text-align: center;
}
.note-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 18px;
}
@media (max-width: 880px) {
  .topbar,
  .note-grid {
    display: block;
  }
  .status-pill {
    display: inline-block;
    margin-top: 14px;
  }
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .bar-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
@media (max-width: 520px) {
  .shell {
    width: min(100% - 20px, 1180px);
  }
  h1 {
    font-size: 24px;
  }
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
"""
