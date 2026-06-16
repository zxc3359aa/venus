# Venus Airtable Sync Plan Design

## Purpose

Venus can already create an Airtable-ready operations package, but the project still needs a controlled bridge between local package generation and any future live Airtable write. This slice adds a local `airtable_sync_plan` workflow.

The workflow validates the Airtable package, connector readiness, approval gates, and rollback information, then records a local sync plan that a future live adapter can execute only after separate approval. It does not create bases, tables, records, views, automations, or interfaces in Airtable.

## Scope

- Add a local `airtable_sync_plan` workflow over `data/venus/airtable_sync_plans.json`.
- Accept Airtable packages from the payload or build one from existing local Airtable export inputs.
- Accept connector reviews from the payload.
- Require `sync_requested` and `approved_sync_review` before local plan persistence.
- Require a ready Airtable connector with `base_read`, `record_write`, audit log readiness, and rollback readiness.
- Validate each table has a name, field definitions, records, and record fields that match declared table fields.
- Create deterministic sync plan records by table, including planned operation, record count, field count, rollback strategy, and blocked external action flag.
- Preserve idempotency with duplicate detection.

Out of scope:

- Calling Airtable APIs.
- Reading Airtable schema from a live base.
- Creating, updating, or deleting any Airtable object.
- Storing Airtable tokens or base secrets.
- Triggering Feishu, Douyin, WeChat, Qianchuan, Xingtu, ecommerce, memory, or backup actions.

## Data Model

`AirtableSyncPlanConfig`:

- `workspace_root`
- `namespace`: `venus_airtable_sync`
- `collection`: `airtable_sync_plans`
- `approval_mode`: `manual`
- `reviewer`: `owner`
- `external_dry_run`: `True`

Input package:

- `base`
- `tables`
- `summary`
- `sync_boundary`

Connector review:

- `surface`: `airtable`
- `status`: `ready`
- `permissions_granted`: includes `base_read` and `record_write`
- `audit_ready` or `audit_log`: ready
- `rollback_ready` or `rollback`: configured
- `external_action_enabled`: false

Output records:

- `sync_plan_id`
- `base_name`
- `base_namespace`
- `connector_id`
- `table_name`
- `planned_operation`
- `record_count`
- `field_count`
- `record_preview_names`
- `rollback_strategy`
- `execution_state`: `local_sync_plan_ready`
- `external_action_enabled`: false

## Safety Boundary

The workflow writes only `data/venus/airtable_sync_plans.json`. It is a readiness and planning ledger, not a live Airtable write adapter.

The workflow rejects Xiaolongxia config references, redacts secret-like payload keys, and returns `external_actions: []`.

## Feishu Behavior

`/venus airtable-sync` returns a dry-run card summary with planned table count, blocked table count, and write-plan state. It reads `data/samples/airtable_sync_plan.json` by default and never sends a Feishu message.

## Testing

Tests cover:

- Creating local sync plans for valid tables when request, approval, and connector readiness are present.
- Blocking missing connector readiness, schema mismatches, unsupported namespaces, and external events.
- Idempotency on repeat runs.
- Blocking writes until sync approval is granted.
- Xiaolongxia isolation.
- CLI and Feishu routing.
