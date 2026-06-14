# Venus Ecommerce Design

Date: 2026-06-14

## Purpose

This slice adds the first Douyin ecommerce operations contract for Venus. It focuses on local or manually exported shop, product, live-room, promotion, and after-sales signals so Venus can prepare conversion recommendations without changing shop state.

It supports the user's goal for Venus to later connect to Douyin ecommerce and live commerce while keeping product cards, prices, coupons, inventory, orders, refunds, and after-sales actions behind explicit approval gates.

## Data Source

The first input shape is `data/samples/ecommerce.json`.

It may contain:

- `shop` metadata.
- `products` with prices, stock, target stock, margin, commission, conversion, return rate, claim risk, and evidence IDs.
- `live_rooms` with planned products and product-card performance.
- `promotions` with coupon, price, or budget suggestions.
- `after_sales` issues and severities.
- `source`, `retrieved_at`, and `live_connector_requested` metadata.

The source is labeled as manual or local export. It must not claim to be live Douyin Shop API data.

## Output

`build_ecommerce_report(payload)` returns:

- `workflow: ecommerce`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for products, low stock, high returns, live rooms, promotions, after-sales issues, conversion recommendations, and approval-gated actions.
- `catalog_checks` for product evidence, risk, stock, margin, conversion, and return signals.
- `inventory_alerts` for products below target stock thresholds.
- `pricing_recommendations` with manual approval boundaries.
- `live_product_card_plan` with manual approval boundaries.
- `after_sales_watchlist`.
- `conversion_recommendations`.
- `approval_records` for connector enablement, product-card updates, and promotion or price changes.
- `external_actions: []`.

The CLI supports:

```bash
venus ecommerce data/samples/ecommerce.json
```

The Feishu dry-run adapter supports:

```text
/venus ecommerce
```

Agent Run also summarizes ecommerce when the payload includes `ecommerce`.

## Approval Boundaries

- Live ecommerce connector enablement requires approval and credential review.
- Product-card order, title, selling point, or live-room changes require approval.
- Promotion, coupon, price, budget, margin, inventory, order, refund, and after-sales actions require approval.
- No ecommerce connector, product-card update, price change, coupon change, inventory write, order action, refund action, or after-sales action is executed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like keys are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live Douyin ecommerce usage must add permission checks, audit logs, rollback notes, rate limits, privacy filtering, and approval records before any side effect.

## Testing

Acceptance requires:

- Unit tests for catalog checks, inventory alerts, pricing recommendations, live product-card plans, after-sales watchlists, approval records, redaction, and isolation.
- CLI smoke test for `venus ecommerce`.
- Feishu dry-run test for `/venus ecommerce`.
- Agent Run test proving ecommerce is summarized in the operating cycle.
- Full `pytest -v` pass.
