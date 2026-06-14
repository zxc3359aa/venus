# Venus Versioned Memory Design

Date: 2026-06-14

## Purpose

This slice adds a local versioned memory contract for Venus. It helps Venus learn the user's skincare philosophy, product judgment, speaking style, content preferences, and safety boundaries without automatically changing long-term memory.

It supports the user's goal for Venus to become a stronger version of the user while preserving privacy, isolation from Xiaolongxia, manual approval, and rollback readiness.

## Data Source

The first input shape is `data/samples/memory.json`.

It may contain:

- `current_memory` with version, principles, style phrases, product beliefs, content rules, banned claims, and privacy boundaries.
- `learning_candidates` from feedback, content edits, product reviews, comment replies, or self-improvement reports.
- `approval_decisions` indicating which candidate IDs are approved, rejected, or still pending.
- `backup` metadata for the last local snapshot.
- `source` and `retrieved_at` metadata.

The source is labeled as manual or local export. It must not contain live account credentials, direct customer contact details, payment details, or unrelated Xiaolongxia memory.

## Output

`build_memory_report(payload)` returns:

- `workflow: memory`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for current version, candidates, approved candidates, rejected candidates, pending candidates, proposed version, proposed change count, blocked sensitive candidate count, backup status, and approval-gated actions.
- `candidate_reviews` with category, proposed rule, decision, risk, privacy flags, evidence IDs, and execution state.
- `memory_diff` showing additions by memory section without overwriting current memory.
- `proposed_memory` with the next version and merged approved rules.
- `rollback_plan` pointing back to the prior version.
- `backup_tasks` when backup verification is missing.
- `approval_records` for memory merge and backup verification.
- `external_actions: []`.

The CLI supports:

```bash
venus memory data/samples/memory.json
```

The Feishu dry-run adapter supports:

```text
/venus memory
```

Agent Run also summarizes memory when the payload includes `memory`.

## Approval Boundaries

- Approved candidates are only staged into `proposed_memory`; they are not written to persistent memory in this dry-run slice.
- Memory merge requires manual approval because it changes how Venus speaks and decides.
- Sensitive or personal candidates are blocked and excluded from the merge proposal.
- Backup verification is approval-gated before any future memory write or restore.
- No system prompt, persona file, JSON store, backup target, Feishu message, or external platform state is changed.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like keys and sensitive personal fields are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live memory writes must add audit logs, immutable snapshots, rollback commands, approval IDs, and privacy scanning before any side effect.

## Testing

Acceptance requires:

- Unit tests for candidate review, decision handling, proposed memory merge, blocked sensitive candidates, rollback plan, backup tasks, approval records, redaction, and isolation.
- CLI smoke test for `venus memory`.
- Feishu dry-run test for `/venus memory`.
- Agent Run test proving memory summaries are included in the operating cycle.
- Full `pytest -v` pass.
