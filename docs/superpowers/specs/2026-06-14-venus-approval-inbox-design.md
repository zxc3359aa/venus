# Venus Approval Inbox Design

## Goal

Add a local approval inbox workflow that centralizes pending Venus approval records across content, Douyin, WeChat, Qianchuan, Xingtu, memory, connector, eval, and Feishu surfaces. The inbox lets the operator see what needs review first, why it is risky, and which decisions have been requested, without executing any approval, platform action, or memory write.

This is the mobile control layer Venus needs before becoming more autonomous: generated actions remain blocked, but the owner gets one clear queue to review on Feishu.

## In Scope

- New `approvals` workflow implemented by `src/venus/approval_inbox.py`.
- CLI command: `venus approvals data/samples/approvals.json`.
- Feishu command: `/venus approvals`.
- Local sample input in `data/samples/approvals.json`.
- Risk and surface classification for approval records.
- Pending priority queue sorted by approval level, surface risk, and created time.
- Decision-intent queue from owner-provided local decisions.
- Summary counts for pending, approved, rejected, level-4, public/spend/user-contact, and decision intents.
- Explicit safety boundary with `external_actions: []`.

## Out Of Scope

- Executing approvals.
- Writing back to memory, Airtable, Feishu, Douyin, WeChat, Qianchuan, Xingtu, or any other platform.
- Changing the status of source approval records.
- Authenticating users or verifying live Feishu signatures.

## Input Contract

The payload is a dictionary:

- `source`: local/manual approval source.
- `reviewed_at`: inbox generation timestamp.
- `approval_records`: list of approval records with:
  - `action_type`
  - `approval_level`
  - `draft`
  - `evidence_ids`
  - `status`
  - `reviewer`
  - `created_at`
- `requested_decisions`: optional list of decision intents:
  - `action_type`
  - `decision`: `approve`, `reject`, or `needs_changes`
  - `reason`
  - `reviewer`

Secret-like keys are redacted recursively.

## Output Contract

The workflow returns:

- `workflow: approvals`.
- `namespace: venus_approvals`.
- `dry_run: true`.
- `approval_mode: manual`.
- `summary`.
- `approval_items`.
- `priority_queue`.
- `surface_summary`.
- `decision_intents`.
- `next_actions`.
- `policy`.
- `external_actions: []`.
- `safety_boundary`.

## Classification Rules

Approval records are classified by action type:

- `autopilot`: `autopilot`, `eval`.
- `ad_spend`: `qianchuan`, `budget`, `campaign`.
- `brand_commercial`: `xingtu`, `brand`, `brief`.
- `public_reply`: `douyin`, `reply`, `comment`.
- `publishing`: `publish`, `production`, `content`.
- `private_domain`: `wechat`, `handoff`, `enterprise`.
- `memory`: `memory`, `learning`.
- `connector`: `connector`, `live_connector`.
- `feishu`: `feishu`.
- `operations`: fallback.

Risk bands:

- `critical`: approval level 4.
- `high`: approval level 3.
- `medium`: approval level 2.
- `low`: approval level 0-1.

Public/spend/user-contact actions are any records whose surface is `ad_spend`, `brand_commercial`, `public_reply`, `publishing`, or `private_domain`.

## Decision Intents

Decision intents are normalized but never applied. Each intent returns:

- `execution_state: recorded_only`.
- `external_action_enabled: false`.
- `requires_second_review: true` for level-4 or public/spend/user-contact actions.
- A matched approval item when possible.

If an intent has no matching approval record, it is retained with `match_status: missing_approval_record`.

## Safety

The workflow must never:

- approve or reject a live platform action;
- send Feishu messages;
- publish content;
- reply to comments;
- change ad spend;
- accept Xingtu work;
- contact WeChat users;
- write memory;
- mutate source approval records.

It only creates a readable queue and decision-intent draft for manual review.

## Acceptance Criteria

- Unit tests prove summary counts, sorting, surface/risk classification, decision intent handling, redaction, and Xiaolongxia isolation.
- CLI smoke test proves `venus approvals data/samples/approvals.json` returns JSON.
- Feishu test proves `/venus approvals` routes to the local approval inbox.
- Full test suite passes.
