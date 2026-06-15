# Venus Airtable Sync Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local Airtable sync planning workflow that validates Airtable-ready packages and records approved local sync plans without touching live Airtable.

**Architecture:** Create `src/venus/airtable_sync.py` as a focused local planning layer over `JsonStore`. It consumes an Airtable package and connector readiness metadata, validates table schemas, persists idempotent sync plan records, and routes through orchestrator, CLI, and Feishu dry-run.

**Tech Stack:** Python standard library, existing Venus `JsonStore`, existing `build_airtable_sync_package`, pytest, deterministic JSON samples.

---

## File Structure

- Create `src/venus/airtable_sync.py`: config, package loading, connector readiness validation, table schema validation, sync plan generation, idempotent local writes, rollback plan, and safety boundary.
- Create `tests/test_airtable_sync.py`: core planning, blocking, idempotency, approval gate, and isolation tests.
- Create `data/samples/airtable_sync_plan.json`: safe sample with sync writes disabled by default.
- Modify `src/venus/orchestrator.py`: route `airtable_sync_plan`.
- Modify `src/venus/cli.py`: add `airtable-sync` command.
- Modify `src/venus/feishu_entry.py`: add `/venus airtable-sync`, default sample path, route mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke using a temporary workspace root.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the Airtable sync planning layer.

## Task 1: Tests First

- [x] Create `tests/test_airtable_sync.py`.
- [x] Assert valid package, approval, and connector readiness create local sync plan records.
- [x] Assert missing connector readiness blocks writes.
- [x] Assert schema mismatch blocks the affected table.
- [x] Assert externally-enabled events are blocked.
- [x] Assert repeat runs skip duplicate sync plan records.
- [x] Assert missing sync approval blocks writes and does not create the sync plan file.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus airtable-sync <tmp-input.json>`.
- [x] Add Feishu route test for `/venus airtable-sync`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Sync Plan Workflow

- [x] Add `AirtableSyncPlanConfig` with workspace root, namespace `venus_airtable_sync`, collection `airtable_sync_plans`, approval mode `manual`, and isolation validation.
- [x] Load `airtable_package` from payload or build it with `build_airtable_sync_package(payload)`.
- [x] Block local writes unless `sync_requested` and `approved_sync_review` are true.
- [x] Require an Airtable connector that is ready, has `base_read` and `record_write`, has audit and rollback readiness, and has external actions disabled.
- [x] Validate package namespace starts with `venus_` and each record field exists in the table's field definitions.
- [x] Write non-duplicate sync plan records into `JsonStore("airtable_sync_plans")`.
- [x] Return summary, sync plan records, blocked tables, duplicate records, rollback plan, and `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_airtable_sync_plan` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `airtable-sync`.
- [x] Add Feishu command `/venus airtable-sync`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/airtable_sync_plan.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted Airtable sync tests.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli airtable-sync data/samples/airtable_sync_plan.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [x] Commit with `feat: add airtable sync plan`.
- [x] Push to `codex/venus-feishu-entry`.
