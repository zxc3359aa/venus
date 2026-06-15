# Venus Connector Execution Gateway Design

## Purpose

Venus already produces local approval records, action outbox items, delivery drafts, connector audits, and delivery status records. This slice adds the next bridge toward real platform integrations: a connector execution gateway that converts approved delivery drafts plus connector readiness metadata into local execution manifests.

The gateway does not send Feishu messages, write Airtable records, reply on Douyin, touch WeChat, spend Qianchuan budget, accept Xingtu tasks, call OpenAI, or mutate any external platform. It prepares auditable manifests that make the eventual live-execution boundary explicit.

## Scope

The workflow is named `connector_execution`.

It supports these target surfaces as manifest candidates:

- `feishu`: Feishu private report/card send candidate.
- `airtable`: Airtable record write candidate.
- `douyin`: Douyin comment, live-message, or metric action candidate.
- `wechat`: WeChat Mini Program or Enterprise WeChat handoff candidate.
- `qianchuan`: OceanEngine/Qianchuan campaign or budget candidate.
- `xingtu`: Xingtu brand-task candidate.
- `openai`: OpenAI Agents SDK or model-run candidate.
- `backup`: local or external backup candidate.

Every candidate is still a local manifest with `external_action_enabled: false`.

## Inputs

The workflow accepts a JSON payload:

- `workspace_root`: optional local workspace root. Defaults to `.`.
- `source`: source label for the manifest run.
- `executed_at`: deterministic timestamp for local records.
- `execution_requested`: must be true before any local execution manifest is written.
- `approved_execution_review`: must be true before any local execution manifest is written.
- `live_dispatch_requested`: when true, creates an approval record for future live connector dispatch review.
- `draft_records`: optional delivery draft records. If omitted, the workflow reads `data/venus/delivery_drafts.json`.
- `connector_reviews`: connector readiness records, usually copied from the `connectors` workflow.
- `execution_overrides`: optional requested per-draft overrides. Any override that tries to enable external actions is blocked.

Secrets and token-like values are redacted recursively before analysis.

## Output

The workflow returns:

- `workflow: connector_execution`
- `namespace: venus_connector_execution`
- `execution_state`
- `summary`
- `execution_records`
- `blocked_items`
- `duplicate_items`
- `approval_records`
- `surface_readiness`
- `write_plan`
- `rollback_plan`
- `external_actions: []`
- `safety_boundary`

When permitted by local gates, records are written only to `data/venus/connector_execution_manifests.json`.

## Manifest Rules

A delivery draft becomes an execution record only when all of these are true:

- `execution_requested` is true.
- `approved_execution_review` is true.
- The draft has `dispatch_state: local_review_required`.
- The draft has `external_action_enabled: false`.
- The draft target surface is supported.
- A connector review exists for that surface.
- The connector review has `ready_for_launch: true`.
- The connector review does not list missing permissions.
- The connector review has audit and rollback readiness.
- The effective approval level is below level 4.
- No override attempts to enable external action.

The execution record includes:

- stable `execution_id`
- draft, outbox, action, artifact, surface, and connector identifiers
- `adapter_type`
- `required_secret_refs`
- `permission_snapshot`
- `audit_log_ref`
- `rollback_ref`
- `execution_state: local_manifest_ready`
- `dispatch_state: blocked_until_live_connector_enabled`
- `external_action_enabled: false`

## Blocking Rules

Blocked items include a stable draft reference and a `skip_reason`.

Reasons:

- `blocked_execution_not_requested`
- `blocked_until_execution_review`
- `unsupported_surface`
- `missing_connector_review`
- `connector_not_ready`
- `missing_connector_permission`
- `missing_audit_or_rollback`
- `draft_not_local_review`
- `external_draft_blocked`
- `external_override_blocked`
- `high_risk_live_action`

Level-4 surfaces such as Qianchuan budget changes and Xingtu brand commitments remain blocked even if connector metadata says ready. They create approval records instead of execution records.

## Approval Records

The workflow creates approval records for:

- `venus_live_connector_dispatch_review` when `live_dispatch_requested` is true.
- `venus_high_risk_connector_execution_review` when high-risk drafts are present.

Both are review artifacts only; no source record is mutated.

## Safety And Isolation

- Config namespaces must start with `venus_`.
- Config and storage collection names must reject Xiaolongxia references.
- Output must not leak secret-like payload values.
- No external action is executed.
- No Feishu message, Airtable write, Douyin reply, Douyin publish, ad spend, Xingtu commitment, WeChat contact, OpenAI model call, memory write, backup upload, or external platform state change occurs.

## Integration

Add:

- `src/venus/connector_execution.py`
- `tests/test_connector_execution.py`
- `data/samples/connector_execution.json`
- CLI command: `venus connector-execution data/samples/connector_execution.json`
- Feishu dry-run command: `/venus connector-execution`
- Orchestrator route: `connector_execution`
- README, task plan, and progress updates.

## Acceptance Criteria

- Unit tests prove manifest creation, blocking, idempotency, approval records, redaction, and Xiaolongxia isolation.
- CLI smoke proves the command outputs `workflow: connector_execution`.
- Feishu route test proves `/venus connector-execution` returns a card-ready dry-run report.
- `pytest -q` passes.
- `git diff --check` passes.
- `data/venus` remains free of accidental runtime state after final verification except `.gitkeep`.
