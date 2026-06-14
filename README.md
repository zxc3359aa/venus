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

The local MVP never performs external actions. Public replies, publishing, lead routing, and ad spend remain approval-gated future integrations.
