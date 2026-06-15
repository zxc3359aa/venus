# Venus Analytics Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run analytics monitoring workflow that ranks competitor accounts, summarizes video/live/ad/comment signals, and returns actionable Venus recommendations with no external actions.

**Architecture:** Create a focused `src/venus/monitoring.py` module and route it through the existing `VenusOrchestrator` and CLI. The implementation accepts local JSON samples now and keeps a connector-ready data contract for later Douyin, Qianchuan, Xingtu, and live-comment sources.

**Tech Stack:** Python standard library, local JSON fixtures, pytest, existing Venus CLI and orchestrator.

---

## File Structure

- Create `src/venus/monitoring.py` for scoring, aggregation, leaderboard rows, risk watchlist, and recommendations.
- Create `tests/test_monitoring.py` for unit behavior.
- Modify `src/venus/orchestrator.py` to route `monitoring`.
- Modify `src/venus/cli.py` to expose `venus monitoring <file>`.
- Modify `tests/test_cli_smoke.py` and `tests/test_end_to_end_acceptance.py` for smoke coverage.
- Add `data/samples/competitors.json`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Monitoring Unit Tests

- [x] Add `tests/test_monitoring.py` with a sample competitor payload.
- [x] Assert the top account is ranked by completion, engagement, and manageable risk.
- [x] Assert ad ratio, live hours, risk count, and opportunities are calculated.
- [x] Run `pytest tests/test_monitoring.py -v` and confirm it fails because `venus.monitoring` does not exist.

### Task 2: Monitoring Implementation

- [x] Create `src/venus/monitoring.py`.
- [x] Implement `build_monitoring_report(payload)`.
- [x] Keep missing optional fields safe and deterministic.
- [x] Raise `ValueError` when no competitors are provided.
- [x] Run `pytest tests/test_monitoring.py -v` and confirm it passes.

### Task 3: Orchestrator And CLI

- [x] Add a failing orchestrator smoke test for `monitoring`.
- [x] Add a failing CLI smoke test for `venus monitoring data/samples/competitors.json`.
- [x] Add `data/samples/competitors.json`.
- [x] Route `monitoring` in `src/venus/orchestrator.py`.
- [x] Add `monitoring` to CLI choices and payload mapping.
- [x] Run targeted CLI/orchestrator tests and confirm they pass.

### Task 4: Documentation And Verification

- [x] Update `README.md` smoke commands.
- [x] Update `task_plan.md` and `progress.md` with Phase 8 progress.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli monitoring data/samples/competitors.json`.
- [x] Check `git status -sb` and commit the Phase 8 changes.
