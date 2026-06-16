# Venus Delivery Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local delivery status ledger that records approved manual delivery outcomes for Venus delivery drafts without touching external platforms.

**Architecture:** Create `src/venus/delivery_status.py` as a focused local ledger layer over `JsonStore`. Route it through the orchestrator, CLI, and Feishu dry-run adapter, matching the existing action outbox and delivery draft patterns.

**Tech Stack:** Python standard library, existing Venus `JsonStore`, pytest, deterministic JSON samples.

---

## File Structure

- Create `src/venus/delivery_status.py`: config, draft loading, event matching, status ledger generation, idempotent local writes, rollback plan, and safety boundary.
- Create `tests/test_delivery_status.py`: status recording, blocking, idempotency, approval gate, and isolation tests.
- Create `data/samples/delivery_status.json`: safe sample with status writes disabled by default.
- Modify `src/venus/orchestrator.py`: route `delivery_status`.
- Modify `src/venus/cli.py`: add `delivery-status` command.
- Modify `src/venus/feishu_entry.py`: add `/venus delivery-status`, default sample path, route mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke using a temporary workspace root.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the delivery status ledger.

## Task 1: Tests First

- [x] Create `tests/test_delivery_status.py`.
- [x] Assert completed and returned manual statuses create `delivery_status` ledger records.
- [x] Assert missing draft, unsupported status, and external event are blocked.
- [x] Assert repeat runs skip duplicate status records.
- [x] Assert missing status approval blocks writes and does not create the status file.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus delivery-status <tmp-input.json>`.
- [x] Add Feishu route test for `/venus delivery-status`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Status Workflow

- [x] Add `DeliveryStatusConfig` with workspace root, namespace `venus_delivery_status`, collection `delivery_status`, approval mode `manual`, and isolation validation.
- [x] Load delivery drafts from payload or `JsonStore("delivery_drafts")`.
- [x] Block local writes unless `status_update_requested` and `approved_status_review` are true.
- [x] Generate status ledger records only for `manual_dispatch_completed`, `returned_for_revision`, and `blocked_after_review`.
- [x] Block missing draft references, unsupported statuses, externally-enabled events, or drafts that are not local review drafts.
- [x] Write non-duplicate status records into `JsonStore("delivery_status")`.
- [x] Return summary, status records, blocked records, duplicate records, rollback plan, and `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_delivery_status` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `delivery-status`.
- [x] Add Feishu command `/venus delivery-status`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/delivery_status.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted delivery status tests.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli delivery-status data/samples/delivery_status.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [x] Commit with `feat: add delivery status ledger`.
- [x] Push to `codex/venus-feishu-entry`.
