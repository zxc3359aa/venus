# Venus Task Plan

## Goal

Build "Venus", a beauty and skincare agent system that helps the user's Douyin skincare account grow toward top-creator status while preserving privacy, data isolation, and long-term self-improvement.

## Current Phase

Phase 8/9 bridge is in progress: the first local Venus MVP, dry-run Feishu mobile entry, competitor monitoring workflow, Airtable-ready operations export, static operations dashboard, local Agent Run orchestration layer, and dry-run Douyin engagement connector are implemented before live Douyin, Qianchuan, Xingtu, BI, or Airtable writes are enabled.

## Phases

| Phase | Status | Purpose | Exit Criteria |
|---|---|---|---|
| 1. Product and system design | Complete | Clarify scope, module boundaries, data flow, safety limits, and MVP sequence. | User approved the written design spec. |
| 2. Implementation plan | Complete | Break the approved design into executable milestones, files, services, connectors, and tests. | Implementation plan saved and reviewed. |
| 3. Local project scaffold | Complete | Create the repo structure, environment templates, docs, and first runnable agent skeleton. | Local smoke commands run. |
| 4. Knowledge and memory layer | Complete | Define Venus memory, style profile, skincare philosophy, content library, product database, and privacy controls. | Local persona and storage tests pass. |
| 5. Trend and research pipeline | Complete | Build source collection, normalization, scoring, reports, and script ideation for Douyin beauty/skincare topics. | Sample report and script pack generated from test inputs. |
| 6. Content creation workflow | Complete | Produce short-video scripts, shot lists, editing briefs, and review gates in the user's voice. | End-to-end content brief can be generated and reviewed. |
| 7. Feishu mobile entry | Complete | Add a Feishu interface isolated from the existing "Xiaolongxia" agent. | Local dry-run Feishu entry parses `/venus` commands, routes safe workflows, and returns card-ready drafts with no external actions. |
| 8. Analytics and monitoring | In Progress | Add dashboards for competitors, videos, comments, product risk, content performance, and growth loops. | Monitoring reports can be refreshed and inspected. |
| 9. Platform integrations | In Progress | Add Douyin comments, livestream, e-commerce, Qianchuan, Xingtu, WeChat mini-program, and enterprise WeChat flows as approved connectors. | Each connector has permissions, logs, and rollback controls. |
| 10. Self-improvement and backup | Pending | Add evals, feedback loops, audit logs, safe learning, backups, and recovery. | Recurring improvement and backup checks are verified. |

## Non-Negotiables

- Venus and the existing "Xiaolongxia" Feishu agent must stay independent: separate identity, config, data, logs, files, and permissions.
- Personal privacy, account credentials, API keys, customer data, and unpublished strategy must never be exposed or committed.
- Automation that replies publicly, spends ad budget, contacts users, or changes platform state needs approval gates until explicitly relaxed.
- Medical/skincare claims need evidence, risk language, and compliance review instead of overconfident promises.
- The project must start with a narrow MVP, then expand through connectors and verified workflows.

## Immediate Next Steps

1. Decide whether the next slice should be real Airtable write connector, live Douyin permission adapter, OpenAI Agents SDK runner/evals, or WeChat private-domain skeleton.
2. Keep external actions disabled until permissions, logs, and approval gates are verified.
3. Preserve Venus/Xiaolongxia isolation in every connector and mobile command.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| None yet | N/A | N/A |
