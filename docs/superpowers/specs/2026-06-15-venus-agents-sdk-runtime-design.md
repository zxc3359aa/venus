# Venus Agents SDK Runtime Manifest Design

## Purpose

Venus has local workflows for trend intelligence, product research, content production, approvals, connector readiness, evals, and delivery ledgers. The next gap is an OpenAI Agents SDK-ready runtime contract that turns those workflows into a coherent agent application shape.

This slice adds a local `agents_sdk` workflow. It does not import `openai-agents`, read `OPENAI_API_KEY`, or call OpenAI. It creates a manifest-only runtime plan that a future SDK app can use after credentials, dependencies, eval gates, and approvals are ready.

Official OpenAI docs position the SDK path for server-owned orchestration, tool execution, state, and approvals. The local manifest follows that shape: one primary agent, deterministic local function-tool candidates, explicit guardrails, server-managed state, eval hooks, and deployment readiness checks.

## Scope

- Add a local `agents_sdk` workflow.
- Generate a primary Venus agent definition with instructions, model env var, output contract, and safety boundaries.
- Generate function-tool candidates for existing Venus workflows.
- Generate approval, state, eval, observability, and deployment readiness sections.
- Block live SDK execution until `OPENAI_API_KEY`, `openai-agents` dependency, passing eval readiness, and owner approval are present.
- Route through orchestrator, CLI, and dry-run Feishu.

Out of scope:

- Installing `openai-agents`.
- Calling OpenAI APIs.
- Starting an HTTP server.
- Deploying through Deployment Manager.
- Running hosted evals or trace graders.
- Enabling any live Douyin, Feishu, Airtable, WeChat, Qianchuan, Xingtu, ecommerce, memory, backup, or publishing action.

## Data Model

`AgentsSdkRuntimeConfig`:

- `namespace`: `venus_agents_sdk`
- `dry_run`: `True`
- `approval_mode`: `manual`
- `reviewer`: `owner`
- `sdk_mode`: `manifest_only`

Payload inputs:

- `live_sdk_requested`
- `environment`
- `agent_run`
- `eval_report`
- optional `tool_overrides`

Output sections:

- `agent_manifest`
- `tool_registry`
- `runtime_plan`
- `guardrails`
- `eval_hooks`
- `deployment_readiness`
- `approval_records`
- `safety_boundary`
- `external_actions: []`

## Readiness Rules

The manifest is `ready_for_sdk_build_review` only when all are true:

- `environment.OPENAI_API_KEY_configured` is true.
- `environment.openai_agents_installed` is true.
- `eval_report.summary.autopilot_ready` is true.
- no tool has `external_action_enabled: true`.
- any `live_sdk_requested` request is represented by a level-4 approval record instead of execution.

Otherwise the status is `blocked_by_sdk_readiness`.

## Feishu Behavior

`/venus agents-sdk` returns a dry-run card summary. It reads `data/samples/agents_sdk.json` by default and never sends a Feishu message.

## Testing

Tests cover:

- Manifest generation with agent definition, tools, guardrails, eval hooks, and deployment readiness blockers.
- Approval record creation for live SDK requests.
- Blocking externally-enabled tool overrides.
- Xiaolongxia isolation.
- CLI and Feishu routing.
