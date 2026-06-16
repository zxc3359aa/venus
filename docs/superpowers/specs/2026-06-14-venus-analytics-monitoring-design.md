# Venus Analytics Monitoring Design

Date: 2026-06-14

## Purpose

Phase 8 adds the first local analytics and monitoring core for Venus. It turns imported competitor, video, live, ad, comment, topic, and risk signals into a concise operating dashboard that helps the user decide what to film, what to watch, what to avoid, and where a future Douyin or ad connector should plug in.

This phase is a local, dry-run analytics layer. It does not call Douyin, Qianchuan, Xingtu, WeChat, Feishu, Airtable, or any live account API.

## Dashboard Brief

Primary audience: the user running a Douyin skincare creator account.

Operating question: "Which competitor and content signals deserve attention today, and what should Venus recommend next?"

Default view:

- Hero metrics for monitored competitors, videos, average completion, average engagement, ad density, live hours, and risk count.
- Competitor leaderboard with completion, engagement, ad ratio, live intensity, and risk count.
- Opportunity list for filming, comment prompts, live topics, and ad-learning ideas.
- Risk watchlist for controversy, high-risk claims, suspicious comments, or commercial density.
- Source coverage and approval boundary notes.

## Metric Model

Primary KPI:

- `growth_signal_score`: weighted score combining completion rate, engagement rate, live intensity, and manageable ad signal while penalizing risk.

Driver metrics:

- `avg_completion_rate`: average video completion rate.
- `avg_engagement_rate`: likes, comments, and shares divided by views.
- `ad_ratio`: share of competitor videos marked as ads.
- `live_hours`: total live duration in hours.
- `risk_count`: count of controversies, risky claims, and high-risk comments.

Guardrails:

- All recommendations are internal drafts and approval level 1 unless they imply money, public reply, publishing, or brand commitment.
- Ad strategy suggestions are learning notes only, not Qianchuan budget changes.
- Risky skincare claims and public replies remain approval-gated.

## Data Contract

The local workflow accepts JSON with:

- `competitors`: list of accounts.
- Each competitor may include `handle`, `followers`, `videos`, `live_sessions`, `notes`, and `source`.
- Each video may include `title`, `views`, `likes`, `comments`, `shares`, `completion_rate`, `is_ad`, `topic`, `ingredients`, `controversies`, and `high_risk_comments`.

Missing optional fields default to zero or an empty list. Missing competitors is an error because the dashboard cannot monitor an empty set.

## Output Contract

`build_monitoring_report(payload)` returns:

- `summary`: dashboard hero metrics.
- `leaderboard`: competitor rows sorted by `growth_signal_score`.
- `opportunities`: prioritized operating recommendations.
- `risk_watchlist`: ranked risks with account, topic, level, and reason.
- `approval_boundary`: reminder that no external action is taken.
- `source_coverage`: imported source count and freshness hints.

The orchestrator wraps the report with the same Venus contract used by other workflows:

- `workflow: "monitoring"`
- `approval_mode: "manual"`
- `external_actions: []`
- `result: <monitoring report>`

## Testing

Phase 8 is accepted when:

- Unit tests prove score calculation, leaderboard ordering, opportunities, and risk watchlist behavior.
- Orchestrator routes `monitoring`.
- CLI smoke command `venus monitoring data/samples/competitors.json` returns JSON with `external_actions: []`.
- Full `pytest -v` passes.
