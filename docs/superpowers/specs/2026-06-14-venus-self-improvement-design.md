# Venus Self-Improvement Design

Date: 2026-06-14

## Purpose

This slice adds the first safe self-improvement contract for Venus. It turns local feedback, defect reports, and backup checks into reviewable tasks so Venus can gradually learn the user's expression style, repair workflow gaps, and protect data without silently changing behavior.

It supports the user's requirement that Venus becomes a stronger version of the user over time while preserving privacy, data isolation, and manual control over any durable memory or system change.

## Data Source

The first input shape is `data/samples/self_improvement.json`.

It may contain:

- Feedback events showing original draft, final user-approved wording, reason for edits, and performance metrics.
- Defect reports describing missing guardrails, workflow gaps, severity, and expected behavior.
- Backup checks describing target, schedule, latest backup time, latest verification time, and status.
- Source and retrieval metadata.

The source is labeled as manual or local learning data. It must not claim to be live Douyin, Feishu, WeChat, Qianchuan, Xingtu, or storage-provider telemetry.

## Output

`build_self_improvement_report(payload)` returns:

- `workflow: improvement`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for feedback events, learning candidates, defects, high-severity defects, backup checks, backup issues, and approval-gated actions.
- `learning_candidates` that propose persona, claim-safety, or operating-preference rules.
- `regression_checks` that convert defects into pending guardrail checks.
- `backup_tasks` that request verification for stale or unverified backups.
- `approval_records` for every learning, guardrail, and backup action.
- `external_actions: []`.

The CLI supports:

```bash
venus improvement data/samples/self_improvement.json
```

The Feishu dry-run adapter supports:

```text
/venus improvement
```

Agent Run also summarizes self-improvement when the payload includes `self_improvement`.

## Approval Boundaries

- Learning candidates are level 2 and do not update long-term memory automatically.
- High-severity regression guardrails are level 3; other regression guardrails are level 2.
- Backup verification tasks are level 2 and do not restore, copy, delete, or upload files in this slice.
- No system prompt, persona memory, code, backup target, platform account, or external service is changed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like fields are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live self-improvement must add eval suites, approval history, rollback plans, versioned memory, backup integrity checks, and restore drills before any side effect.

## Testing

Acceptance requires:

- Unit tests for learning candidates, regression checks, backup tasks, approval records, redaction, and isolation.
- CLI smoke test for `venus improvement`.
- Feishu dry-run test for `/venus improvement`.
- Agent Run test proving self-improvement summaries are included in the operating cycle.
- Full `pytest -v` pass.
