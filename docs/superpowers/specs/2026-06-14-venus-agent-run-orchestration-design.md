# Venus Agent Run Orchestration Design

Date: 2026-06-14

## Purpose

This slice adds a local Agent Run layer for Venus. It turns the existing hotspot, product, comment, competitor monitoring, and Airtable packaging workflows into one approval-gated operating plan.

The layer is meant to become the contract that future OpenAI Agents SDK runners, schedulers, Douyin connectors, Feishu reports, WeChat private-domain flows, Qianchuan, Xingtu, and Airtable writes can call after credentials and eval gates are ready. This first version stays local and dry-run only.

## Contract

`build_agent_run_plan(payload)` returns:

- `workflow: agent_run`.
- `run_id`, trigger, requested time, and Venus namespace.
- `executed_workflows` for the local workflows that ran.
- `workflow_summaries` for hotspot, product, comments, monitoring, and Airtable.
- `action_plan` with proposed next actions and approval levels.
- `approval_records` for every action at approval level 2 or higher.
- `external_actions: []`.

The CLI supports:

```bash
venus agent-run data/samples/agent_run.json
```

The Feishu dry-run adapter supports:

```text
/venus agent-run
```

Both surfaces return structured JSON/card-ready drafts only.

## Approval Boundaries

The Agent Run layer follows the existing Venus approval model:

- Level 1: local creator drafts such as short-video scripts.
- Level 2: private external surfaces such as Feishu reports or Airtable sync review.
- Level 3: public platform actions such as Douyin comment replies.
- Level 4: money, reputation, compliance, or customer-routing surfaces such as Qianchuan, Xingtu, and WeChat private-domain handoff.

Level 2-4 actions are represented as pending approval records. They are not executed.

## Safety

- The config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like keys are redacted before summaries, drafts, or approval records are produced.
- The output must never include executed external actions.
- Future OpenAI Agents SDK usage requires an API key gate, evals, and this same approval contract.

## Testing

Acceptance requires:

- Unit tests for workflow routing, summaries, approval levels, approval records, secret redaction, and Xiaolongxia isolation.
- CLI smoke test for `venus agent-run`.
- Feishu dry-run test for `/venus agent-run`.
- Full `pytest -v` pass.
- A CLI smoke command over `data/samples/agent_run.json`.
