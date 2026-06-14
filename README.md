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

Analyze comments and draft approval-gated replies:

```bash
venus comments data/samples/comments.json
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
It also supports `/venus douyin` to preview comment and live-message reply queues without touching Douyin.
It also supports `/venus wechat` to preview Mini Program answer and Enterprise WeChat handoff queues without touching WeChat.
It also supports `/venus agent-run` to preview the next Venus operating cycle and pending approval records.

The local MVP never performs external actions. Public replies, publishing, lead routing, and ad spend remain approval-gated future integrations.
