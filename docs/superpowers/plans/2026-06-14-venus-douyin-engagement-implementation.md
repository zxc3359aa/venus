# Venus Douyin Engagement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run Douyin engagement connector for imported video comments and live messages.

**Architecture:** Create `src/venus/douyin_engagement.py` as a connector contract that normalizes local Douyin-style inputs into summaries, reply queues, live queues, and approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner without enabling live platform side effects.

**Tech Stack:** Python standard library, existing Venus persona/comment/approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/douyin_engagement.py`.
- Create `tests/test_douyin_engagement.py`.
- Create `data/samples/douyin_engagement.json`.
- Modify `src/venus/comments.py`.
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

- [x] Add `tests/test_douyin_engagement.py`.
- [x] Verify the first run fails because `venus.douyin_engagement` does not exist.
- [x] Assert the connector returns `workflow: douyin`, Venus namespace, dry-run status, source metadata, summary metrics, reply queues, live queues, approval records, and `external_actions: []`.
- [x] Assert secret-like values and user IDs do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Connector Implementation

- [x] Create `src/venus/douyin_engagement.py`.
- [x] Normalize video comments into the existing comment analyzer.
- [x] Preserve comment/video metadata needed for reply queues.
- [x] Build per-video summaries and live-message queues.
- [x] Add approval records for public comment and live reply drafts.
- [x] Enforce dry-run mode and Venus namespace validation.
- [x] Run targeted connector tests and confirm they pass.

### Task 3: Routes And Samples

- [x] Add CLI workflow `douyin`.
- [x] Add Feishu dry-run command `/venus douyin`.
- [x] Add `data/samples/douyin_engagement.json`.
- [x] Add Douyin engagement summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli douyin data/samples/douyin_engagement.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
