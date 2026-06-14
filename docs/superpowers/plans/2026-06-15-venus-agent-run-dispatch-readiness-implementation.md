# Venus Agent Run Dispatch Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add connector execution and connector dispatch readiness summaries to Agent Run and make evals check those last-mile connector gates before live autopilot readiness.

**Architecture:** Reuse existing local builders `build_connector_execution_plan` and `build_connector_dispatch_rehearsal` inside `agent_run.py` when corresponding payloads are present. Add a new eval gate in `evals.py` that reads Agent Run workflow summaries and blocks autopilot when execution or dispatch readiness is missing or blocked.

**Tech Stack:** Python standard library, existing Venus workflow builders, pytest, deterministic JSON samples.

---

## File Structure

- Modify `src/venus/agent_run.py`: import connector execution/dispatch builders, read optional payloads, add summaries.
- Modify `src/venus/evals.py`: add default gate, gate definition, check function, and readiness status branch.
- Modify `tests/test_agent_run.py`: add payload fields and assertions for connector execution/dispatch summaries.
- Modify `tests/test_evals.py`: update default counts and add pass/fail coverage for new gate.
- Modify `data/samples/agent_run.json`: include safe connector execution and dispatch payloads.
- Modify `data/samples/evals.json`: include workflow summaries for connector execution and dispatch.
- Modify `task_plan.md` and `progress.md`: document the new orchestration coverage.

## Task 1: Tests First

- [x] Add connector execution and dispatch payloads for Agent Run coverage.
- [x] Assert Agent Run `executed_workflows` includes `connector_execution` and `connector_dispatch`.
- [x] Assert Agent Run summaries include execution state, dispatch state, record counts, blocked counts, and approval record counts.
- [x] Update eval summary expectations for the new default gate count.
- [x] Assert evals fail with `connector_dispatch_readiness` when connector execution or dispatch has blocked items.
- [x] Add an eval test that clears connector audit, execution, and dispatch blockers and passes all gates.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Agent Run Integration

- [x] Import `build_connector_execution_plan` and `build_connector_dispatch_rehearsal`.
- [x] Read `connector_execution` and `connector_dispatch` from the safe payload.
- [x] Run and summarize connector execution when present.
- [x] Run and summarize connector dispatch when present.
- [x] Preserve `external_actions: []`.

## Task 3: Eval Gate

- [x] Add `eval-connector-dispatch-readiness` to `DEFAULT_CASES`.
- [x] Add `connector_dispatch_readiness` to `GATE_DEFINITIONS`.
- [x] Route `_evaluate_case` to a new `_check_connector_dispatch_readiness`.
- [x] Fail when last-mile summaries are missing or blocked.
- [x] Pass when connector execution and dispatch are clean.
- [x] Return `blocked_by_connector_dispatch_readiness` when this gate is the top blocker.
- [x] Add next action `resolve_connector_dispatch_readiness` for this gate.

## Task 4: Samples, Docs, Verification

- [x] Update `data/samples/agent_run.json`.
- [x] Update `data/samples/evals.json`.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted Agent Run and eval tests.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `python3 -m venus.cli evals data/samples/evals.json`.
- [x] Run `pytest -q`.
- [x] Run `git diff --check`.
- [x] Confirm `find data/venus -maxdepth 1 -type f -print` only shows `.gitkeep`.
- [x] Commit with `feat: add agent run dispatch readiness`.
- [x] Push to `codex/venus-feishu-entry`.
