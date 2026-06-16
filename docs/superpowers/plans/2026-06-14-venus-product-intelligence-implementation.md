# Venus Product Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local dry-run product-intelligence workflow for brand backing, filing status, ingredient details, supplier documents, test reports, historical controversies, claim risk, and precise retrieval tasks.

**Architecture:** Create `src/venus/product_intelligence.py` as a focused deep-dossier builder that complements the existing simple `product` card. Route it through the orchestrator, CLI, Feishu dry-run adapter, and Agent Run planner while keeping live regulator, supplier, brand, crawler, and social-platform access disabled.

**Tech Stack:** Python standard library, existing Venus approval and product-risk helpers, pytest, local JSON fixtures.

---

## File Structure

- Create `src/venus/product_intelligence.py`.
- Create `tests/test_product_intelligence.py`.
- Create `data/samples/product_intelligence.json`.
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

### Task 1: Product Intelligence Tests

- [x] Add `tests/test_product_intelligence.py`.
- [x] Verify the first run fails because `venus.product_intelligence` does not exist.
- [x] Assert the workflow returns `workflow: product_intel`, Venus namespace, dry-run status, filing check, brand backing, ingredient matrix, supplier checks, test report checks, controversy scan, claim risk, retrieval plan, approval records, and `external_actions: []`.
- [x] Assert secret-like values do not leak.
- [x] Assert Xiaolongxia namespace values are rejected.

### Task 2: Product Intelligence Implementation

- [x] Create `src/venus/product_intelligence.py`.
- [x] Build brand backing verification states.
- [x] Build filing check, ingredient matrix, supplier document checks, and test report checks.
- [x] Build historical controversy scan and claim-risk summary.
- [x] Build precise retrieval tasks for missing or unverified evidence.
- [x] Add approval records for live connector enablement and product claim review.
- [x] Enforce dry-run mode and Venus namespace validation.

### Task 3: Routes And Samples

- [x] Add CLI workflow `product-intel`.
- [x] Add Feishu dry-run command `/venus product-intel`.
- [x] Add `data/samples/product_intelligence.json`.
- [x] Add product-intel summary support to Agent Run.
- [x] Add CLI, Feishu, and Agent Run tests.
- [x] Run targeted integration tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [ ] Run `pytest -v`.
- [ ] Run `python3 -m venus.cli product-intel data/samples/product_intelligence.json`.
- [ ] Run `python3 -m venus.cli agent-run data/samples/agent_run.json`.
- [ ] Run `git diff --check`.
- [ ] Commit and push the changes.
