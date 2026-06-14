# Venus Dashboard Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local static HTML dashboard generator for Venus operating data.

**Architecture:** Create `src/venus/dashboard.py` to compose the existing Airtable-ready package into a dashboard summary and single-file HTML. Add a CLI path that can either print JSON status or write the HTML to a requested output file.

**Tech Stack:** Python standard library, HTML escaping, existing Venus analytics functions, pytest, local sample JSON.

---

## File Structure

- Create `src/venus/dashboard.py`.
- Create `tests/test_dashboard.py`.
- Modify `src/venus/cli.py` for optional dashboard output path.
- Modify `tests/test_cli_smoke.py`.
- Update `README.md`, `task_plan.md`, and `progress.md`.

## Tasks

### Task 1: Dashboard Unit Tests

- [x] Add `tests/test_dashboard.py`.
- [x] Assert `build_dashboard_html()` returns complete HTML, summary metrics, and `external_actions: []`.
- [x] Assert sections for Hotspots, Products, Comments, Competitors, Monitoring Opportunities, and Approvals exist.
- [x] Assert user-provided text is HTML-escaped.
- [x] Run `pytest tests/test_dashboard.py -v` and confirm failure because `venus.dashboard` does not exist.

### Task 2: Dashboard Implementation

- [x] Create `src/venus/dashboard.py`.
- [x] Implement `build_dashboard_html(payload)`.
- [x] Reuse `build_airtable_sync_package()` to keep dashboard numbers reconciled with the export package.
- [x] Add compact inline CSS and visual bar components.
- [x] Run `pytest tests/test_dashboard.py -v` and confirm it passes.

### Task 3: CLI Output File Support

- [x] Extend CLI to accept an optional output path only for `dashboard`.
- [x] Add `dashboard` to workflow choices.
- [x] Write dashboard HTML to the requested path and print JSON status with path, summary, and `external_actions: []`.
- [x] Add CLI smoke test that writes to a temporary file.
- [x] Run targeted CLI tests and confirm they pass.

### Task 4: Docs And Verification

- [x] Update README smoke commands.
- [x] Update `task_plan.md` and `progress.md`.
- [x] Run `pytest -v`.
- [x] Run `python3 -m venus.cli dashboard data/samples/airtable_export.json reports/venus-dashboard.html`.
- [x] Inspect the generated HTML file for expected title and sections.
- [x] Run `git diff --check`.
- [ ] Commit and push the changes.
