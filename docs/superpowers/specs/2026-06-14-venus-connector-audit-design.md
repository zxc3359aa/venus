# Venus Connector Audit Design

Date: 2026-06-14

## Purpose

This slice adds a local dry-run connector audit contract for Venus. It centralizes pre-launch readiness checks for external surfaces such as Douyin, Douyin Shop, Feishu, WeChat, Enterprise WeChat, Qianchuan, Xingtu, Airtable, memory storage, and backups.

It supports the user's goal for Venus to become fully automatic without leaking privacy or accidentally touching live accounts. Before any live connector is enabled, Venus should know which permissions are missing, which audit logs and rollback controls exist, which data classes are involved, and which approvals are required.

## Data Source

The first input shape is `data/samples/connectors.json`.

It may contain:

- `reviewed_at` and `source`.
- `live_connector_requested` for future live enablement review.
- `connectors` with connector ID, surface, connector type, desired workflows, status, required permissions, granted permissions, secret references, audit log state, rollback state, data classes, approval level, and evidence IDs.

The source is labeled as manual or local export. It must not contain raw access tokens, app secrets, customer data, payment data, or live session cookies.

## Output

`build_connector_audit_report(payload)` returns:

- `workflow: connectors`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for connectors, ready connectors, blocked connectors, missing permissions, missing audit logs, missing rollback plans, high-risk connectors, approval-gated connectors, and approval records.
- `connector_reviews` with status, risk level, missing permissions, audit readiness, rollback readiness, approval state, and execution state.
- `permission_matrix` grouped by connector.
- `readiness_gaps` sorted by severity.
- `launch_sequence` containing only connectors that are ready enough for future manual enablement.
- `approval_records` for live connector enablement and high-risk connector review.
- `external_actions: []`.

The CLI supports:

```bash
venus connectors data/samples/connectors.json
```

The Feishu dry-run adapter supports:

```text
/venus connectors
```

Agent Run also summarizes connector readiness when the payload includes `connectors`.

## Approval Boundaries

- Live connector enablement requires manual approval.
- Connectors with approval level 2 or higher remain `blocked_until_approved`.
- Connectors missing permissions, audit logs, or rollback plans are excluded from `launch_sequence`.
- No token is written, no app is configured, no API call is made, no platform read/write happens, and no account state changes.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like keys are redacted from outputs.
- Secret references are allowed as names such as `VENUS_FEISHU_APP_ID`; raw secret values are not allowed in samples.
- Outputs keep `external_actions: []`.
- Future live connector enablement must add credential storage rules, run locks, audit log writes, rollback commands, rate limits, permission checks, and approval IDs before any side effect.

## Testing

Acceptance requires:

- Unit tests for connector review, permission gap detection, audit/rollback checks, readiness gaps, launch sequence, approval records, redaction, and isolation.
- CLI smoke test for `venus connectors`.
- Feishu dry-run test for `/venus connectors`.
- Agent Run test proving connector readiness summaries are included in the operating cycle.
- Full `pytest -v` pass.
