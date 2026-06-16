# Venus Performance Calibration Design

## Goal

Add a local dry-run performance calibration workflow that turns published short-video metrics into Venus learning signals. The workflow compares actual completion, comment, follow, share, and negative-feedback rates against target KPI thresholds, then recommends next content moves without reading live Douyin data or publishing anything.

This slice supports Venus' growth loop:

- Use measured video results to learn which hooks, CTAs, topics, and evidence structures should be repeated.
- Detect weak content packages before repeating the same pattern.
- Preserve claim-safety judgment when a high-growth script still had publish-risk blockers.
- Produce Feishu-card-ready summaries and Agent Run summaries so the operator can review on mobile.

## In Scope

- New `performance` workflow implemented by `src/venus/performance.py`.
- CLI command: `venus performance data/samples/performance.json`.
- Feishu command: `/venus performance`.
- Agent Run summary when `performance` is included in `data/samples/agent_run.json`.
- KPI definitions for completion, comment, follow, share, negative feedback, and growth score.
- Approval records for learning-rule adoption and next-content drafting.
- Deterministic local sample data only.

## Out Of Scope

- Live Douyin API reads.
- Automatic data scraping.
- Video publishing, comment replying, ad spend, Feishu sending, WeChat routing, or memory writes.
- Training or fine-tuning a model.

## Input Contract

The payload is a dictionary:

- `source`: expected to describe the local/manual source, such as `manual_douyin_video_metrics`.
- `analyzed_at`: ISO-like timestamp for the local analysis.
- `live_metrics_requested`: boolean flag that records intent but never enables a live connector.
- `targets`: optional thresholds:
  - `completion_rate`
  - `comment_rate`
  - `follow_rate`
  - `negative_feedback_rate`
- `videos`: list of video metric records:
  - `video_id`
  - `title`
  - `topic`
  - `published_at`
  - `views`
  - `completion_rate`
  - `comment_rate`
  - `follow_rate`
  - `share_rate`
  - `negative_feedback_rate`
  - `content_eval_score`
  - `content_eval_status`
  - `hook_type`
  - `cta_type`
  - `persona_fit`
  - `claim_risk`
  - `evidence`

Secret-like keys such as `api_key`, `token`, `password`, and `authorization` are redacted recursively.

## Output Contract

The workflow returns:

- `workflow: performance`.
- `namespace: venus_performance`.
- `dry_run: true`.
- `approval_mode: manual`.
- `source` metadata that clearly says the workflow uses local metrics only.
- `summary` with video counts, averages, alert counts, rule counts, and approval count.
- `targets` used for review.
- `leaderboard` sorted by deterministic `growth_score`.
- `video_reviews` with KPI pass/fail fields.
- `winners` and `underperformers`.
- `calibration_rules`.
- `next_actions`.
- `kpi_definitions`.
- `approval_records`.
- `external_actions: []`.
- `safety_boundary` stating that no connector, publishing, reply, promotion, or memory write occurs.

## KPI Logic

Default target thresholds:

- completion rate: 0.65
- comment rate: 0.03
- follow rate: 0.008
- negative feedback rate: 0.015

A winner must meet completion, comment, and follow targets and stay at or under the negative-feedback target.

An underperformer is any non-winner. Videos above the negative-feedback target are also marked with a negative-feedback alert.

Growth score:

`completion_rate * 40 + comment_rate * 300 + follow_rate * 500 + share_rate * 100 - negative_feedback_rate * 200`

Scores are rounded to one decimal.

Average rates are rounded to three decimals.

## Calibration Rules

The first implementation creates three deterministic rule families when evidence exists:

- `amplify_winning_hook`: repeat the best winning hook/topic pattern.
- `repair_generic_cta`: replace generic CTAs from underperforming videos with specific comment prompts.
- `claim_safety_calibration`: keep claim-safety review active when a high pre-publish score still had a blocked or non-ready status.

Rules do not write to memory automatically. They are proposed learning candidates only.

## Approval And Privacy

The workflow creates approval records when learning rules or next-content actions are proposed:

- `venus_performance_learning_review`
- `venus_performance_next_content_review`

All future live-metric, learning, publishing, Feishu, Douyin, ad, and memory operations remain blocked until approved. The config rejects Xiaolongxia namespaces and enforces `venus_` namespacing.

## Acceptance Criteria

- Unit tests prove KPI summaries, leaderboard ordering, calibration rules, approvals, redaction, and Xiaolongxia isolation.
- CLI smoke test proves `venus performance data/samples/performance.json` returns JSON.
- Feishu test proves `/venus performance` routes to the local sample.
- Agent Run test proves performance summary is included when payload includes `performance`.
- Full test suite passes.
