# Venus Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run scheduler workflow that creates a 24-hour Venus run queue without executing jobs or touching external platforms.

**Architecture:** Create `src/venus/scheduler.py` as a focused contract that normalizes job definitions, computes due local jobs, separates blocked jobs, builds private operator digest text, and emits approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner.

**Tech Stack:** Python standard library, existing Venus approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/scheduler.py`.
- Create `tests/test_scheduler.py`.
- Create `data/samples/scheduler.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Scheduler Tests

- [x] Add `tests/test_scheduler.py`.
- [x] Verify the first run fails because `venus.scheduler` does not exist.
- [x] Assert the scheduler returns `workflow: scheduler`, Venus namespace, dry-run status, run queue, blocked jobs, next runs, operator digest, approval records, and `external_actions: []`.
- [x] Assert due jobs are selected from cadence and timestamps.
- [x] Assert connector/permission blocked jobs are excluded from the run queue.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Scheduler Implementation

- [x] Create `src/venus/scheduler.py`.
- [x] Normalize generated time, timezone, jobs, blackout windows, and operator channels.
- [x] Compute each job's next run from `last_run_at` plus `cadence_minutes`.
- [x] Build `run_queue`, `blocked_jobs`, and `next_runs`.
- [x] Mark approval-gated due jobs as `blocked_until_approved`.
- [x] Build operator digest and approval records.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `scheduler`.
- [x] Add Feishu dry-run command `/venus scheduler`.
- [x] Add `data/samples/scheduler.json`.
- [x] Add scheduler summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted scheduler integration tests.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli scheduler data/samples/scheduler.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
