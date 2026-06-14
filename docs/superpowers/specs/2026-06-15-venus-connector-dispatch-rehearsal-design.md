# Venus Connector Dispatch Rehearsal Design

## Purpose

The connector execution gateway creates local platform execution manifests. This slice adds the next bridge toward safe live integrations: a connector dispatch rehearsal workflow that converts those manifests into platform-specific request drafts, credential-reference checks, audit packets, and rollback notes.

The workflow is still local-only. It does not call Feishu, Airtable, Douyin, WeChat, Qianchuan, Xingtu, OpenAI, backup storage, browsers, mobile apps, or any external API. It creates a reviewable rehearsal artifact that proves what would be dispatched and why it remains blocked.

## Scope

The workflow is named `connector_dispatch`.

It supports request drafts for these surfaces:

- `feishu`: private card send draft.
- `airtable`: record write draft.
- `douyin`: comment/live reply or metric action draft.
- `wechat`: Mini Program answer or Enterprise WeChat handoff draft.
- `qianchuan`: campaign/budget operation draft.
- `xingtu`: brand-task response draft.
- `openai`: Agents SDK/model-run draft.
- `backup`: backup write or verification draft.

Every request draft includes `external_action_enabled: false`.

## Inputs

The workflow accepts a JSON payload:

- `workspace_root`: optional local workspace root. Defaults to `.`.
- `source`: source label.
- `rehearsed_at`: deterministic timestamp.
- `dispatch_requested`: must be true before any local rehearsal record is written.
- `approved_dispatch_review`: must be true before any local rehearsal record is written.
- `live_dispatch_requested`: when true, creates a level-4 owner approval record.
- `execution_records`: optional connector execution records. If omitted, the workflow reads `data/venus/connector_execution_manifests.json`.
- `environment`: safe readiness booleans such as `VENUS_FEISHU_APP_ID_configured`. The workflow never reads secret values from the shell.
- `dispatch_overrides`: optional per-execution request changes. Any override that enables external actions is blocked.

Secret-like payload values are redacted recursively.

## Outputs

The workflow returns:

- `workflow: connector_dispatch`
- `namespace: venus_connector_dispatch`
- `dispatch_state`
- `summary`
- `rehearsal_records`
- `blocked_items`
- `duplicate_items`
- `approval_records`
- `credential_readiness`
- `write_plan`
- `rollback_plan`
- `external_actions: []`
- `safety_boundary`

When both local gates are approved, rehearsal records are written only to `data/venus/connector_dispatch_rehearsals.json`.

## Rehearsal Rules

An execution manifest becomes a rehearsal record only when all of these are true:

- `dispatch_requested` is true.
- `approved_dispatch_review` is true.
- The execution manifest has `execution_state: local_manifest_ready`.
- The execution manifest has `dispatch_state: blocked_until_live_connector_enabled`.
- The execution manifest has `external_action_enabled: false`.
- Its target surface is supported.
- Every `required_secret_ref` is represented by a true environment readiness flag.
- Its effective approval level is below level 4.
- No override attempts to enable an external action.

The rehearsal record includes:

- stable `rehearsal_id`
- execution, draft, outbox, action, connector, surface, and adapter identifiers
- `request_envelope` with method, endpoint label, idempotency key, headers by reference, and payload preview
- `credential_refs`
- `audit_packet`
- `rollback_packet`
- `dispatch_state: blocked_until_live_dispatch_enabled`
- `external_action_enabled: false`

## Blocking Rules

Blocked reasons:

- `blocked_dispatch_not_requested`
- `blocked_until_dispatch_review`
- `unsupported_surface`
- `execution_not_ready`
- `external_execution_blocked`
- `external_override_blocked`
- `missing_credential_ref`
- `high_risk_dispatch`

High-risk dispatch candidates such as Qianchuan budget operations, Xingtu commitments, public Douyin replies, WeChat contact sends, OpenAI model execution, and backup writes remain blocked unless a future live adapter explicitly implements a stronger approval policy.

## Approval Records

The workflow creates approval records for:

- `venus_live_connector_dispatch_rehearsal_review` when `live_dispatch_requested` is true.
- `venus_high_risk_dispatch_rehearsal_review` when high-risk dispatch candidates are blocked.

These records are review artifacts only.

## Safety And Isolation

- Config namespace must start with `venus_`.
- Config and storage names reject Xiaolongxia references.
- No secret values are read from environment variables or payload output.
- No external action is executed.
- No Feishu message, Airtable write, Douyin reply, Douyin publish, ad spend, Xingtu commitment, WeChat contact, OpenAI model call, backup write, memory write, or platform state change occurs.

## Integration

Add:

- `src/venus/connector_dispatch.py`
- `tests/test_connector_dispatch.py`
- `data/samples/connector_dispatch.json`
- CLI command: `venus connector-dispatch data/samples/connector_dispatch.json`
- Feishu dry-run command: `/venus connector-dispatch`
- Orchestrator route: `connector_dispatch`
- README, task plan, and progress updates.

## Acceptance Criteria

- Unit tests prove request-envelope generation, credential blocking, high-risk blocking, external override blocking, idempotency, approval records, redaction, and Xiaolongxia isolation.
- CLI smoke proves the command outputs `workflow: connector_dispatch`.
- Feishu route test proves `/venus connector-dispatch` returns a card-ready dry-run report.
- `pytest -q` passes.
- `git diff --check` passes.
- `data/venus` remains free of accidental runtime state after final verification except `.gitkeep`.
