# Venus Task Plan

## Goal

Build "Venus", a beauty and skincare agent system that helps the user's Douyin skincare account grow toward top-creator status while preserving privacy, data isolation, and long-term self-improvement.

## Current Phase

Phase 7 is next: the first local Venus MVP is implemented and verified. The first practical Venus version includes all three MVP centers: content/trend intelligence, product research, and persona/style learning.

## Phases

| Phase | Status | Purpose | Exit Criteria |
|---|---|---|---|
| 1. Product and system design | Complete | Clarify scope, module boundaries, data flow, safety limits, and MVP sequence. | User approved the written design spec. |
| 2. Implementation plan | Complete | Break the approved design into executable milestones, files, services, connectors, and tests. | Implementation plan saved and reviewed. |
| 3. Local project scaffold | Complete | Create the repo structure, environment templates, docs, and first runnable agent skeleton. | Local smoke commands run. |
| 4. Knowledge and memory layer | Complete | Define Venus memory, style profile, skincare philosophy, content library, product database, and privacy controls. | Local persona and storage tests pass. |
| 5. Trend and research pipeline | Complete | Build source collection, normalization, scoring, reports, and script ideation for Douyin beauty/skincare topics. | Sample report and script pack generated from test inputs. |
| 6. Content creation workflow | Complete | Produce short-video scripts, shot lists, editing briefs, and review gates in the user's voice. | End-to-end content brief can be generated and reviewed. |
| 7. Feishu mobile entry | Pending | Add a Feishu interface isolated from the existing "Xiaolongxia" agent. | Venus receives and responds through separate Feishu identity/config/files. |
| 8. Analytics and monitoring | Pending | Add dashboards for competitors, videos, comments, product risk, content performance, and growth loops. | Monitoring reports can be refreshed and inspected. |
| 9. Platform integrations | Pending | Add Douyin comments, livestream, e-commerce, Qianchuan, Xingtu, WeChat mini-program, and enterprise WeChat flows as approved connectors. | Each connector has permissions, logs, and rollback controls. |
| 10. Self-improvement and backup | Pending | Add evals, feedback loops, audit logs, safe learning, backups, and recovery. | Recurring improvement and backup checks are verified. |

## Non-Negotiables

- Venus and the existing "Xiaolongxia" Feishu agent must stay independent: separate identity, config, data, logs, files, and permissions.
- Personal privacy, account credentials, API keys, customer data, and unpublished strategy must never be exposed or committed.
- Automation that replies publicly, spends ad budget, contacts users, or changes platform state needs approval gates until explicitly relaxed.
- Medical/skincare claims need evidence, risk language, and compliance review instead of overconfident promises.
- The project must start with a narrow MVP, then expand through connectors and verified workflows.

## Immediate Next Steps

1. Choose the next integration slice: Feishu mobile entry, Airtable sync, Douyin comment connector, or richer OpenAI Agents SDK orchestration.
2. Write a focused follow-up plan for the chosen slice.
3. Implement the chosen slice with tests and approval gates.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| None yet | N/A | N/A |
