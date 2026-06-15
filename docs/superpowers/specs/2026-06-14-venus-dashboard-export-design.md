# Venus Dashboard Export Design

Date: 2026-06-14

## Purpose

This slice adds a portable local dashboard for Venus operations. It turns the existing local analytics, monitoring, and Airtable-ready data into a static HTML dashboard that can be opened in a browser without live Douyin, Airtable, Feishu, Qianchuan, Xingtu, WeChat, or BI access.

The dashboard is a dry-run operating surface, not a production BI tool. It is meant to make the current Venus loop readable: what is hot, which products are risky, which comments need approval, which competitors are worth studying, and what actions Venus recommends next.

## Data Source

The first dashboard reads a local payload shaped like `data/samples/airtable_export.json`. It uses the same functions already verified by the CLI:

- Hotspot scoring.
- Product risk analysis.
- Comment triage and reply approval levels.
- Competitor monitoring and opportunities.
- Airtable-ready table packaging.

The source is explicitly labeled as `manual-import` or sample data. The dashboard must not claim to be live Douyin or live Airtable data.

## Output

`build_dashboard_html(payload)` returns a dictionary with:

- `html`: complete static HTML.
- `summary`: dashboard metrics.
- `external_actions: []`.

The CLI supports:

```bash
venus dashboard data/samples/airtable_export.json reports/venus-dashboard.html
```

When an output path is supplied, the CLI writes the HTML file and prints a JSON status. If no output path is supplied, the CLI prints the HTML in the JSON payload.

## Layout

The HTML dashboard uses a restrained operating dashboard layout:

- Header with title, source status, and dry-run boundary.
- KPI cards for table count, record count, high-risk comments, high-risk products, competitors, and opportunities.
- Bar-style visual summaries for competitor growth score, comment approval levels, and product risk.
- Detail tables for hotspots, products, comments, competitors, monitoring opportunities, and approvals.
- Visible source and safety notes.

The design should be neutral, dense, and scan-friendly rather than a marketing landing page. It uses no external JavaScript, no external CSS, and no external network assets.

## Safety

- No external action is taken.
- No secrets are rendered.
- Public replies, publishing, lead routing, ad spend, and live connector writes remain approval-gated.
- Venus and Xiaolongxia isolation remains unchanged.

## Testing

Acceptance requires:

- Unit tests that parse generated HTML and confirm expected sections, metrics, dry-run notes, and escaped user-provided text.
- CLI test that writes a dashboard file and returns JSON with `external_actions: []`.
- Full `pytest -v` pass.
- Manual local HTML smoke command succeeds.
