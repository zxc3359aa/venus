# Venus Ecommerce Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run Douyin ecommerce operations workflow for shop products, inventory, live product cards, promotions, and after-sales risk.

**Architecture:** Create `src/venus/ecommerce.py` as a connector contract that normalizes local Douyin Shop-style inputs into catalog checks, inventory alerts, pricing recommendations, live product-card plans, after-sales watchlists, conversion recommendations, and approval records. Route it through the existing orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner without enabling live shop side effects.

**Tech Stack:** Python standard library, existing Venus approval helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/ecommerce.py`.
- Create `tests/test_ecommerce.py`.
- Create `data/samples/ecommerce.json`.
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

- [x] Add `tests/test_ecommerce.py`.
- [x] Verify the first run fails because `venus.ecommerce` does not exist.
- [x] Assert the connector returns `workflow: ecommerce`, Venus namespace, dry-run status, summary metrics, catalog checks, inventory alerts, pricing recommendations, live product-card plans, after-sales watchlist, approval records, and `external_actions: []`.
- [x] Assert secret-like values and Xiaolongxia references do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Connector Implementation

- [x] Create `src/venus/ecommerce.py`.
- [x] Normalize product, live-room, promotion, and after-sales inputs.
- [x] Build product catalog checks and low-stock alerts.
- [x] Build live product-card and pricing recommendations behind approval gates.
- [x] Add approval records for live connector, product-card updates, and promotion or price changes.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `ecommerce`.
- [x] Add Feishu dry-run command `/venus ecommerce`.
- [x] Add `data/samples/ecommerce.json`.
- [x] Add ecommerce summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted ecommerce integration tests.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli ecommerce data/samples/ecommerce.json`.
- [x] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
