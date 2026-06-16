# Venus Approval Decision Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dry-run approval decision ledger that converts approval decision intents into auditable, deduplicated, rollback-ready local ledger entries.

**Architecture:** Create `src/venus/approval_ledger.py` and reuse `build_approval_inbox` for normalization. Route the workflow through the existing orchestrator, CLI, and Feishu dry-run adapter. Keep writes blocked behind approval records and preserve `external_actions: []`.

**Tech Stack:** Python standard library, existing approval helper, pytest, local sample JSON.

---

## File Structure

- Create `src/venus/approval_ledger.py`: config, redaction, inbox reuse, decision ID generation, duplicate detection, ledger entries, write plan, rollback plan, and approval records.
- Create `tests/test_approval_ledger.py`: unit tests for ledger drafting.
- Create `data/samples/approval_ledger.json`: deterministic local ledger sample.
- Modify `src/venus/orchestrator.py`: route `approval_ledger`.
- Modify `src/venus/cli.py`: add `approval-ledger` command and map it to `approval_ledger`.
- Modify `src/venus/feishu_entry.py`: add `/venus approval-ledger`, default sample path, workflow mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the ledger.

## Task 1: Tests First

- [x] Create `tests/test_approval_ledger.py`.
- [x] Assert workflow metadata and `external_actions: []`.
- [x] Assert summary:
  - decision intent count 3;
  - new entry count 2;
  - duplicate intent count 1;
  - second-review count 1;
  - ready-to-record count 1;
  - blocked intent count 1;
  - approval record count 2.
- [x] Assert first ledger entry is `qianchuan_budget_review` with `record_state: blocked_for_second_review`.
- [x] Assert second ledger entry is `douyin_comment_reply_queue` with `record_state: ready_for_local_ledger_review`.
- [x] Assert duplicate intent is `feishu_mobile_report`.
- [x] Assert write plan target is `approval_decision_ledger` and remains `blocked_until_approved`.
- [x] Assert rollback plan lists the two new decision IDs.
- [x] Assert secret-like values and Xiaolongxia references are absent from output.
- [x] Add CLI smoke test for `venus approval-ledger data/samples/approval_ledger.json`.
- [x] Add Feishu route test for `/venus approval-ledger`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Workflow

- [x] Add `ApprovalLedgerConfig` with `namespace="venus_approval_ledger"`, `dry_run=True`, `approval_mode="manual"`, `reviewer="owner"`, and Xiaolongxia isolation checks.
- [x] Add recursive redaction.
- [x] Call `build_approval_inbox` with the redacted payload.
- [x] Generate deterministic decision IDs from action type, decision, reviewer, and matched approval ID.
- [x] Detect duplicates against `existing_ledger_entries`.
- [x] Build proposed ledger entries for non-duplicate matched intents.
- [x] Mark high-risk approve intents as `blocked_for_second_review`.
- [x] Build write plan, rollback plan, approval records, and safety boundary.

## Task 3: Routing

- [x] Import and route `build_approval_ledger` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `approval-ledger`.
- [x] Add Feishu command `/venus approval-ledger`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/approval_ledger.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted tests for approval ledger, CLI, and Feishu route.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli approval-ledger data/samples/approval_ledger.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [x] Commit with `feat: add approval decision ledger`.
- [x] Push to `codex/venus-feishu-entry`.
