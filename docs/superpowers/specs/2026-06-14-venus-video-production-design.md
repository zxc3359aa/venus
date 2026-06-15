# Venus Video Production Design

Date: 2026-06-14

## Purpose

This slice adds the first structured video-production contract for Venus. It turns a beauty/skincare topic and content brief into a short-video package that includes script copy, shot list, editing timeline, subtitle cards, asset checklist, and publishing draft.

It supports the user's requirement that Venus has professional copywriting and video-editing capabilities, while keeping actual rendering, uploading, and publishing disabled until real media tools and platform permissions are connected.

## Data Source

The first input shape is `data/samples/video_production.json`.

It may contain:

- Topic, format, objective, duration, and retrieval metadata.
- Persona samples for the user's speaking style.
- Key points for the content structure.
- Risk notes for claim boundaries.
- B-roll or evidence assets that should appear in the cut.

The source is labeled as manual or local content-brief data. It must not claim to be a live剪映, CapCut, Douyin, or cloud-rendering project.

## Output

`build_video_production_package(payload)` returns:

- `workflow: production`.
- Venus namespace and dry-run status.
- Source metadata and freshness notes.
- Summary metrics for duration, scenes, subtitles, B-roll assets, title options, and approval-gated actions.
- `script_package` with hook, opening, body segments, CTA, comment prompt, and title options.
- `shot_list` with scene timing, visual direction, spoken line, overlay text, B-roll asset, and retention goal.
- `edit_plan` with 9:16 timeline instructions, cuts, transitions, subtitles, sound notes, and export notes.
- `subtitle_cards` optimized for fast Douyin viewing.
- `asset_checklist` for B-roll/evidence review.
- `publish_package` with cover text, title options, caption, hashtags, and pinned-comment draft.
- `approval_records` for claim review and publish review.
- `external_actions: []`.

The CLI supports:

```bash
venus production data/samples/video_production.json
```

The Feishu dry-run adapter supports:

```text
/venus production
```

Agent Run also summarizes video production when the payload includes `video_production`.

## Approval Boundaries

- Claim-sensitive wording requires level 2 review.
- Publishing, final cover/caption/hashtags, and pinned comment require level 3 review.
- Drafting scripts, shot lists, and edit instructions is level 1 internal work.
- No video file, local editor project, cloud render, Douyin upload, publish schedule, or pinned comment is created.

## Safety

- Config must use a Venus namespace and reject Xiaolongxia references.
- Dry-run mode is required.
- Secret-like fields are redacted from outputs.
- Outputs keep `external_actions: []`.
- Future live editing must add source-file checks, media rights review, export logs, checksum tracking, rollback, and explicit publish approval.

## Testing

Acceptance requires:

- Unit tests for script package, shot list, edit plan, subtitles, publishing package, approvals, redaction, and isolation.
- CLI smoke test for `venus production`.
- Feishu dry-run test for `/venus production`.
- Agent Run test proving production summaries are included in the operating cycle.
- Full `pytest -v` pass.
