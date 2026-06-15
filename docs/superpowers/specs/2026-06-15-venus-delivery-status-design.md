# Venus Delivery Status Design

## Purpose

Venus already has a local approval chain that can move from approval decisions to action outbox items and then to local delivery drafts. The next gap is status evidence after a draft is reviewed by the operator: whether it was manually dispatched, returned for revision, or blocked after review.

This slice adds a local `delivery_status` workflow. It records reviewable status events for delivery drafts in the isolated Venus JSON store while keeping all platform actions disabled.

## Scope

- Add a local status ledger over `data/venus/delivery_status.json`.
- Accept delivery drafts from the payload or from `JsonStore("delivery_drafts")`.
- Accept status events from the payload.
- Persist only approved, local, manual status events.
- Keep duplicate status events idempotent.
- Block missing draft references, unsupported statuses, externally-enabled events, and unapproved status writes.
- Route the workflow through the orchestrator, CLI, and dry-run Feishu command.

Out of scope:

- Sending Feishu messages.
- Writing Airtable records.
- Updating Douyin, WeChat, Qianchuan, Xingtu, ecommerce, or backup systems.
- Mutating existing outbox or delivery draft records.

## Data Model

`DeliveryStatusConfig` mirrors the existing local write gates:

- `workspace_root`
- `namespace`: `venus_delivery_status`
- `collection`: `delivery_status`
- `approval_mode`: `manual`
- `reviewer`: `owner`
- `external_dry_run`: `True`

Status events use these fields:

- `draft_id`
- `outbox_id`
- `delivery_status`: one of `manual_dispatch_completed`, `returned_for_revision`, `blocked_after_review`
- `reviewer`
- `event_time`
- `notes`
- `evidence_ids`
- `external_action_enabled`

Stored status ledger records include the matched draft metadata, deterministic `status_id`, `follow_up_state`, `audit_state`, and `external_action_enabled: False`.

## Safety Boundary

The workflow writes only `data/venus/delivery_status.json`. It does not confirm that a platform state changed; it only records the operator's manual review status. Any live delivery adapter must later read this ledger and require separate connector permissions, audit logs, and approvals.

The workflow refuses Xiaolongxia references in config values, preserves `external_actions: []`, and redacts secret-like keys in payload-derived output.

## Feishu Behavior

`/venus delivery-status` returns a card-ready dry-run report summary. It reads `data/samples/delivery_status.json` by default and does not send a Feishu message.

## Testing

Tests cover:

- Recording completed and returned local statuses for known drafts.
- Blocking missing drafts, unsupported statuses, and externally-enabled events.
- Idempotency on repeat runs.
- Blocking writes until status update review is approved.
- Xiaolongxia isolation.
- CLI and Feishu routing.
