# Venus Agent Run Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local Agent Run planner that composes current Venus workflows into one approval-gated operating cycle.

**Architecture:** Create `src/venus/agent_run.py` as a dry-run orchestration contract. Route it through the existing `VenusOrchestrator`, CLI, and Feishu adapter. Keep all future platform actions represented as pending review records rather than side effects.

**Tech Stack:** Python standard library, existing Venus workflow functions, pytest, local sample JSON.

---

## File Structure

- Create `src/venus/agent_run.py`.
- Create `tests/test_agent_run.py`.
- Create `data/samples/agent_run.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Agent Run Tests

- [x] Add unit tests for the Agent Run planner.
- [x] Verify the first run fails because the module or behavior is missing.
- [x] Assert local workflows are summarized in order: hotspot, product, comments, monitoring, Airtable.
- [x] Assert external surfaces map to approval levels 2-4 and produce pending records.
- [x] Assert secret-like payload values do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Agent Run Implementation

- [x] Create `src/venus/agent_run.py`.
- [x] Reuse existing workflow functions for hotspot, product, comments, monitoring, and Airtable packaging.
- [x] Add dry-run config validation and Venus namespace checks.
- [x] Add action-plan templates for Feishu, Airtable, Douyin comments, Qianchuan, Xingtu, and WeChat private-domain handoff.
- [x] Add approval records for level 2-4 actions.
- [x] Run targeted tests and confirm they pass.

### Task 3: CLI And Feishu Entry

- [x] Add CLI workflow `agent-run`.
- [x] Add `data/samples/agent_run.json`.
- [x] Add Feishu dry-run command `/venus agent-run`.
- [x] Add CLI and Feishu tests.
- [x] Run targeted tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
