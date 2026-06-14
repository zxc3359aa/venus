# Venus Connector Execution Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local connector execution gateway that turns approved delivery drafts and connector readiness records into platform-specific execution manifests without performing external actions.

**Architecture:** Create `src/venus/connector_execution.py` following the existing local workflow pattern: config validation, recursive redaction, input loading from payload or `JsonStore`, deterministic local record generation, idempotent storage writes, approval records, rollback plan, and `external_actions: []`. Route it through orchestrator, CLI, and Feishu.

**Tech Stack:** Python standard library, existing `JsonStore`, existing approval helpers, pytest, deterministic JSON sample data.

---

## File Structure

- Create `src/venus/connector_execution.py`: config, adapter map, draft/connector matching, blocker rules, manifest records, local persistence, approvals, redaction, rollback.
- Create `tests/test_connector_execution.py`: direct unit coverage for records, blockers, idempotency, approval gating, redaction, and config isolation.
- Create `data/samples/connector_execution.json`: safe sample with Feishu/Airtable ready, Douyin missing permission, Qianchuan high risk, and an external override attempt.
- Modify `src/venus/orchestrator.py`: import and route `build_connector_execution_plan`.
- Modify `src/venus/cli.py`: add `connector-execution` command and map to `connector_execution`.
- Modify `src/venus/feishu_entry.py`: add `/venus connector-execution`, default sample path, route mapping, and summary.
- Modify `tests/test_cli_smoke.py`: add connector-execution smoke.
- Modify `tests/test_feishu_entry.py`: add default path assertion, help text assertion, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the gateway.

## Task 1: Tests First

- [x] Create `tests/test_connector_execution.py`.
- [x] Assert ready Feishu and Airtable drafts create local execution manifests.
- [x] Assert missing connector readiness, missing permissions, high-risk level-4 drafts, and external overrides are blocked.
- [x] Assert `live_dispatch_requested` creates a level-4 approval record without execution.
- [x] Assert a second run is idempotent for existing local manifests.
- [x] Assert missing approval review blocks writes.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus connector-execution data/samples/connector_execution.json`.
- [x] Add Feishu route test for `/venus connector-execution`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Gateway Workflow

- [x] Add `ConnectorExecutionConfig`.
- [x] Add supported surface to adapter-type mapping.
- [x] Load `draft_records` from payload or `data/venus/delivery_drafts.json`.
- [x] Load connector reviews from payload.
- [x] Build surface readiness from connector reviews.
- [x] Match drafts to connector reviews by `target_surface` or `surface`.
- [x] Block unsupported surfaces, missing connector reviews, not-ready connectors, missing permissions, missing audit/rollback readiness, external drafts, non-local-review drafts, external overrides, and high-risk level-4 actions.
- [x] Create deterministic execution records with external actions disabled.
- [x] Write only local `connector_execution_manifests` records when requested and approved.
- [x] Add rollback plan and safety boundary.
- [x] Add approval records for live dispatch request and high-risk execution review.
- [x] Return `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_connector_execution_plan` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `connector-execution`.
- [x] Add Feishu command `/venus connector-execution`, default sample path, route mapping, and report summary.
- [x] Add deterministic `data/samples/connector_execution.json`.

## Task 4: Docs And Verification

- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted connector execution tests.
- [x] Run CLI smokes:
  - `python3 -m venus.cli connector-execution data/samples/connector_execution.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `pytest -q`.
- [x] Run `git diff --check`.
- [x] Confirm `find data/venus -maxdepth 1 -type f -print` only shows `.gitkeep`.
- [x] Commit with `feat: add connector execution gateway`.
- [x] Push to `codex/venus-feishu-entry`.
