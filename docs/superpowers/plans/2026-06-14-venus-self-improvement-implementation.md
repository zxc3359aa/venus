# Venus Self-Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run self-improvement workflow for learning candidates, defect guardrails, and backup verification tasks.

**Architecture:** Create `src/venus/self_improvement.py` as a safe local contract that turns feedback, defects, and backup checks into approval-gated tasks. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner without changing memory, code, backups, or external services.

**Tech Stack:** Python standard library, existing Venus approval and backup helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/self_improvement.py`.
- Create `tests/test_self_improvement.py`.
- Create `data/samples/self_improvement.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `data/samples/agent_run.json`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Self-Improvement Tests

- [x] Add `tests/test_self_improvement.py`.
- [x] Verify the first run fails because `venus.self_improvement` does not exist.
- [x] Assert the connector returns `workflow: improvement`, Venus namespace, dry-run status, source metadata, summary metrics, learning candidates, regression checks, backup tasks, approval records, and `external_actions: []`.
- [x] Assert secret-like values do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Self-Improvement Implementation

- [x] Create `src/venus/self_improvement.py`.
- [x] Build learning candidates from user edits, approved wording, reasons, and metrics.
- [x] Build regression checks from defect reports and expected guardrails.
- [x] Build backup verification tasks from stale or unverified backup checks.
- [x] Add approval records for learning candidates, regression guardrails, and backup verification.
- [x] Enforce dry-run mode and Venus namespace validation.
- [x] Run targeted connector tests and confirm they pass.

### Task 3: Routes And Samples

- [x] Add CLI workflow `improvement`.
- [x] Add Feishu dry-run command `/venus improvement`.
- [x] Add `data/samples/self_improvement.json`.
- [x] Add self-improvement summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [ ] Run `pytest -v`.
- [ ] Run `python3 -m venus.cli improvement data/samples/self_improvement.json`.
- [ ] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [ ] Run `git diff --check`.
- [ ] Commit and push the changes.
