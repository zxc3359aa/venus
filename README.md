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

Build a local Douyin comment and live-message engagement report:

```bash
venus douyin data/samples/douyin_engagement.json
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

Build a local short-video production and editing package:

```bash
venus production data/samples/video_production.json
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
It also supports `/venus product-intel` to preview brand backing, filing checks, ingredient risk, supplier documents, test reports, controversies, and product retrieval tasks without live product-data reads.
It also supports `/venus douyin` to preview comment and live-message reply queues without touching Douyin.
It also supports `/venus wechat` to preview Mini Program answer and Enterprise WeChat handoff queues without touching WeChat.
It also supports `/venus commercial` to preview Qianchuan budget guardrails and Xingtu brief reviews without touching ad accounts or brand tasks.
It also supports `/venus improvement` to preview learning candidates, defect guardrails, and backup verification tasks without changing memory, code, or backups.
It also supports `/venus production` to preview scripts, shot lists, editing timelines, subtitles, and publishing drafts without rendering or publishing video.
It also supports `/venus trend-scan` to preview Douyin beauty/skincare hot topics, products, creators, comments, ingredients, tags, controversies, and refresh gaps without live platform reads.
It also supports `/venus agent-run` to preview the next Venus operating cycle and pending approval records.

The local MVP never performs external actions. Public replies, publishing, lead routing, and ad spend remain approval-gated future integrations.
