# Venus Connector Dispatch Rehearsal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local connector dispatch rehearsal workflow that turns connector execution manifests into platform request drafts, credential-readiness checks, audit packets, and rollback packets without performing external actions.

**Architecture:** Create `src/venus/connector_dispatch.py` using the existing Venus workflow shape: config validation, redaction, optional `JsonStore` input, deterministic record generation, idempotent local persistence, approval records, rollback plan, and `external_actions: []`. Route it through orchestrator, CLI, and Feishu.

**Tech Stack:** Python standard library, existing `JsonStore`, existing approval helpers, pytest, deterministic JSON samples.

---

## File Structure

- Create `src/venus/connector_dispatch.py`: config, surface request templates, credential checks, blocker rules, request envelopes, audit packets, local persistence, approvals, rollback, redaction.
- Create `tests/test_connector_dispatch.py`: unit coverage for request drafts, credential blocking, high-risk blocking, idempotency, approval gating, redaction, and config isolation.
- Create `data/samples/connector_dispatch.json`: safe sample with Feishu/Airtable ready, Douyin missing credential, Qianchuan high risk, and WeChat external override.
- Modify `src/venus/orchestrator.py`: import and route `build_connector_dispatch_rehearsal`.
- Modify `src/venus/cli.py`: add `connector-dispatch` command and map to `connector_dispatch`.
- Modify `src/venus/feishu_entry.py`: add `/venus connector-dispatch`, default sample path, route mapping, and summary.
- Modify `tests/test_cli_smoke.py`: add connector-dispatch smoke.
- Modify `tests/test_feishu_entry.py`: add default path assertion, help text assertion, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the rehearsal layer.

## Task 1: Tests First

- [x] Create `tests/test_connector_dispatch.py`.
- [x] Assert ready Feishu and Airtable execution manifests create local dispatch rehearsal records.
- [x] Assert missing credentials, high-risk level-4 dispatch candidates, and external overrides are blocked.
- [x] Assert `live_dispatch_requested` creates a level-4 approval record without execution.
- [x] Assert a second run is idempotent for existing rehearsal records.
- [x] Assert missing dispatch approval review blocks writes.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus connector-dispatch data/samples/connector_dispatch.json`.
- [x] Add Feishu route test for `/venus connector-dispatch`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Dispatch Rehearsal Workflow

- [x] Add `ConnectorDispatchConfig`.
- [x] Add supported surface request template mapping.
- [x] Load `execution_records` from payload or `data/venus/connector_execution_manifests.json`.
- [x] Build credential readiness from safe boolean environment flags.
- [x] Match dispatch overrides by execution, draft, or action id.
- [x] Block unsupported surfaces, non-ready executions, external executions, missing credential refs, external overrides, and high-risk dispatches.
- [x] Create deterministic rehearsal records with request envelopes, audit packets, rollback packets, and external actions disabled.
- [x] Write only local `connector_dispatch_rehearsals` records when requested and approved.
- [x] Add rollback plan and safety boundary.
- [x] Add approval records for live dispatch request and high-risk dispatch review.
- [x] Return `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_connector_dispatch_rehearsal` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `connector-dispatch`.
- [x] Add Feishu command `/venus connector-dispatch`, default sample path, route mapping, and report summary.
- [x] Add deterministic `data/samples/connector_dispatch.json`.

## Task 4: Docs And Verification

- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted connector dispatch tests.
- [x] Run CLI smokes:
  - `python3 -m venus.cli connector-dispatch data/samples/connector_dispatch.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `pytest -q`.
- [x] Run `git diff --check`.
- [x] Confirm `find data/venus -maxdepth 1 -type f -print` only shows `.gitkeep`.
- [x] Commit with `feat: add connector dispatch rehearsal`.
- [x] Push to `codex/venus-feishu-entry`.
