# Venus Airtable Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run Airtable export workflow that packages Venus hotspots, products, comments, monitoring, and approvals into import-ready tables without touching live Airtable.

**Architecture:** Create `src/venus/airtable_export.py` for schema and record mapping, route it through `VenusOrchestrator`, expose it through CLI and Feishu dry-run, and add deterministic sample input. The output mirrors Airtable concepts: base, tables, fields, views, and records.

**Tech Stack:** Python standard library, local JSON fixtures, pytest, existing Venus orchestrator, CLI, and Feishu dry-run adapter.

---

## File Structure

- Create `src/venus/airtable_export.py`.
- Create `tests/test_airtable_export.py`.
- Create `data/samples/airtable_export.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify smoke and acceptance tests.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Airtable Export Unit Tests

- [x] Add `tests/test_airtable_export.py` for dry-run package behavior.
- [x] Assert the package includes Venus base metadata, table schemas, records, summary, and `external_actions: []`.
- [x] Assert Xiaolongxia namespaces are rejected.
- [x] Run `pytest tests/test_airtable_export.py -v` and confirm it fails because `venus.airtable_export` does not exist.

### Task 2: Airtable Export Implementation

- [x] Create `src/venus/airtable_export.py`.
- [x] Implement `AirtableExportConfig`.
- [x] Implement `build_airtable_sync_package(payload, config=None)`.
- [x] Reuse existing content, product, comments, and monitoring functions to enrich records.
- [x] Run `pytest tests/test_airtable_export.py -v` and confirm it passes.

### Task 3: Orchestrator, CLI, And Feishu

- [x] Add failing tests for `airtable` orchestrator, CLI, and `/venus airtable`.
- [x] Create `data/samples/airtable_export.json`.
- [x] Route `airtable` in `src/venus/orchestrator.py`.
- [x] Add `airtable` to CLI choices and payload mapping.
- [x] Add `/venus airtable` to Feishu dry-run help, defaults, and report routing.
- [x] Run targeted tests and confirm they pass.

### Task 4: Documentation And Verification

- [x] Update `README.md` with the Airtable dry-run command.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli airtable data/samples/airtable_export.json`.
- [x] Run `python3 -m venus.cli feishu data/samples/feishu_message.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
