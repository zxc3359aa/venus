# Venus Approval Archive Design

## Purpose

Venus already drafts approval decision ledger entries, but the entries are not persisted. The approval archive adds the first controlled local write path: approved, low-risk ledger entries can be appended to the isolated Venus JSON store so later automation can prove which decisions were reviewed, skipped, or rolled back.

This is a local persistence step only. It does not execute a Douyin reply, video publish, ad spend change, Xingtu acceptance, WeChat handoff, Feishu send, memory merge, backup upload, or any other platform action.

## Scope

The archive workflow accepts the same approval payload used by `approval_ledger`, plus explicit archive controls:

- `archive_requested`: must be true before any local write is attempted.
- `approved_ledger_write_review`: must be true before any local write is attempted.
- `workspace_root`: optional root for the isolated Venus `JsonStore`; if omitted by CLI, the current working directory is used.

The workflow calls `build_approval_ledger`, filters non-duplicate ledger entries, persists only entries with `record_state: ready_for_local_ledger_review`, and leaves `blocked_for_second_review` entries out of storage. Duplicates already present in local storage are skipped idempotently.

## Data Flow

1. Redact secret-like values through the existing ledger workflow.
2. Build ledger entries from pending approval records and requested decision intents.
3. Read `data/venus/approval_decision_ledger.json` through `JsonStore`.
4. Combine existing local entries with proposed ready entries.
5. Write the collection only if archive controls are approved.
6. Return a report with archived IDs, skipped IDs, rollback instructions, local storage path, and `external_actions: []`.

## Safety Rules

- The collection name is fixed to `approval_decision_ledger`.
- Config and storage paths must reject Xiaolongxia references.
- High-risk decisions requiring second review are never archived by this first archive workflow.
- The workflow does not mutate source approval records.
- The workflow does not call live Feishu, Douyin, WeChat, Qianchuan, Xingtu, Airtable, OpenAI, or other APIs.
- Feishu entry remains dry-run; `/venus approval-archive` can display the archive result from a sample payload but must not send a live card or platform action.

## Interfaces

- Core function: `build_approval_archive(payload, config=None)`.
- CLI command: `venus approval-archive <input.json>`.
- Orchestrator workflow: `approval_archive`.
- Feishu command: `/venus approval-archive`.
- Local store: `data/venus/approval_decision_ledger.json`.

## Acceptance Criteria

- A ready ledger entry is persisted to the Venus JSON store when archive controls are approved.
- A high-risk second-review entry is skipped and reported.
- Re-running the same archive is idempotent and does not duplicate stored decisions.
- Missing archive approval returns a blocked report and performs no local write.
- CLI and Feishu routes work with sample payloads.
- Full test suite, CLI smoke, and git whitespace checks pass before committing.
