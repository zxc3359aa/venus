# Venus Airtable Export Design

Date: 2026-06-14

## Purpose

This slice adds an Airtable-ready operations export for Venus. The goal is to make Venus outputs human-reviewable in structured operating tables before any live Airtable write, Douyin action, ad spend, or private-domain routing is enabled.

The workflow is local and dry-run only. It creates a JSON package containing base metadata, table schemas, view suggestions, and records derived from imported Venus sample data.

## Operating Need

Venus needs a human-editable operations layer for:

- Daily hotspot review.
- Product research cards.
- Comment triage and reply approval.
- Competitor monitoring and opportunity review.
- Approval records and future action gates.

Airtable is a good future surface for these because it has bases, tables, fields, records, views, automations, and interfaces. This slice prepares the data contract without requiring an Airtable personal access token.

## Scope

Included:

- A local `airtable` workflow.
- A `build_airtable_sync_package(payload)` function.
- Tables for `Hotspots`, `Products`, `Comments`, `Competitors`, `Monitoring Opportunities`, and `Approvals`.
- Airtable-style field definitions and record field dictionaries.
- CLI smoke command: `venus airtable data/samples/airtable_export.json`.
- Feishu dry-run command: `/venus airtable`.
- `external_actions: []` for every output.

Excluded:

- Creating Airtable bases or tables.
- Writing records to Airtable.
- Reading real Airtable data.
- Storing Airtable tokens.
- Triggering automations.

## Data Contract

Input JSON:

- `hotspots`: list matching the local hotspot sample.
- `products`: list matching the local product sample.
- `comments`: list matching the local comment sample.
- `competitors`: either a competitor payload with `competitors`, or a list of competitors.
- `approvals`: optional list of local approval records.

Output JSON:

- `dry_run: true`
- `external_actions: []`
- `base`: Airtable base metadata with Venus namespace.
- `tables`: list of table packages with fields, view suggestions, and records.
- `summary`: table count, record count, and included table names.
- `sync_boundary`: clear statement that this package is import-ready but not written to Airtable.

## Isolation And Safety

- All base and namespace labels must use Venus naming.
- The export must reject Xiaolongxia namespaces.
- The package must not include secrets, tokens, passwords, or authorization values.
- The export must keep public replies, publishing, lead routing, and ad changes outside the automatic action surface.

## Testing

Acceptance requires:

- Unit tests for schema, record mapping, dry-run boundary, and Xiaolongxia rejection.
- Orchestrator test for the `airtable` workflow.
- CLI smoke test for `venus airtable data/samples/airtable_export.json`.
- Feishu dry-run test for `/venus airtable`.
- Full `pytest -v` pass.
