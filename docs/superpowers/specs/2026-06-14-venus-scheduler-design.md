# Venus Scheduler Design

Date: 2026-06-14

## Purpose

This slice adds a local dry-run scheduler contract for Venus. It turns the system from a set of independent workflows into a 24-hour operating plan by deciding which local jobs are due, which jobs are blocked by connector or permission state, and which jobs require manual approval before any future automation.

It supports the user's goal for Venus to run all-day Douyin trend scanning, comment review, ecommerce checks, competitor monitoring, backup verification, memory review, and Feishu mobile reporting while preserving privacy and side-effect controls.

## Data Source

The first input shape is `data/samples/scheduler.json`.

It may contain:

- `generated_at` and `timezone`.
- `live_scheduler_requested` for future always-on scheduler enablement review.
- `jobs` with job ID, workflow, cadence, priority, last run time, connector state, approval level, and evidence IDs.
- `blackout_windows` for windows where public-facing jobs should be paused.
- `operator_channels` for private status surfaces such as Feishu.

The source is labeled as manual or local export. It must not contain live platform credentials or customer contact data.

## Output

`build_scheduler_plan(payload)` returns:

- `workflow: scheduler`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for jobs, due jobs, blocked jobs, paused jobs, approval-gated jobs, high-priority jobs, backup jobs, and approval records.
- `run_queue` containing due local jobs that are ready or approval-gated.
- `blocked_jobs` for jobs blocked by connector, permission, or health state.
- `next_runs` for jobs not yet due.
- `blackout_windows` copied into the report for review.
- `operator_digest` describing what should be sent to private Feishu once live sending is approved.
- `approval_records` for live scheduler enablement and approval-gated due jobs.
- `external_actions: []`.

The CLI supports:

```bash
venus scheduler data/samples/scheduler.json
```

The Feishu dry-run adapter supports:

```text
/venus scheduler
```

Agent Run also summarizes scheduler state when the payload includes `scheduler`.

## Approval Boundaries

- Live scheduler enablement requires manual approval.
- Any due job with approval level 2 or higher is only queued as `blocked_until_approved`.
- Jobs blocked by missing permissions, unhealthy connectors, or blackout windows are not placed into the executable queue.
- No timer, cron job, Feishu message, platform read, platform write, ad spend, reply, memory write, backup write, or external call is executed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like keys are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live scheduler usage must add run locks, audit logs, retry limits, rate limits, approval IDs, credential checks, rollback notes, and operator alert routing before any side effect.

## Testing

Acceptance requires:

- Unit tests for due-job selection, blocked connector handling, approval-gated jobs, blackout windows, operator digest, approval records, redaction, and isolation.
- CLI smoke test for `venus scheduler`.
- Feishu dry-run test for `/venus scheduler`.
- Agent Run test proving scheduler summaries are included in the operating cycle.
- Full `pytest -v` pass.
