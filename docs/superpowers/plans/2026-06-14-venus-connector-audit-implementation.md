# Venus Connector Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run connector audit workflow that evaluates live integration readiness without touching credentials or external platforms.

**Architecture:** Create `src/venus/connector_audit.py` as a focused contract that reviews connector definitions, computes permission/audit/rollback gaps, builds a launch sequence, and emits approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner.

**Tech Stack:** Python standard library, existing Venus approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/connector_audit.py`.
- Create `tests/test_connector_audit.py`.
- Create `data/samples/connectors.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Connector Audit Tests

- [x] Add `tests/test_connector_audit.py`.
- [x] Verify the first run fails because `venus.connector_audit` does not exist.
- [x] Assert the report returns `workflow: connectors`, Venus namespace, dry-run status, connector reviews, permission matrix, readiness gaps, launch sequence, approval records, and `external_actions: []`.
- [x] Assert missing permissions, missing audit logs, and missing rollback plans are detected.
- [x] Assert blocked connectors are excluded from launch sequence.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Connector Audit Implementation

- [x] Create `src/venus/connector_audit.py`.
- [x] Normalize connector definitions and required/granted permissions.
- [x] Compute missing permissions, audit readiness, rollback readiness, risk levels, and execution states.
- [x] Build readiness gaps sorted by severity.
- [x] Build launch sequence for ready connectors only.
- [x] Add approval records for live connector enablement and high-risk connector review.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `connectors`.
- [x] Add Feishu dry-run command `/venus connectors`.
- [x] Add `data/samples/connectors.json`.
- [x] Add connector readiness summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted connector audit integration tests.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli connectors data/samples/connectors.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [x] Commit and push the changes.
