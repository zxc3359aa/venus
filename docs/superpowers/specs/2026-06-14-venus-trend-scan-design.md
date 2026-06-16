# Venus Trend Scan Design

Date: 2026-06-14

## Purpose

This slice adds the first structured trend-scanning contract for Venus. It normalizes Douyin beauty/skincare signals across hot topics, products, creators, comments, ingredients, tags, and controversies, then ranks them into a report that can drive analysis, script writing, production, and monitoring workflows.

It supports the user's requirement that Venus watches beauty/skincare trends all day, extracts professional insight, and turns hot signals into shooting and copywriting direction. The first version stays dry-run and local, so it does not claim live Douyin access before account permissions and connector controls exist.

## Data Source

The first input shape is `data/samples/trend_scan.json`.

It may contain:

- Hot topics with mentions, growth, controversy, and evidence IDs.
- Hot products with brand/product labels and trend metrics.
- Hot creators with handle-level trend metrics.
- Hot comments with likes, growth, controversy, and evidence IDs.
- Hot ingredients with mentions, growth, and controversy.
- Hot tags with mentions, growth, and controversy.
- Controversies with risk labels, mentions, growth, and evidence IDs.
- Refresh cadence and live-connector intent.

The source is labeled as manual/imported Douyin beauty scan data. Live Douyin search, login, browser automation, scraping, or API access remains disabled in this slice.

## Output

`build_trend_scan_report(payload)` returns:

- `workflow: trend_scan`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for signal count, category coverage, content opportunities, refresh interval, and approval-gated actions.
- `normalized_signals` with signal type, label, volume, growth, controversy, score, priority, evidence, and source bucket.
- `leaderboard` ordered by priority score.
- `trend_clusters` that connect the top signal with related products, creators, comments, ingredients, tags, and controversies.
- `content_opportunities` with hook, angle, filming advice, comment prompt, and completion-rate levers.
- `watch_plan` with refresh cadence, required coverage targets, gap alerts, live connector state, and storage namespace.
- `approval_records` when live connector enablement is requested.
- `external_actions: []`.

The CLI supports:

```bash
venus trend-scan data/samples/trend_scan.json
```

The Feishu dry-run adapter supports:

```text
/venus trend-scan
```

Agent Run also summarizes trend scanning when the payload includes `trend_scan`.

## Approval Boundaries

- Local trend normalization and content opportunities are level 1 internal analysis.
- Enabling live all-day Douyin trend scanning is level 2 and requires manual approval.
- Public replies, publishing, platform reads with credentials, browser automation, and paid data access are not executed by this workflow.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like fields are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live scanning must add credential validation, rate limits, source logs, privacy review, account ownership checks, error handling, and connector rollback controls.

## Testing

Acceptance requires:

- Unit tests for all seven signal categories, scoring, leaderboard, clusters, content opportunities, watch plan, approval records, redaction, and isolation.
- CLI smoke test for `venus trend-scan`.
- Feishu dry-run test for `/venus trend-scan`.
- Agent Run test proving trend scan summaries are included in the operating cycle.
- Full `pytest -v` pass.
