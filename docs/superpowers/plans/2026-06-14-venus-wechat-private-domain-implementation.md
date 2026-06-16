# Venus WeChat Private-Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run WeChat private-domain connector for Mini Program skincare Q&A and Enterprise WeChat handoff queues.

**Architecture:** Create `src/venus/wechat_private_domain.py` as a connector contract that turns local Mini Program session exports into answer queues, Enterprise WeChat handoff queues, summary metrics, and approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner without enabling live WeChat or Enterprise WeChat side effects.

**Tech Stack:** Python standard library, existing Venus persona and approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/wechat_private_domain.py`.
- Create `tests/test_wechat_private_domain.py`.
- Create `data/samples/wechat_private_domain.json`.
- Modify `src/venus/orchestrator.py`.
- Modify `src/venus/cli.py`.
- Modify `src/venus/feishu_entry.py`.
- Modify `src/venus/agent_run.py`.
- Modify `tests/test_cli_smoke.py`.
- Modify `tests/test_feishu_entry.py`.
- Modify `tests/test_agent_run.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Connector Tests

- [x] Add `tests/test_wechat_private_domain.py`.
- [x] Verify the first run fails because `venus.wechat_private_domain` does not exist.
- [x] Assert the connector returns `workflow: wechat`, Venus namespace, dry-run status, source metadata, summary metrics, answer queues, handoff queues, approval records, and `external_actions: []`.
- [x] Assert secret-like values, OpenIDs, WeChat IDs, phone numbers, and contact objects do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Connector Implementation

- [x] Create `src/venus/wechat_private_domain.py`.
- [x] Classify Mini Program questions by skincare risk and private-domain lead intent.
- [x] Build answer queues with approval levels and persona-styled drafts.
- [x] Build Enterprise WeChat handoff queues without exposing raw contact fields.
- [x] Add approval records for high-risk answers and handoff drafts.
- [x] Enforce dry-run mode and Venus namespace validation.
- [x] Run targeted connector tests and confirm they pass.

### Task 3: Routes And Samples

- [x] Add CLI workflow `wechat`.
- [x] Add Feishu dry-run command `/venus wechat`.
- [x] Add `data/samples/wechat_private_domain.json`.
- [x] Add WeChat private-domain summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli wechat data/samples/wechat_private_domain.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
