# Venus Commercial Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run commercial strategy workflow for Qianchuan budget guidance and Xingtu brief review.

**Architecture:** Create `src/venus/commercial_strategy.py` as a connector contract that turns local campaign/brief inputs into budget guardrails, Xingtu risk review, commercial script recommendations, and approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner without enabling ad spend or brand-side effects.

**Tech Stack:** Python standard library, existing Venus persona and approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/commercial_strategy.py`.
- Create `tests/test_commercial_strategy.py`.
- Create `data/samples/commercial_strategy.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Commercial Strategy Tests

- [x] Add `tests/test_commercial_strategy.py`.
- [x] Verify the first run fails because `venus.commercial_strategy` does not exist.
- [x] Assert the connector returns `workflow: commercial`, Venus namespace, dry-run status, source metadata, summary metrics, Qianchuan recommendations, Xingtu brief reviews, script recommendations, approval records, and `external_actions: []`.
- [x] Assert secret-like values do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Commercial Strategy Implementation

- [x] Create `src/venus/commercial_strategy.py`.
- [x] Build Qianchuan budget guardrails from budget, spend, ROI, audiences, and creative metrics.
- [x] Build Xingtu brief risk review from product, requirements, forbidden claims, budget, and deliverables.
- [x] Build short-video ad and live-slice script recommendations in the user's style.
- [x] Add approval records for budget recommendations, brief decisions, and brand commitments.
- [x] Enforce dry-run mode and Venus namespace validation.
- [x] Run targeted connector tests and confirm they pass.

### Task 3: Routes And Samples

- [x] Add CLI workflow `commercial`.
- [x] Add Feishu dry-run command `/venus commercial`.
- [x] Add `data/samples/commercial_strategy.json`.
- [x] Add commercial strategy summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli commercial data/samples/commercial_strategy.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
