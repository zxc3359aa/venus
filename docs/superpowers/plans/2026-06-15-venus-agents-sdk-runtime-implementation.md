# Venus Agents SDK Runtime Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local Agents SDK-ready runtime manifest workflow for Venus without installing dependencies or calling OpenAI.

**Architecture:** Create `src/venus/agents_sdk_runtime.py` to assemble an SDK-style manifest from existing Venus workflows, eval status, and environment readiness. Route it through orchestrator, CLI, and Feishu while preserving dry-run and approval gates.

**Tech Stack:** Python standard library, existing Venus approval helpers, pytest, deterministic JSON samples.

---

## File Structure

- Create `src/venus/agents_sdk_runtime.py`: config, tool registry, agent manifest, runtime plan, readiness checks, approval records, and safety boundary.
- Create `tests/test_agents_sdk_runtime.py`: manifest generation, readiness blockers, tool blocking, live approval, and isolation tests.
- Create `data/samples/agents_sdk.json`: safe sample with live SDK disabled and dependencies missing.
- Modify `src/venus/orchestrator.py`: route `agents_sdk`.
- Modify `src/venus/cli.py`: add `agents-sdk` command.
- Modify `src/venus/feishu_entry.py`: add `/venus agents-sdk`, default sample path, route mapping, and summary text.
- Modify `tests/test_cli_smoke.py`: add CLI smoke.
- Modify `tests/test_feishu_entry.py`: add default path, help text, sample writer, and route test.
- Modify `README.md`, `task_plan.md`, and `progress.md`: document the SDK runtime manifest.

## Task 1: Tests First

- [x] Create `tests/test_agents_sdk_runtime.py`.
- [x] Assert the manifest contains one primary Venus agent.
- [x] Assert the tool registry includes core local workflows and keeps all external actions disabled.
- [x] Assert readiness blocks when `OPENAI_API_KEY` and `openai-agents` are missing.
- [x] Assert live SDK requests create a level-4 approval record without execution.
- [x] Assert externally-enabled tool overrides are blocked.
- [x] Assert Xiaolongxia config is rejected.
- [x] Add CLI smoke for `venus agents-sdk data/samples/agents_sdk.json`.
- [x] Add Feishu route test for `/venus agents-sdk`.
- [x] Run targeted tests and confirm RED before implementation.

## Task 2: Core Manifest Workflow

- [x] Add `AgentsSdkRuntimeConfig`.
- [x] Add default local tool registry for existing Venus workflows.
- [x] Merge safe `tool_overrides` while blocking externally-enabled tools.
- [x] Add `agent_manifest` with instructions, model env var, output contract, and namespace.
- [x] Add `runtime_plan` for server-managed state, approvals, evals, and future SDK command.
- [x] Add readiness checks for API key, dependency, eval readiness, and external action lock.
- [x] Add level-4 approval record for `live_sdk_requested`.
- [x] Return `external_actions: []`.

## Task 3: Routing

- [x] Import and route `build_agents_sdk_manifest` in `src/venus/orchestrator.py`.
- [x] Add CLI workflow `agents-sdk`.
- [x] Add Feishu command `/venus agents-sdk`, default sample path, route mapping, and report summary.

## Task 4: Docs And Verification

- [x] Add `data/samples/agents_sdk.json`.
- [x] Update README smoke commands and Feishu support list.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run targeted Agents SDK runtime tests.
- [x] Run `pytest -q`.
- [x] Run CLI smokes:
  - `python3 -m venus.cli agents-sdk data/samples/agents_sdk.json`
  - `python3 -m venus.cli feishu data/samples/feishu_message.json`
- [x] Run `git diff --check`.
- [x] Commit with `feat: add agents sdk runtime manifest`.
- [x] Push to `codex/venus-feishu-entry`.
