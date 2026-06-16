# Venus Performance Calibration Implementation Plan

**Goal:** Add a dry-run performance calibration workflow that feeds published short-video metrics back into Venus' content strategy, without live Douyin access or external side effects.

**Architecture:** Create `src/venus/performance.py` as a deterministic KPI and learning-rule module. Route it through the existing orchestrator, CLI, Feishu entry, and Agent Run aggregator. Keep every platform or learning mutation as an approval record.

**Tech Stack:** Python standard library, existing approval helper, pytest, local sample JSON.

## Task 1: Tests First

- [x] Create `tests/test_performance.py`.
- [x] Assert summary metrics, winner/underperformer classification, leaderboard order, growth score, KPI definitions, calibration rules, approval records, redaction, and config isolation.
- [x] Extend CLI smoke tests with `performance`.
- [x] Extend Feishu tests with `/venus performance`.
- [x] Extend Agent Run tests with performance summary.
- [x] Run targeted tests and confirm they fail before implementation.

## Task 2: Core Workflow

- [x] Add `PerformanceConfig` with Venus namespace validation and dry-run enforcement.
- [x] Add recursive secret redaction.
- [x] Normalize targets and video metrics.
- [x] Compute pass/fail flags, winner state, negative-feedback alerts, and growth score.
- [x] Build summary, leaderboard, winners, underperformers, KPI definitions, calibration rules, next actions, approval records, and safety boundary.

## Task 3: Routing

- [x] Import and route `build_performance_report` in `src/venus/orchestrator.py`.
- [x] Add CLI choice `performance`.
- [x] Add Feishu command, default sample path, workflow mapping, and summary text.
- [x] Add Agent Run `performance` section and workflow summary.

## Task 4: Samples And Docs

- [x] Add `data/samples/performance.json`.
- [x] Add the performance payload to `data/samples/agent_run.json`.
- [x] Update README usage.
- [x] Update `task_plan.md` and `progress.md`.

## Task 5: Verification And Delivery

- [x] Run targeted tests for performance, CLI, Feishu, and Agent Run.
- [x] Run full `pytest -v`.
- [x] Run CLI smokes for `performance`, `feishu`, and `agent-run`.
- [x] Run `git diff --check`.
- [ ] Stage, commit, and push the branch so the existing PR updates.

## Review

- Scope is intentionally local and dry-run.
- The workflow does not use live Douyin, Feishu, WeChat, Qianchuan, Xingtu, Airtable, or Enterprise WeChat connectors.
- Learning and next-content actions are review records, not automatic memory writes or publishing actions.
