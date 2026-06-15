# Venus WeChat Private-Domain Design

Date: 2026-06-14

## Purpose

This slice adds the first WeChat private-domain connector contract for Venus. It models Mini Program skincare Q&A and Enterprise WeChat handoff flows from local/manual imports so Venus can triage questions, draft safe answers, and prepare customer handoff queues before any live WeChat or Enterprise WeChat permission is connected.

It supports the user's goal for Venus to answer skincare questions in a Mini Program and guide qualified users into Enterprise WeChat while preserving privacy, compliance, and approval control.

## Data Source

The first input shape is `data/samples/wechat_private_domain.json`.

It may contain:

- Mini Program sessions.
- User skincare questions.
- Session-level display metadata such as nickname.
- Optional source and retrieval metadata.
- Optional private contact fields, which must be redacted or omitted from outputs.

The source is labeled as manual or local export. It must not claim to be live WeChat API data.

## Output

`build_wechat_private_domain_report(payload)` returns:

- `workflow: wechat`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for sessions, questions, high-risk questions, lead intent, Enterprise WeChat handoffs, and approval-gated actions.
- `answer_queue` for Mini Program answer drafts.
- `handoff_queue` for Enterprise WeChat routing drafts.
- `approval_records` for risky answers and customer-routing actions.
- `external_actions: []`.

The CLI supports:

```bash
venus wechat data/samples/wechat_private_domain.json
```

The Feishu dry-run adapter supports:

```text
/venus wechat
```

Agent Run also summarizes WeChat private-domain work when the payload includes `wechat_private_domain`.

## Approval Boundaries

- Mini Program answers are external private communication and are approval-gated.
- High-risk skincare advice, medical-like questions, and customer-routing actions use approval level 4.
- Enterprise WeChat handoff drafts never add contacts, send messages, join groups, route leads, or expose private contact details in this slice.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like fields, OpenIDs, union IDs, phone numbers, WeChat IDs, and contact objects are redacted or omitted from outputs.
- Outputs keep `external_actions: []`.
- Future live WeChat usage must add permission checks, audit logs, explicit consent capture, rollback notes, and approval records before any side effect.

## Testing

Acceptance requires:

- Unit tests for Q&A summaries, answer queues, handoff queues, approval levels, approval records, redaction, and isolation.
- CLI smoke test for `venus wechat`.
- Feishu dry-run test for `/venus wechat`.
- Agent Run test proving WeChat private-domain summaries are included in the operating cycle.
- Full `pytest -v` pass.
