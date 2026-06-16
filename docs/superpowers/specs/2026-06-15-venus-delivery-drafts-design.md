# Venus Delivery Drafts Design

## Purpose

Venus can now queue approved low-risk actions in the local `action_outbox`. The delivery drafts workflow turns those queue items into concrete local handoff artifacts: Feishu card drafts for private operator review and Airtable record packages for operations sync review.

This is not live delivery. It creates local drafts only. It does not send Feishu messages, write Airtable records, reply on Douyin, publish videos, change ad budgets, accept Xingtu tasks, contact WeChat users, mutate memory, or call any live platform API.

## Scope

The workflow accepts:

- `workspace_root`: optional root for isolated Venus JSON storage.
- `delivery_requested`: must be true before local draft persistence is attempted.
- `approved_delivery_review`: must be true before local draft persistence is attempted.
- `outbox_items`: optional action outbox items; if absent, the workflow reads `action_outbox` from `JsonStore`.
- `existing_delivery_drafts`: optional dry-run duplicate-check records.

Supported local draft adapters:

- `feishu_mobile_report`: creates a `feishu_card_draft` artifact for manual private review.
- `airtable_sync_review`: creates an `airtable_record_package` artifact for manual Airtable import review.

Unsupported or high-risk actions are blocked with explicit reasons.

## Data Flow

1. Load outbox items from payload or `data/venus/action_outbox.json`.
2. Keep only items with `delivery_state: local_manual_dispatch_required`.
3. Generate deterministic draft IDs from outbox ID and action type.
4. Build platform-specific local draft payloads for supported adapters.
5. Read `data/venus/delivery_drafts.json`.
6. Append non-duplicate drafts only when delivery controls are approved.
7. Return drafted, duplicate, and blocked items with rollback instructions and `external_actions: []`.

## Safety Rules

- Config must use a `venus_` namespace and reject Xiaolongxia references.
- The local collection is fixed to `delivery_drafts`.
- Draft persistence is blocked unless `delivery_requested` and `approved_delivery_review` are both true.
- Drafts remain `dispatch_state: local_review_required`.
- Any item with `external_action_enabled: true` is blocked.
- No draft is treated as sent, delivered, synced, replied, published, routed, or spent.

## Interfaces

- Core function: `build_delivery_drafts(payload, config=None)`.
- CLI command: `venus delivery-drafts <input.json>`.
- Orchestrator workflow: `delivery_drafts`.
- Feishu command: `/venus delivery-drafts`.
- Local store: `data/venus/delivery_drafts.json`.

## Acceptance Criteria

- Feishu and Airtable outbox items generate local delivery drafts when delivery controls are approved.
- Unsupported or high-risk items are blocked.
- Re-running the workflow is idempotent and does not duplicate drafts.
- Missing delivery approval blocks local writes.
- CLI and Feishu routes return safe reports with `external_actions: []`.
- Full test suite, CLI smoke commands, and git whitespace checks pass before committing.
