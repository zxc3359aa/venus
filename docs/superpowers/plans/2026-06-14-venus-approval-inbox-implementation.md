# Venus Approval Inbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run approval inbox that centralizes Venus approval records and decision intents for safe Feishu/mobile review.

**Architecture:** Create `src/venus/approval_inbox.py` as a deterministic queue builder. Route it through the existing orchestrator, CLI, and Feishu entry adapter. Keep decisions recorded-only and preserve `external_actions: []`.

**Tech Stack:** Python standard library, pytest, local sample JSON.

---

## File Structure

- Create `src/venus/approval_inbox.py`: config validation, redaction, record normalization, surface/risk classification, priority sorting, decision-intent normalization, and report building.
- Create `tests/test_approval_inbox.py`: unit tests for the workflow.
- Create `data/samples/approvals.json`: deterministic local approval queue.
- Modify `src/venus/orchestrator.py`: route `approvals`.
- Modify `src/venus/cli.py`: add `approvals` command.
- Modify `src/venus/feishu_entry.py`: add `/venus approvals`, default sample path, workflow route, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the approval inbox.

## Task 1: Tests First

- [x] Create `tests/test_approval_inbox.py`.
- [x] Assert the report returns `workflow: approvals`, `namespace: venus_approvals`, `dry_run: true`, `approval_mode: manual`, and `external_actions: []`.
- [x] Assert summary counts:
  - approval count 6;
  - pending count 4;
  - approved count 1;
  - rejected count 1;
  - level-4 count 2;
  - public/spend/user-contact count 4;
  - decision intent count 2;
  - second-review count 1.
- [x] Assert priority queue starts with `venus_autopilot_enablement_review`, then `qianchuan_budget_review`.
- [x] Assert `surface_summary["ad_spend"]["pending_count"] == 1`.
- [x] Assert first decision intent has `execution_state: recorded_only` and `requires_second_review: true`.
- [x] Assert secret-like values and Xiaolongxia references are absent from the output.
- [x] Add CLI smoke test for `venus approvals data/samples/approvals.json`.
- [x] Add Feishu route test for `/venus approvals`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Workflow

- [x] Add `ApprovalInboxConfig` with `namespace="venus_approvals"`, `dry_run=True`, `approval_mode="manual"`, and Xiaolongxia isolation checks.
- [x] Add recursive redaction for secret-like keys.
- [x] Normalize approval records into stable items with `approval_id`, `surface`, `risk_band`, `is_public_or_spend_or_contact`, `status`, and `execution_state`.
- [x] Sort pending items by approval level descending, public/spend/contact risk, and created time.
- [x] Build `surface_summary` with total and pending counts per surface.
- [x] Normalize decision intents without mutating approval records.
- [x] Build `next_actions`, policy, and safety boundary.

## Task 3: Routing

- [x] Import and route `build_approval_inbox` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `approvals`.
- [x] Add Feishu command `/venus approvals`, default sample path, workflow mapping, and summary text.

## Task 4: Docs And Verification

- [x] Add `data/samples/approvals.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted tests for approval inbox, CLI, and Feishu route.
- [x] Run `pytest -v`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli approvals data/samples/approvals.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [ ] Commit with `feat: add approval inbox workflow`.
- [ ] Push to `codex/venus-feishu-entry`.
