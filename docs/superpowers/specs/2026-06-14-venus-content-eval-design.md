# Venus Content Eval Design

Date: 2026-06-14

## Purpose

This slice adds a local dry-run content evaluation workflow for Venus. It checks whether a short-video script and editing package is strong enough to move toward the user's Douyin growth goals before any rendering, posting, ad spend, or public reply happens.

The evaluation is a publishing gate, not a generator. It reviews the content package for predicted retention, interaction, comment intent, follow intent, persona fit, evidence clarity, and skincare claim safety. It produces revision tasks and approval records so Venus can keep improving content quality without overclaiming medical or skincare effects.

## KPI Frame

Because there is not yet a connected source of truth for live Douyin video performance, the first version uses deterministic structural scoring. The scores are directional, explainable, and intended for pre-publish review only. Future live analytics can calibrate weights against real completion rate, comment rate, follow rate, share rate, click-through, conversion, and negative feedback.

Primary local KPIs:

- `retention_score`: strength of the first three seconds, pacing, scene structure, and tension.
- `interaction_score`: whether the script gives viewers a concrete reason to answer, save, or ask for a follow-up.
- `comment_score`: whether the prompt asks for specific skin state, product, frequency, or controversy input.
- `follow_score`: whether the video creates a credible reason to follow for future product breakdowns.
- `persona_score`: whether the language matches the user's evidence-first, conversational skincare style.
- `safety_score`: whether claims avoid absolute promises, unsupported treatment language, and missing evidence framing.

Guardrails:

- Claim safety can block publishing even when growth scores are strong.
- Evidence gaps become revision tasks.
- Raw tokens, customer identifiers, and Xiaolongxia references must not appear in outputs.
- All platform actions remain disabled and `external_actions: []` is preserved.

## Input

The first sample input is `data/samples/content_eval.json`.

It may contain:

- `source`, `evaluated_at`, `topic`, `objective`, and `live_publish_requested`.
- `persona_samples` for style checks.
- `script_package` with hook, opening, body segments, CTA, comment prompt, and title options.
- `shot_list`, `edit_plan`, `subtitle_cards`, and `publish_package` from the production workflow.
- `evidence_ids`, `risk_notes`, `forbidden_claims`, and optional benchmark targets.

The workflow also supports Agent Run input under `content_eval`.

## Output

`build_content_eval_report(payload)` returns:

- `workflow: content_eval`.
- Venus namespace, dry-run status, approval mode, source metadata, and summary.
- `scorecard` for the six KPI dimensions.
- `publish_readiness` with status, blocking reasons, and manual review level.
- `revision_queue` sorted by priority.
- `kpi_definitions` documenting every local metric and guardrail.
- `approval_records` for content revision and publish review when needed.
- `external_actions: []`.

The CLI supports:

```bash
venus content-eval data/samples/content_eval.json
```

The Feishu dry-run adapter supports:

```text
/venus content-eval
```

Agent Run summarizes content readiness when the payload includes `content_eval`.

## Approval Boundaries

- `publish_readiness.status == blocked_by_claim_risk` blocks publishing until claim language is revised.
- `publish_readiness.status == needs_revision` blocks publishing until high-priority revision tasks are reviewed.
- Any live publish request creates an approval record, but no publishing action is executed.
- Final export, upload, pinned comment, paid traffic, or brand-deliverable submission remain out of scope.

## Testing

Acceptance requires:

- Unit tests for scorecard generation, revision task creation, claim-risk blocking, approval records, redaction, and Xiaolongxia isolation.
- CLI smoke test for `venus content-eval`.
- Feishu dry-run test for `/venus content-eval`.
- Agent Run test proving content-eval summaries are included in the operating cycle.
- Full `pytest -v` pass.
