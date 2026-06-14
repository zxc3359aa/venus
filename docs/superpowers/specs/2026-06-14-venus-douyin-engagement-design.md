# Venus Douyin Engagement Design

Date: 2026-06-14

## Purpose

This slice adds the first Douyin engagement connector contract for Venus. It focuses on imported or manually exported comments and live messages so Venus can summarize risk, draft professional replies, and prepare approval queues before any live Douyin API permission is connected.

It directly supports the user's goal for Venus to read every video comment, summarize what audiences are asking, and help reply scientifically and professionally. In this version, all public-facing behavior is dry-run only.

## Data Source

The first input shape is `data/samples/douyin_engagement.json`.

It may contain:

- `videos` with video IDs, titles, publish times, and comments.
- `live_sessions` with live session IDs and messages.
- `persona_samples` for reply style.
- `source` and `retrieved_at` metadata.

The source is labeled as manual or local export. It must not claim to be live Douyin API data.

## Output

`build_douyin_engagement_report(payload)` returns:

- `workflow: douyin`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for videos, comments, live sessions, live messages, high-risk items, and approval-gated replies.
- Per-video comment summaries.
- `reply_queue` for video comments.
- `live_queue` for live messages.
- `approval_records` for public or live replies requiring approval.
- `external_actions: []`.

The CLI supports:

```bash
venus douyin data/samples/douyin_engagement.json
```

The Feishu dry-run adapter supports:

```text
/venus douyin
```

Agent Run also summarizes Douyin engagement when the payload includes `douyin_engagement`.

## Approval Boundaries

- Comment reply drafts are public platform actions and use approval level 3 when risk is high.
- Live-message reply drafts are treated as approval level 4 in dry-run because they are real-time public interaction.
- No reply, pin, publish, user interaction, or live message is executed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like keys and user identifiers are redacted or omitted from outputs.
- Outputs keep `external_actions: []`.
- Future live Douyin API usage must add permission checks, audit logs, rollback notes, rate limits, and approval records before any side effect.

## Testing

Acceptance requires:

- Unit tests for comment/live summaries, reply queues, approval levels, approval records, redaction, and isolation.
- CLI smoke test for `venus douyin`.
- Feishu dry-run test for `/venus douyin`.
- Agent Run test proving Douyin engagement is summarized in the operating cycle.
- Full `pytest -v` pass.
