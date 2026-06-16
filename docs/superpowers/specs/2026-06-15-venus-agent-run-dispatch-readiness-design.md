# Venus Agent Run Dispatch Readiness Design

## Purpose

Venus now has local connector execution manifests and connector dispatch rehearsals. The main Agent Run still summarizes connector audit readiness, but it does not yet surface the two last-mile gates. This slice folds those new gates into the Agent Run and eval readiness view so one Venus run can show whether connector execution and dispatch are ready, blocked, or still review-only.

## Scope

This is a local orchestration update only. It does not call connector APIs, dispatch messages, read credentials, or mutate external state.

Add Agent Run support for optional payload keys:

- `connector_execution`: payload for `build_connector_execution_plan`.
- `connector_dispatch`: payload for `build_connector_dispatch_rehearsal`.

Add eval support for a new gate:

- `connector_dispatch_readiness`: checks connector execution and dispatch summaries before live autopilot can be considered ready.

## Agent Run Behavior

When `connector_execution` is present:

- Run `build_connector_execution_plan`.
- Add `connector_execution` to `executed_workflows`.
- Add a workflow summary with execution record count, blocked count, duplicate count, approval record count, and execution state.

When `connector_dispatch` is present:

- Run `build_connector_dispatch_rehearsal`.
- Add `connector_dispatch` to `executed_workflows`.
- Add a workflow summary with rehearsal record count, blocked count, duplicate count, approval record count, and dispatch state.

Both workflows must preserve `external_actions: []`.

## Eval Behavior

Add `connector_dispatch_readiness` to the default eval cases and gate definitions.

The gate fails when:

- Connector execution summary has `blocked_count > 0`.
- Connector dispatch summary has `blocked_count > 0`.
- Connector execution or dispatch summaries are missing from the Agent Run when the new gate is present.
- Either summary reports approval records without an explicit blocked/review state.

The gate passes when both summaries exist, both blocked counts are zero, and their state values indicate local manifest/rehearsal readiness or already-produced records.

If this gate fails, readiness status should be `blocked_by_connector_dispatch_readiness` unless the earlier connector audit readiness gate fails first.

## Safety And Isolation

- Agent Run and evals remain dry-run and manual approval only.
- No Feishu message, Airtable write, Douyin reply, Douyin publish, ad spend, Xingtu commitment, WeChat contact, OpenAI model call, backup write, memory write, or external platform state change occurs.
- Secret-like payload values stay redacted.
- Xiaolongxia references remain rejected through config guards and privacy checks.

## Integration

Modify:

- `src/venus/agent_run.py`
- `src/venus/evals.py`
- `tests/test_agent_run.py`
- `tests/test_evals.py`
- `data/samples/agent_run.json`
- `data/samples/evals.json`
- `progress.md`
- `task_plan.md`

## Acceptance Criteria

- Agent Run tests prove connector execution and connector dispatch summaries are included when payloads are present.
- Eval tests prove the new gate fails on blocked dispatch readiness and can pass when both last-mile summaries are clean.
- Existing dry-run external action guarantees remain unchanged.
- `pytest -q` passes.
- `git diff --check` passes.
