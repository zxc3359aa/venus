# Venus Action Outbox Design

## Purpose

Venus now has approval records, approval decision ledger drafts, and a controlled local approval archive. The action outbox adds the next step in the automation chain: it turns archived approval decisions into auditable local execution queue records.

This workflow is deliberately local-first. It can write a Venus-only `action_outbox` collection, but it cannot send Feishu messages, write Airtable bases, reply on Douyin, publish videos, spend Qianchuan budget, accept Xingtu tasks, contact WeChat users, mutate memory, or call any live platform.

## Scope

The workflow accepts:

- `workspace_root`: optional root for isolated Venus JSON storage.
- `execution_requested`: must be true before any local queue write is attempted.
- `approved_execution_review`: must be true before any local queue write is attempted.
- `action_plan`: action objects from Agent Run or another Venus workflow.
- `archived_decisions`: optional already-approved decision entries; if absent, the workflow reads `approval_decision_ledger` from `JsonStore`.
- `existing_outbox_items`: optional extra duplicate-check records for dry-run samples.

Only archived `approve` decisions for low-risk local actions can be queued. Current queueable action types are:

- `feishu_mobile_report`: private Feishu card draft for the operator, stored locally only.
- `airtable_sync_review`: Airtable-ready package review, stored locally only.

Everything else is blocked or skipped with a reason. High-risk surfaces such as Douyin replies, WeChat handoff, Qianchuan budget, Xingtu brand commitments, publishing, ecommerce changes, and memory writes stay blocked even if an approval-like decision exists.

## Data Flow

1. Load archived decisions from payload or `data/venus/approval_decision_ledger.json`.
2. Normalize action plan items and match them by `action_type`.
3. Keep only `decision=approve` records with `archive_state=archived`.
4. Build deterministic outbox IDs from action type, matched approval ID, and decision ID.
5. Read `data/venus/action_outbox.json`.
6. Append non-duplicate queueable records when execution controls are approved.
7. Return queued, duplicate, blocked, and rejected entries with rollback instructions and `external_actions: []`.

## Safety Rules

- Config must use a `venus_` namespace and reject Xiaolongxia references.
- The local collection is fixed to `action_outbox`.
- Queueing is blocked unless `execution_requested` and `approved_execution_review` are both true.
- The workflow writes only the local Venus JSON store.
- Outbox records are `delivery_state: local_manual_dispatch_required`; no platform delivery is performed.
- Any action with `external_action_enabled: true` is blocked from local queueing.

## Interfaces

- Core function: `build_action_outbox(payload, config=None)`.
- CLI command: `venus action-outbox <input.json>`.
- Orchestrator workflow: `action_outbox`.
- Feishu command: `/venus action-outbox`.
- Local store: `data/venus/action_outbox.json`.

## Acceptance Criteria

- Approved low-risk local actions are written to the Venus action outbox.
- Re-running the workflow is idempotent and does not duplicate outbox items.
- Missing execution approval blocks local writes.
- Rejected decisions and high-risk external actions are skipped with explicit reasons.
- CLI and Feishu routes return safe reports with `external_actions: []`.
- Full test suite, CLI smoke commands, and git whitespace checks pass before committing.
