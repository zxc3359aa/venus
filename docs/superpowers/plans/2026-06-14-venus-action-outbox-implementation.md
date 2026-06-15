# Venus Action Outbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local action outbox that queues approved low-risk Venus actions after approval decisions have been archived.

**Architecture:** Create `src/venus/action_outbox.py` as a local execution queue layer over `JsonStore`. Route it through the orchestrator, CLI, and Feishu dry-run adapter while keeping all platform delivery disabled and reporting blocked external actions.

**Tech Stack:** Python standard library, existing Venus `JsonStore`, pytest, deterministic JSON samples.

---

## File Structure

- Create `src/venus/action_outbox.py`: config, archived-decision loading, action matching, queue eligibility, idempotent local writes, rollback plan, and safety boundary.
- Create `tests/test_action_outbox.py`: core local queue, idempotency, blocking, and isolation tests.
- Create `data/samples/action_outbox.json`: safe sample with execution disabled by default.
- Modify `src/venus/orchestrator.py`: route `action_outbox`.
- Modify `src/venus/cli.py`: add `action-outbox` command.
- Modify `src/venus/feishu_entry.py`: add `/venus action-outbox`, default sample path, route mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke using a temporary workspace root.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the outbox.

## Task 1: Tests First

- [x] Create `tests/test_action_outbox.py`.
- [x] Assert an approved `feishu_mobile_report` decision writes one `action_outbox` item.
- [x] Assert `qianchuan_budget_review` is blocked as an external high-risk action.
- [x] Assert a rejected `airtable_sync_review` decision is skipped as `decision_not_approved`.
- [x] Assert repeat runs skip duplicates and do not append a second item.
- [x] Assert missing execution approval blocks writes and does not create the outbox file.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus action-outbox <tmp-input.json>`.
- [x] Add Feishu route test for `/venus action-outbox`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Outbox Workflow

- [x] Add `ActionOutboxConfig` with workspace root, namespace `venus_action_outbox`, collection `action_outbox`, approval mode `manual`, and isolation validation.
- [x] Load archived decisions from payload or `JsonStore("approval_decision_ledger")`.
- [x] Match decisions to action plan entries by `action_type`.
- [x] Queue only approved archived local actions with approval level `<= 2`.
- [x] Block high-risk or external actions with clear skip reasons.
- [x] Write non-duplicate outbox items into `JsonStore("action_outbox")`.
- [x] Return summary, queued items, blocked items, duplicate items, rollback plan, and `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_action_outbox` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `action-outbox`.
- [x] Add Feishu command `/venus action-outbox`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/action_outbox.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted outbox tests.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli action-outbox data/samples/action_outbox.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [x] Commit with `feat: add action outbox`.
- [x] Push to `codex/venus-feishu-entry`.
