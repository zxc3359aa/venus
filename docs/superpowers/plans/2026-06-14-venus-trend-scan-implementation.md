# Venus Trend Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run trend-scan workflow that normalizes Douyin beauty/skincare hot topics, products, creators, comments, ingredients, tags, and controversies into ranked content opportunities.

**Architecture:** Create `src/venus/trend_scan.py` as a focused signal-normalization and ranking module. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner while keeping live Douyin reads, login, scraping, browser automation, and API calls disabled.

**Tech Stack:** Python standard library, existing Venus approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/trend_scan.py`.
- Create `tests/test_trend_scan.py`.
- Create `data/samples/trend_scan.json`.
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

### Task 1: Trend Scan Tests

- [x] Add `tests/test_trend_scan.py`.
- [x] Verify the first run fails because `venus.trend_scan` does not exist.
- [x] Assert the workflow returns `workflow: trend_scan`, Venus namespace, dry-run status, all seven signal categories, leaderboard, trend clusters, content opportunities, watch plan, approval records, and `external_actions: []`.
- [x] Assert secret-like values do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Trend Scan Implementation

- [x] Create `src/venus/trend_scan.py`.
- [x] Normalize topics, products, creators, comments, ingredients, tags, and controversies into a single signal schema.
- [x] Score and rank signals by volume, growth, and controversy.
- [x] Build trend clusters and content opportunities.
- [x] Build watch plan with refresh interval, coverage targets, gap alerts, and live connector state.
- [x] Add approval records for live connector enablement.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `trend-scan`.
- [x] Add Feishu dry-run command `/venus trend-scan`.
- [x] Add `data/samples/trend_scan.json`.
- [x] Add trend-scan summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [ ] Run `pytest -v`.
- [ ] Run `python3 -m venus.cli trend-scan data/samples/trend_scan.json`.
- [ ] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [ ] Run `git diff --check`.
- [ ] Commit and push the changes.
