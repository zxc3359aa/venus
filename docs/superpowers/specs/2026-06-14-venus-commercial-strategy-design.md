# Venus Commercial Strategy Design

Date: 2026-06-14

## Purpose

This slice adds the first commercial strategy contract for Venus. It models Qianchuan ad decision support and Xingtu brand-brief review from local/manual inputs so Venus can recommend budget guardrails, audience/creative diagnostics, and compliant commercial scripts before any live ad account or Xingtu permission is connected.

It supports the user's goal for Venus to improve live-stream ad efficiency, guide Xingtu commercial orders, and write brand-required ad videos in the user's style while preserving budget, reputation, and compliance controls.

## Data Source

The first input shape is `data/samples/commercial_strategy.json`.

It may contain:

- Qianchuan campaign objective, budget, spend, ROI, audience tags, and creative metrics.
- Xingtu brief ID, brand, product, budget, requirements, forbidden claims, and deliverables.
- Persona samples for commercial script tone.
- Source and retrieval metadata.

The source is labeled as manual or local brief data. It must not claim to be live Qianchuan, OceanEngine, or Xingtu API data.

## Output

`build_commercial_strategy_report(payload)` returns:

- `workflow: commercial`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for campaigns, briefs, high-risk briefs, budget recommendations, script recommendations, and approval-gated actions.
- `qianchuan_recommendations` for budget guardrails, audience notes, and creative diagnostics.
- `xingtu_brief_reviews` for claim risk, deliverables, and decision guidance.
- `commercial_script_recommendations` for short-video ad and live-slice script directions.
- `approval_records` for ad spend and brand commitment decisions.
- `external_actions: []`.

The CLI supports:

```bash
venus commercial data/samples/commercial_strategy.json
```

The Feishu dry-run adapter supports:

```text
/venus commercial
```

Agent Run also summarizes commercial strategy when the payload includes `commercial_strategy`.

## Approval Boundaries

- Qianchuan budget recommendations are level 4 and never change spend in this slice.
- Xingtu brief acceptance, rejection, quote, claim commitment, and brand-facing promises are level 4.
- Script recommendations are level 1 internal drafts until the user approves a commercial brief and claim boundaries.
- No budget, campaign, audience, creative, Xingtu order, quote, or brand response is executed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like fields, advertiser IDs, account IDs, and access tokens are redacted or omitted from outputs.
- Outputs keep `external_actions: []`.
- Future live Qianchuan or Xingtu usage must add permission checks, account ownership checks, budget caps, audit logs, rollback/pause plans, and explicit approval records before any side effect.

## Testing

Acceptance requires:

- Unit tests for Qianchuan budget guardrails, Xingtu brief risk review, script recommendations, approval records, redaction, and isolation.
- CLI smoke test for `venus commercial`.
- Feishu dry-run test for `/venus commercial`.
- Agent Run test proving commercial summaries are included in the operating cycle.
- Full `pytest -v` pass.
