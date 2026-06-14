# Venus Content Eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run content evaluation workflow that scores Venus short-video packages for growth quality, persona fit, evidence clarity, and claim safety before publishing.

**Architecture:** Create `src/venus/content_eval.py` as a focused contract that reviews script and production-package fields, computes deterministic KPI scores, produces revision tasks, and emits approval records. Route it through the orchestrator, CLI, Feishu dry-run adapter, and Agent Run.

**Tech Stack:** Python standard library, existing Venus approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/content_eval.py`.
- Create `tests/test_content_eval.py`.
- Create `data/samples/content_eval.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Content Eval Tests

- [x] Add `tests/test_content_eval.py`.
- [x] Verify the first run fails because `venus.content_eval` does not exist.
- [x] Assert the report returns `workflow: content_eval`, Venus namespace, dry-run status, KPI scorecard, publish readiness, revision queue, approval records, and `external_actions: []`.
- [x] Assert weak hooks, generic CTAs, missing evidence framing, and absolute skincare claims create revision tasks.
- [x] Assert high claim risk can block publishing even when other growth scores are usable.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Content Eval Implementation

- [x] Create `src/venus/content_eval.py`.
- [x] Normalize script, shot, edit, subtitle, and publish-package fields.
- [x] Compute retention, interaction, comment, follow, persona, and safety scores.
- [x] Build publish-readiness status from score thresholds and claim-risk blockers.
- [x] Build a prioritized revision queue with concrete fixes.
- [x] Add approval records for content revision and publish review.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `content-eval`.
- [x] Add Feishu dry-run command `/venus content-eval`.
- [x] Add `data/samples/content_eval.json`.
- [x] Add content-eval readiness summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted content-eval integration tests.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli content-eval data/samples/content_eval.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [x] Commit and push the changes.
