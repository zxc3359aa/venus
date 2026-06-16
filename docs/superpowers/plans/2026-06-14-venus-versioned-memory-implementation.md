# Venus Versioned Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run versioned memory workflow that stages approved learning into proposed Venus memory without writing persistent memory.

**Architecture:** Create `src/venus/memory.py` as a focused contract that reviews learning candidates, filters sensitive content, builds a proposed next memory version, records a rollback plan, and emits approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner.

**Tech Stack:** Python standard library, existing Venus approval and backup helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/memory.py`.
- Create `tests/test_memory.py`.
- Create `data/samples/memory.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Connector Tests

- [x] Add `tests/test_memory.py`.
- [x] Verify the first run fails because `venus.memory` does not exist.
- [x] Assert the connector returns `workflow: memory`, Venus namespace, dry-run status, candidate reviews, memory diff, proposed memory, rollback plan, backup tasks, approval records, and `external_actions: []`.
- [x] Assert sensitive candidates are blocked and excluded from proposed memory.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Connector Implementation

- [x] Create `src/venus/memory.py`.
- [x] Normalize current memory, learning candidates, approval decisions, and backup metadata.
- [x] Classify candidates by category, decision, risk, and privacy sensitivity.
- [x] Merge approved non-sensitive candidates into a proposed next version without writing storage.
- [x] Build rollback and backup verification tasks.
- [x] Add approval records for memory merge and backup verification.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `memory`.
- [x] Add Feishu dry-run command `/venus memory`.
- [x] Add `data/samples/memory.json`.
- [x] Add memory summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted memory integration tests.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli memory data/samples/memory.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
