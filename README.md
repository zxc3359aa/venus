# Venus

Venus is a beauty and skincare agent system for content intelligence, product research, persona learning, approval-gated reply drafting, and future platform integrations.

The first implementation slice runs locally and does not touch live Douyin, Feishu, WeChat, Qianchuan, Xingtu, Airtable, or Enterprise WeChat accounts.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Smoke Commands

Run all tests:

```bash
pytest -v
```

Generate a hotspot brief:

```bash
venus hotspot data/samples/hotspots.json
```

Generate a product research card:

```bash
venus product data/samples/products.json
```

Build a deep product intelligence dossier:

```bash
venus product-intel data/samples/product_intelligence.json
```

Analyze comments and draft approval-gated replies:

```bash
venus comments data/samples/comments.json
```

Build a local Douyin beauty trend scan report:

```bash
venus trend-scan data/samples/trend_scan.json
```

Build a local competitor monitoring report:

```bash
venus monitoring data/samples/competitors.json
```

Build a local Airtable-ready operations export:

```bash
venus airtable data/samples/airtable_export.json
```

Build a local approval inbox:

```bash
venus approvals data/samples/approvals.json
```

Build a local approval decision ledger draft:

```bash
venus approval-ledger data/samples/approval_ledger.json
```

Preview the local approval decision archive gate:

```bash
venus approval-archive data/samples/approval_archive.json
```

Build a local Douyin comment and live-message engagement report:

```bash
venus douyin data/samples/douyin_engagement.json
```

Build a local Douyin ecommerce operations report:

```bash
venus ecommerce data/samples/ecommerce.json
```

Build a local WeChat Mini Program Q&A and Enterprise WeChat handoff report:

```bash
venus wechat data/samples/wechat_private_domain.json
```

Build a local Qianchuan and Xingtu commercial strategy report:

```bash
venus commercial data/samples/commercial_strategy.json
```

Build a local self-improvement, regression, and backup verification report:

```bash
venus improvement data/samples/self_improvement.json
```

Build a local versioned memory review report:

```bash
venus memory data/samples/memory.json
```

Build a local 24-hour scheduler run plan:

```bash
venus scheduler data/samples/scheduler.json
```

Build a local connector readiness audit:

```bash
venus connectors data/samples/connectors.json
```

Build a local short-video production and editing package:

```bash
venus production data/samples/video_production.json
```

Build a local pre-publish content quality evaluation:

```bash
venus content-eval data/samples/content_eval.json
```

Build a local content performance calibration report:

```bash
venus performance data/samples/performance.json
```

Build a local Agent Run eval gate report:

```bash
venus evals data/samples/evals.json
```

Build a local approval-gated Agent Run plan:

```bash
venus agent-run data/samples/agent_run.json
```

Build a local static operations dashboard:

```bash
venus dashboard data/samples/airtable_export.json reports/venus-dashboard.html
```

Run the local Feishu dry-run entry:

```bash
venus feishu data/samples/feishu_message.json
```

This command parses a Feishu-like `/venus` message and returns a card-ready JSON draft. It does not send Feishu messages or perform external actions.

The Feishu dry-run entry also supports `/venus monitoring` when the local `data/samples/competitors.json` sample is present.
It also supports `/venus airtable` to preview the Airtable-ready operations package without writing to Airtable.
It also supports `/venus approvals` to preview the pending approval inbox and recorded-only decision intents without applying approvals.
It also supports `/venus approval-ledger` to preview deduplicated approval decision ledger entries, write plans, and rollback plans without writing storage.
It also supports `/venus approval-archive` to preview the local approval archive gate; approved low-risk entries can be persisted only through the isolated Venus JSON store, with no platform actions.
It also supports `/venus product-intel` to preview brand backing, filing checks, ingredient risk, supplier documents, test reports, controversies, and product retrieval tasks without live product-data reads.
It also supports `/venus douyin` to preview comment and live-message reply queues without touching Douyin.
It also supports `/venus ecommerce` to preview product catalog checks, inventory alerts, live product-card plans, promotions, and after-sales risk without touching shop, order, price, coupon, or inventory state.
It also supports `/venus wechat` to preview Mini Program answer and Enterprise WeChat handoff queues without touching WeChat.
It also supports `/venus commercial` to preview Qianchuan budget guardrails and Xingtu brief reviews without touching ad accounts or brand tasks.
It also supports `/venus improvement` to preview learning candidates, defect guardrails, and backup verification tasks without changing memory, code, or backups.
It also supports `/venus memory` to preview versioned memory merges, rollback plans, privacy blocks, and backup checks without writing long-term memory.
It also supports `/venus scheduler` to preview a 24-hour run queue, blocked connector jobs, approval-gated jobs, and private operator digests without starting timers or platform actions.
It also supports `/venus connectors` to preview connector permissions, audit logs, rollback gaps, and launch sequence without configuring live apps.
It also supports `/venus production` to preview scripts, shot lists, editing timelines, subtitles, and publishing drafts without rendering or publishing video.
It also supports `/venus content-eval` to preview retention, interaction, comment, follow, persona, evidence, and claim-safety gates without publishing video.
It also supports `/venus performance` to preview video metric winners, underperformers, calibration rules, and next-content actions without reading live Douyin metrics.
It also supports `/venus evals` to preview Agent Run safety gates before live autopilot, connector writes, memory writes, replies, publishing, or ad spend are considered.
It also supports `/venus trend-scan` to preview Douyin beauty/skincare hot topics, products, creators, comments, ingredients, tags, controversies, and refresh gaps without live platform reads.
It also supports `/venus agent-run` to preview the next Venus operating cycle and pending approval records.

The local MVP never performs external actions. Public replies, publishing, lead routing, and ad spend remain approval-gated future integrations.
