# Venus Delivery Drafts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local delivery draft adapters that turn approved action outbox items into reviewable Feishu and Airtable handoff artifacts without sending anything.

**Architecture:** Create `src/venus/delivery_drafts.py` as a local draft layer over `JsonStore`. Route it through the orchestrator, CLI, and Feishu dry-run adapter while preserving `external_actions: []` and blocking unsupported or high-risk dispatch.

**Tech Stack:** Python standard library, existing Venus `JsonStore`, pytest, deterministic JSON samples.

---

## File Structure

- Create `src/venus/delivery_drafts.py`: config, outbox loading, adapter selection, draft generation, idempotent local writes, rollback plan, and safety boundary.
- Create `tests/test_delivery_drafts.py`: core draft generation, idempotency, blocking, and isolation tests.
- Create `data/samples/delivery_drafts.json`: safe sample with delivery disabled by default.
- Modify `src/venus/orchestrator.py`: route `delivery_drafts`.
- Modify `src/venus/cli.py`: add `delivery-drafts` command.
- Modify `src/venus/feishu_entry.py`: add `/venus delivery-drafts`, default sample path, route mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke using a temporary workspace root.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document delivery drafts.

## Task 1: Tests First

- [x] Create `tests/test_delivery_drafts.py`.
- [x] Assert `feishu_mobile_report` creates a `feishu_card_draft`.
- [x] Assert `airtable_sync_review` creates an `airtable_record_package`.
- [x] Assert `qianchuan_budget_review` is blocked as unsupported/high-risk.
- [x] Assert repeat runs skip duplicate draft records.
- [x] Assert missing delivery approval blocks writes and does not create the drafts file.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus delivery-drafts <tmp-input.json>`.
- [x] Add Feishu route test for `/venus delivery-drafts`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Draft Workflow

- [x] Add `DeliveryDraftConfig` with workspace root, namespace `venus_delivery_drafts`, collection `delivery_drafts`, approval mode `manual`, and isolation validation.
- [x] Load outbox items from payload or `JsonStore("action_outbox")`.
- [x] Block local writes unless `delivery_requested` and `approved_delivery_review` are true.
- [x] Generate draft records only for `feishu_mobile_report` and `airtable_sync_review`.
- [x] Block unsupported, high-risk, or externally-enabled outbox items.
- [x] Write non-duplicate drafts into `JsonStore("delivery_drafts")`.
- [x] Return summary, draft records, blocked records, duplicate records, rollback plan, and `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_delivery_drafts` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `delivery-drafts`.
- [x] Add Feishu command `/venus delivery-drafts`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/delivery_drafts.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted delivery draft tests.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli delivery-drafts data/samples/delivery_drafts.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [x] Commit with `feat: add delivery drafts`.
- [x] Push to `codex/venus-feishu-entry`.
