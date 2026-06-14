# Venus Approval Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a controlled local approval archive that persists approved, low-risk approval ledger entries into Venus isolated JSON storage.

**Architecture:** Create `src/venus/approval_archive.py` as a thin persistence layer over `build_approval_ledger` and `JsonStore`. Route it through the orchestrator, CLI, and Feishu dry-run adapter while preserving `external_actions: []` and blocking unapproved or high-risk decisions.

**Tech Stack:** Python standard library, existing Venus `JsonStore`, pytest, local JSON samples.

---

## File Structure

- Create `src/venus/approval_archive.py`: config, archive controls, ledger reuse, local-store idempotency, write report, rollback plan, safety boundary.
- Create `tests/test_approval_archive.py`: core persistence and blocking tests.
- Create `data/samples/approval_archive.json`: deterministic sample with archive disabled for safe Feishu preview.
- Modify `src/venus/orchestrator.py`: route `approval_archive`.
- Modify `src/venus/cli.py`: add `approval-archive` command and workspace root defaulting.
- Modify `src/venus/feishu_entry.py`: add `/venus approval-archive`, default sample path, workflow mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke using a temporary workspace root.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the archive.

## Task 1: Tests First

- [x] Create `tests/test_approval_archive.py`.
- [x] Assert approved ready entries are written to `data/venus/approval_decision_ledger.json`.
- [x] Assert high-risk second-review entries are skipped.
- [x] Assert duplicate local entries are skipped on repeat runs.
- [x] Assert missing archive approval blocks the write and does not create the collection file.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus approval-archive <tmp-input.json>`.
- [x] Add Feishu route test for `/venus approval-archive`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Archive Workflow

- [x] Add `ApprovalArchiveConfig` with workspace root, namespace `venus_approval_archive`, collection `approval_decision_ledger`, approval mode `manual`, reviewer `owner`, and isolation validation.
- [x] Build the ledger via `build_approval_ledger`.
- [x] Block local writes unless `archive_requested` and `approved_ledger_write_review` are true.
- [x] Read existing local archive records with `JsonStore`.
- [x] Persist only `ready_for_local_ledger_review` entries that are not already archived.
- [x] Return archive summary, skipped entries, rollback plan, storage path, safety boundary, and `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_approval_archive` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `approval-archive`.
- [x] Add Feishu command `/venus approval-archive`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/approval_archive.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted archive tests.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli approval-archive <tmp-input.json>`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [ ] Commit with `feat: add approval archive`.
- [ ] Push to `codex/venus-feishu-entry`.
