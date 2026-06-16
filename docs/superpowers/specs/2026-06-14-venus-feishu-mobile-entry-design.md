# Venus Feishu Mobile Entry Design

Date: 2026-06-14

## 1. Purpose

This phase adds the first Feishu-facing entry layer for Venus without connecting to live Feishu APIs yet. The goal is to make Venus ready for a dedicated mobile control surface while protecting the existing Xiaolongxia Feishu agent from shared identity, shared files, shared secrets, or command collisions.

The first slice is a safe adapter layer: it accepts Feishu-like message payloads from local samples, parses Venus commands, routes allowed requests to the existing local orchestrator, returns Feishu-card-ready response drafts, and logs approval-gated external actions without sending them.

## 2. Scope

### In Scope

- A Venus-only Feishu namespace using `VENUS_FEISHU_` environment variables.
- A local Feishu entry adapter that accepts deterministic JSON payloads.
- Message normalization into a small internal command object.
- Command parsing for the first mobile workflows:
  - `help`
  - `status`
  - `hotspot`
  - `product`
  - `comments`
  - `approve`
- Routing `hotspot`, `product`, and `comments` commands into the existing Venus orchestrator.
- Feishu-card-ready response drafts for reports, errors, and approval requests.
- Explicit side-effect controls so the first version never sends Feishu messages, replies to Douyin comments, publishes content, routes leads, or spends money.
- Tests proving Venus and Xiaolongxia remain isolated.

### Out Of Scope

- Live Feishu event callback server.
- Live Feishu message sending.
- Feishu app secret validation, request signature verification, or token refresh.
- Public Douyin replies, publishing, livestream actions, WeChat actions, Enterprise WeChat actions, Qianchuan actions, or Xingtu actions.
- Multi-user permission management beyond local sender allow-list metadata.

## 3. Architecture

The Feishu entry layer sits outside the existing Venus domain cores.

```text
Feishu-like JSON payload
        |
        v
FeishuEntryAdapter
        |
        v
FeishuCommandParser
        |
        v
VenusOrchestrator
        |
        v
FeishuResponseRenderer
        |
        v
Feishu card draft + audit metadata
```

The adapter must not contain product research, trend scoring, persona logic, or comment analysis. It only translates mobile messages into existing Venus workflows and translates workflow results back into response drafts.

## 4. Components

### 4.1 FeishuConfig

`FeishuConfig` describes local Feishu settings without storing secrets in code:

- `env_prefix`: must be `VENUS_FEISHU_`.
- `agent_name`: defaults to `venus`.
- `command_prefix`: defaults to `/venus`.
- `dry_run`: defaults to `true`.
- `allowed_sender_ids`: optional list for future access control.
- `storage_namespace`: must resolve under Venus storage, not Xiaolongxia storage.

The config loader should reject keys or paths that contain Xiaolongxia naming, and it should never read variables with a Xiaolongxia prefix.

### 4.2 FeishuMessage

`FeishuMessage` is the normalized inbound object:

- `message_id`
- `chat_id`
- `sender_id`
- `text`
- `timestamp`
- `raw_payload`

The local implementation accepts a small JSON shape that resembles Feishu message events but remains intentionally provider-neutral enough for tests.

### 4.3 FeishuCommand

`FeishuCommand` captures intent:

- `name`: one of `help`, `status`, `hotspot`, `product`, `comments`, `approve`.
- `args`: command-specific text or key-value pairs.
- `requires_approval`: boolean.
- `approval_level`: integer matching Venus approval levels.
- `source_message_id`: inbound message id.

Unknown or unsupported commands should return a help-style error draft instead of raising an uncaught exception.

### 4.4 FeishuEntryAdapter

The adapter validates isolation, normalizes the payload, parses the command, calls the orchestrator for allowed workflows, and returns a response draft.

Rules:

- `help` returns available commands.
- `status` returns local Venus status: dry-run mode, agent namespace, and approval policy.
- `hotspot` routes to the existing hotspot workflow using the configured sample file unless an explicit local path is provided.
- `product` routes to product research using the configured sample file unless an explicit local path is provided.
- `comments` routes to comment analysis using the configured sample file unless an explicit local path is provided.
- `approve` only creates or updates local approval intent metadata in this phase; it must not execute an external action.

### 4.5 FeishuResponseRenderer

The renderer returns card-ready dictionaries rather than live Feishu API calls. Response types:

- `report`: summary, highlights, next recommended action.
- `approval_request`: action summary, approval level, risk notes, and a local approval id.
- `error`: safe explanation and suggested command.
- `status`: environment and dry-run facts without secrets.

Every response must include `external_actions: []` in this phase.

## 5. Data Flow

1. A local JSON message enters `venus feishu <path>`.
2. The adapter validates that the runtime config uses Venus-only names.
3. The message is normalized into `FeishuMessage`.
4. The parser extracts `/venus <command> ...`.
5. The adapter maps the command to a safe workflow.
6. The existing orchestrator generates the domain result.
7. The renderer wraps the result as a Feishu card draft.
8. The adapter returns structured JSON with:
   - `workflow: "feishu"`
   - `command`
   - `dry_run: true`
   - `card`
   - `approval_records`
   - `external_actions: []`

## 6. Safety And Approval Policy

The first Feishu entry slice is dry-run only.

- Private report drafts are allowed.
- External Feishu sends are not allowed.
- Public replies are not allowed.
- Publishing is not allowed.
- Lead routing is not allowed.
- Ad spend or Qianchuan changes are not allowed.
- `approve` records intent but cannot trigger external side effects.
- Any future live sender must consume the same card draft and pass a separate approval gate.

The adapter should redact common secret-looking fields from status or error output: `secret`, `token`, `password`, `app_secret`, and `authorization`.

## 7. Isolation Requirements

Venus must stay independent from Xiaolongxia:

- Feishu environment variables must begin with `VENUS_FEISHU_`.
- Command prefix must be `/venus`.
- Storage must remain under `data/venus` and `logs/venus`.
- Config loaders must reject Xiaolongxia names, paths, or prefixes.
- Sample payloads must not mention Xiaolongxia.
- Tests must verify the guard rejects a Xiaolongxia namespace.

## 8. Error Handling

The adapter should return structured error drafts for:

- Missing payload file.
- Invalid JSON.
- Missing text field.
- Message not starting with `/venus`.
- Unknown command.
- Missing local sample path for a workflow.
- Isolation violation.
- Orchestrator workflow failure.

Errors must be safe to show in Feishu and must not expose secrets or raw stack traces.

## 9. Testing

The implementation plan should use TDD and cover:

- Config defaults use `VENUS_FEISHU_`, `/venus`, and dry-run mode.
- Xiaolongxia config names are rejected.
- A `/venus help` payload returns a help card draft.
- A `/venus hotspot` payload routes through the existing hotspot workflow.
- A `/venus product` payload routes through product research.
- A `/venus comments` payload routes through comment analysis and keeps reply drafts approval-gated.
- A `/venus approve ...` payload records approval intent but returns no external actions.
- Unknown commands return structured help errors.
- The CLI command `venus feishu data/samples/feishu_message.json` returns JSON.

## 10. Acceptance Criteria

Phase 7 is complete when:

- The code exposes a local Feishu entry workflow through the CLI.
- All Feishu entry outputs are dry-run response drafts with no external actions.
- Existing MVP tests still pass.
- New tests prove command parsing, workflow routing, approval gating, error handling, and Venus/Xiaolongxia isolation.
- The README explains how to run the Feishu local smoke command.

