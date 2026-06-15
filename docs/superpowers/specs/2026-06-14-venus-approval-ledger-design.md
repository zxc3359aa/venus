# Venus Approval Decision Ledger Design

## Goal

Add a local approval decision ledger workflow that turns recorded-only approval intents into an auditable, deduplicated, rollback-ready ledger draft. This gives Venus a safe bridge from "I saw the approval queue" to "I can remember which decisions were reviewed" without applying any decision to live platforms.

The ledger is intentionally dry-run in this slice. It produces entries, duplicate detection, write plans, and rollback plans, but it does not write to `data/venus`, mutate source approval records, send Feishu messages, or execute approvals.

## In Scope

- New `approval_ledger` workflow implemented by `src/venus/approval_ledger.py`.
- CLI command: `venus approval-ledger data/samples/approval_ledger.json`.
- Feishu command: `/venus approval-ledger`.
- Local sample input in `data/samples/approval_ledger.json`.
- Reuse of approval inbox normalization for records and decision intents.
- Deterministic decision IDs and deduplication against existing ledger entries.
- Second-review blocking for high-risk approve decisions.
- Dry-run write plan and rollback plan.
- Approval records for local ledger write review and high-risk second review.

## Out Of Scope

- Writing ledger entries to disk.
- Applying approvals to source records.
- Executing Feishu, Douyin, WeChat, Qianchuan, Xingtu, Airtable, memory, backup, or publishing actions.
- Authenticating approvers.
- Replacing the approval inbox.

## Input Contract

The payload is a dictionary:

- `source`: local/manual ledger source.
- `recorded_at`: ledger draft timestamp.
- `write_requested`: boolean intent to write a local ledger in the future.
- `approval_records`: approval records accepted by the approval inbox workflow.
- `requested_decisions`: decision intents accepted by the approval inbox workflow.
- `existing_ledger_entries`: optional existing entries for duplicate detection.

Secret-like keys are redacted recursively.

## Output Contract

The workflow returns:

- `workflow: approval_ledger`.
- `namespace: venus_approval_ledger`.
- `dry_run: true`.
- `approval_mode: manual`.
- `summary`.
- `ledger_entries`.
- `duplicate_intents`.
- `write_plan`.
- `rollback_plan`.
- `approval_records`.
- `external_actions: []`.
- `safety_boundary`.

## Ledger Entry Rules

Each non-duplicate matched decision intent becomes a proposed ledger entry:

- `decision_id`: deterministic from action type, decision, reviewer, and matched approval ID.
- `action_type`.
- `decision`.
- `reviewer`.
- `reason`.
- `surface`.
- `approval_level`.
- `matched_approval_id`.
- `requires_second_review`.
- `record_state`:
  - `blocked_for_second_review` for approve intents that require second review.
  - `ready_for_local_ledger_review` for non-duplicate intents that can be recorded after local review.
- `external_action_enabled: false`.

Duplicate detection uses `decision_id` first. Existing ledger entries can also match on action type, decision, reviewer, and matched approval ID.

## Write Plan

The write plan always remains blocked:

- `target_collection: approval_decision_ledger`.
- `record_count`: count of proposed new ledger entries.
- `existing_entry_count`.
- `write_requested`.
- `execution_state: blocked_until_approved`.
- `external_action_enabled: false`.

## Rollback Plan

The rollback plan lists the proposed decision IDs that would be removed if a local ledger write were later approved and then rolled back. In this slice it is documentation only.

## Approval Records

- `venus_approval_ledger_write_review`: created when `write_requested` is true and new entries exist.
- `venus_high_risk_decision_second_review`: created when any proposed entry is blocked for second review.

## Safety

The workflow must never:

- write to local storage;
- update source approvals;
- send Feishu messages;
- reply to Douyin;
- publish content;
- change ad spend;
- accept brand work;
- contact WeChat users;
- write memory or backup state.

## Acceptance Criteria

- Unit tests prove deterministic ledger entries, duplicate detection, second-review blocking, write plan, rollback plan, approval records, redaction, and Xiaolongxia isolation.
- CLI smoke test proves `venus approval-ledger data/samples/approval_ledger.json` returns JSON.
- Feishu test proves `/venus approval-ledger` routes to the local ledger draft.
- Full test suite passes.
