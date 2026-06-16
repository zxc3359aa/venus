# Venus Video Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run video-production workflow that generates professional short-video copy, shot lists, editing timelines, subtitles, asset checklists, and publishing drafts.

**Architecture:** Create `src/venus/video_production.py` as a focused production-package builder. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner while keeping rendering, editor automation, uploads, and publishing disabled.

**Tech Stack:** Python standard library, existing Venus persona and approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/video_production.py`.
- Create `tests/test_video_production.py`.
- Create `data/samples/video_production.json`.
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

### Task 1: Production Tests

- [x] Add `tests/test_video_production.py`.
- [x] Verify the first run fails because `venus.video_production` does not exist.
- [x] Assert the workflow returns `workflow: production`, Venus namespace, dry-run status, script package, shot list, edit plan, subtitle cards, asset checklist, publish package, approval records, and `external_actions: []`.
- [x] Assert secret-like values do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Production Implementation

- [x] Create `src/venus/video_production.py`.
- [x] Build persona-aware hooks, body segments, CTAs, comment prompts, and title options.
- [x] Build a five-scene short-video shot list with timing, visual direction, B-roll, and retention goals.
- [x] Build editing timeline instructions, subtitle cards, asset checklist, and publish package.
- [x] Add approval records for claim review and publishing review.
- [x] Enforce dry-run mode and Venus namespace validation.
- [x] Run targeted connector tests and confirm they pass.

### Task 3: Routes And Samples

- [x] Add CLI workflow `production`.
- [x] Add Feishu dry-run command `/venus production`.
- [x] Add `data/samples/video_production.json`.
- [x] Add production summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [ ] Run `pytest -v`.
- [ ] Run `python3 -m venus.cli production data/samples/video_production.json`.
- [ ] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [ ] Run `git diff --check`.
- [ ] Commit and push the changes.
