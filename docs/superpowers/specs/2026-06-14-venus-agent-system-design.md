# Venus Agent System Design

Date: 2026-06-14

## 1. Purpose

Venus is a beauty and skincare agent system for helping the user's Douyin skincare account grow toward top-creator status. It must combine trend intelligence, professional product research, persona learning, content generation, competitor monitoring, future platform integrations, privacy protection, and self-improvement.

The user approved a "three-core, one-foundation" direction:

- Content intelligence core
- Product research core
- Persona learning core
- Shared evidence, memory, approval, audit, and backup foundation

This design intentionally starts with a controlled MVP that automates analysis, research, and drafts before it automates public replies, publishing, ad spend, private-domain routing, or other account-changing actions.

## 2. Product Principles

Venus should feel powerful, but not reckless.

- It should help the user move faster without losing judgment, taste, or trust.
- It should learn the user's skincare philosophy, product standards, spoken style, and creator persona over time.
- It should prefer evidence-backed recommendations over empty trend chasing.
- It should never expose private user data, account credentials, unpublished strategy, user/customer data, or platform tokens.
- It should keep Venus separate from the existing Feishu agent "Xiaolongxia".
- It should treat public replies, publishing, ad spend, customer routing, and medical-like skincare claims as approval-gated actions.

## 3. Scope

### Phase 1 Scope

Phase 1 builds the first useful Venus operating loop without assuming every external account permission already exists.

It must support:

- Beauty/skincare hotspot briefs from reviewed sources or manually imported samples.
- Professional trend analysis across topics, products, creators, comments, ingredients, tags, and controversies.
- Short-video output: hook, script, title, cover text, shot list, editing notes, interaction prompts, and call to action.
- Product research cards covering filing/registration, ingredients, claims, supplier/testing evidence, controversy, and safe talking points.
- Persona profile storage and application: skincare philosophy, product judgment, speaking style, expressions, banned claims, and examples.
- Comment analysis from imported or future permissioned data: intent, sentiment, risk, summary, and reply drafts.
- Competitor schema and sample analysis for accounts, videos, live behavior, ad intensity, style, and recommendations.
- Approval records and audit logs for decisions.
- Backup metadata and recovery expectations.

Phase 1 may use manual imports, sample data, screenshots, exported files, official pages, or connector-ready stubs while platform permissions are pending.

### Later Scope

Later phases add permissioned production integrations:

- Douyin comment retrieval, reply drafts, approved replies, pinned comments, publishing, and video performance data.
- Douyin e-commerce and live comment flows.
- Qianchuan and OceanEngine reporting, budget recommendations, audience analysis, creative diagnostics, and approved campaign changes.
- Xingtu task intake, brand-brief analysis, quote/acceptance guidance, and ad-script drafting.
- Feishu mobile command, report, approval, and alert surface.
- WeChat Mini Program skincare Q&A and customer-service flow.
- Enterprise WeChat private-domain lead routing and customer handoff.
- 24/7 competitor monitoring, dashboards, alerts, and recurring reports.
- Automatic learning summaries, evals, regression tests, and verified backups.

## 4. Architecture

Venus is a modular agent system with one orchestration layer and three domain cores.

### 4.1 Orchestrator

The orchestrator receives a task, identifies the workflow, gathers evidence, chooses the relevant core, enforces approval policy, writes logs, and returns a structured result.

Responsibilities:

- Route requests to content, product research, persona learning, or cross-core workflows.
- Require evidence bundles for claims and recommendations.
- Enforce approval levels before any external action.
- Keep all file paths, environment variables, logs, and data stores under Venus-specific namespaces.
- Produce outputs that can later be delivered through Feishu, dashboards, Airtable, or local reports.

### 4.2 Content Intelligence Core

Purpose: turn beauty/skincare market signals into usable content decisions.

Inputs:

- Hot topics, product mentions, creator activity, comments, ingredients, tags, controversies, and trend notes.
- Official platform API data when permissioned.
- Manual imports, screenshots, exports, public web pages, and curated source lists when API data is unavailable.

Outputs:

- Daily or on-demand hotspot brief.
- Trend score and controversy score.
- Content angle recommendation.
- Filming advice.
- Short-video script pack with multiple hooks and CTAs.
- Comment-bait and follow-bait suggestions that remain respectful and compliant.

### 4.3 Product Research Core

Purpose: help the user judge whether a product is safe, credible, content-worthy, and how it can be discussed without overclaiming.

Evidence categories:

- Filing or registration identity.
- Product category and claimed functions.
- Ingredient list and ingredient roles.
- Raw-material safety information where available.
- Supplier and test-report evidence where provided.
- Efficacy-claim evidence.
- Labeling and compliance risk.
- Public controversy, historical stains, creator criticism, consumer complaints, and official notices.

Outputs:

- Product research card.
- Evidence confidence and freshness.
- Product risk score.
- Talking-point boundaries.
- Claims that need human review.
- Suggested wording for content.
- Warning list for claims Venus should not make.

### 4.4 Persona Learning Core

Purpose: make Venus increasingly understand and imitate the user's approved creator style while preserving boundaries.

Memory objects:

- Skincare beliefs.
- Product evaluation standards.
- Tone and speaking rhythm.
- Preferred vocabulary.
- Phrases to avoid.
- Persona boundaries.
- Approved script samples.
- Rejected drafts and reasons.
- Performance learnings from published content.

Outputs:

- Updated persona profile.
- Style guidance for scripts and replies.
- Draft rewrites in the user's voice.
- Learning summaries after user approvals, edits, rejections, and performance reviews.

## 5. Shared Foundation

### 5.1 Evidence Store

Every important output must retain an evidence bundle:

- Source name and URL or local file reference.
- Source type: official API, regulator, platform docs, manual import, screenshot, public web, or user-provided note.
- Retrieval or import timestamp.
- Freshness.
- Confidence.
- Risk notes.
- Claims derived from the source.

Official platform APIs and government/regulatory sources rank highest. General web and social search can identify trends but must not be treated as final proof for product safety, legality, or efficacy.

### 5.2 Structured Data Layer

Venus can start with local files or a local database and later sync selected objects to Airtable if the user wants a human-editable operating table.

Candidate objects:

- `sources`
- `hotspots`
- `products`
- `ingredients`
- `creators`
- `comments`
- `scripts`
- `persona_profile`
- `approvals`
- `experiments`
- `backups`

Airtable is suitable for fast operations and manual review. A local database is suitable for tighter privacy and code-first control. The implementation plan will choose the first storage method based on available credentials and privacy preference.

### 5.3 Approval System

Approval levels:

- Level 0: safe internal analysis. No external side effects.
- Level 1: creator drafts such as scripts, titles, shot lists, product cards, and reply drafts.
- Level 2: private external communication such as Feishu reports or approved mini-program answers.
- Level 3: public platform actions such as Douyin replies, publishing, pinning comments, or user interactions.
- Level 4: money, reputation, or compliance risk, including ad budget changes, Qianchuan campaigns, Xingtu decisions, crisis replies, private-domain lead routing, and medical-like claims.

Phase 1 only performs Level 0 and Level 1 automatically. Levels 2-4 require explicit user approval until the user changes policy after logs and evals prove the workflow is safe.

### 5.4 Audit Logs

Venus must log:

- Input task.
- Sources used.
- Agent/core used.
- Output generated.
- Approval level.
- User decision.
- External action taken, if any.
- Follow-up learning.

Audit logs must not contain secrets or raw credentials.

### 5.5 Backups

Venus needs backup metadata from the beginning:

- Backup target.
- Backup schedule.
- Last backup timestamp.
- Last verification timestamp.
- Checksum or status where practical.
- Recovery note.

The backup workflow is part of the self-improvement foundation, not an afterthought.

## 6. Platform Integration Boundaries

### 6.1 Douyin

Known official directions:

- Comment management can retrieve comments, retrieve replies, reply to comments, and pin comments after permission approval.
- Content publishing supports video/image publishing and interaction data, with moderation and format constraints.
- User data such as fan count requires permission and user authorization, and some metrics update with delay.
- Xingtu creator hot-list data exists under permissioned APIs.

Phase 1 does not directly operate the Douyin account. It can analyze imported comments or reviewed source data and generate reply/publishing drafts.

### 6.2 OceanEngine, Qianchuan, and Xingtu

These are later permissioned integrations. Phase 1 may generate strategy, scripts, audience hypotheses, and budget recommendations, but it must not spend money or alter campaigns.

Any ad or commercial action requires:

- Account permission verification.
- Explicit budget limit.
- Approval log.
- Rollback or pause plan.
- Post-action report.

### 6.3 Feishu

Venus should eventually use a dedicated Feishu app as the mobile control surface.

Venus and Xiaolongxia isolation requirements:

- Separate app identity.
- Separate callback URL.
- Separate app secrets.
- Separate bot name.
- Separate command namespace.
- Separate environment variable prefix, such as `VENUS_`.
- Separate storage folder, logs, and data tables or database.
- No shared automation unless explicitly approved.

Custom bot webhooks are suitable for one-way notifications. A Feishu application bot is required for richer two-way commands, reports, and approval workflows.

### 6.4 WeChat Mini Program and Enterprise WeChat

WeChat Mini Program is a later skincare Q&A entry. It can support message push, customer-service messages, subscribe messages, and customer-service entry components, subject to platform rules and user/session constraints.

Enterprise WeChat is a later customer handoff and private-domain management surface. It can support customer detail, customer groups, application messages, and callbacks, subject to permissions and privacy policy.

Phase 1 only designs these flows; it does not automate customer communication.

## 7. Workflows

### 7.1 Hotspot To Script

1. Ingest hotspot notes or API data.
2. Normalize topics, products, creators, ingredients, comments, tags, and controversies.
3. Score each item by freshness, relevance, controversy, creator fit, evidence quality, and content potential.
4. Select top opportunities.
5. Generate professional analysis and filming angle.
6. Apply persona profile.
7. Produce script pack with hook, main body, turning point, CTA, title, cover text, and editing notes.
8. Attach evidence bundle and risk notes.

### 7.2 Product Research To Safe Talking Points

1. Receive product name, brand, filing number, ingredient list, links, screenshots, or source files.
2. Classify evidence by authority and freshness.
3. Build filing/registration, ingredient, claim, supplier/testing, controversy, and compliance sections.
4. Assign confidence and risk labels.
5. Generate safe talking points and forbidden claims.
6. Produce content-ready wording in the user's style.

### 7.3 Persona Learning

1. Ingest approved scripts, edits, rejected drafts, notes, and performance signals.
2. Extract durable style and judgment patterns.
3. Update the persona profile with clear examples and boundaries.
4. Use the profile in future scripts, replies, and brand-ad scripts.
5. Keep learning logs explainable so the user can correct Venus.

### 7.4 Comment Analysis

1. Import sample comments or retrieve permissioned comments later.
2. Classify each comment by intent, sentiment, topic, urgency, and risk.
3. Summarize comment themes.
4. Draft replies in the user's style.
5. Hold replies for approval before any public posting.

### 7.5 Competitor Monitoring

1. Maintain a watchlist of reference creators and competitors.
2. Track videos, themes, style, engagement patterns, ad content, live behavior, and product mentions.
3. Produce periodic strategy recommendations.
4. Feed learnings into content planning without copying another creator's protected expression.

## 8. Safety, Privacy, and Compliance

Venus must not:

- Commit or expose secrets, tokens, API keys, phone numbers, customer details, account credentials, or unpublished strategy.
- Make medical claims or guaranteed efficacy claims without suitable evidence and review.
- Present trend rumors as verified product safety facts.
- Reply publicly, publish content, route leads, or spend ad budget without the required approval level.
- Share Xiaolongxia data, files, logs, or secrets.

Venus should:

- Show uncertainty.
- Cite source types and timestamps.
- Flag risky claims.
- Prefer conservative language around skin conditions, irritation, allergy, medical treatment, and efficacy.
- Maintain logs and backups.

## 9. Error Handling

If a source is missing:

- Mark the section as missing evidence.
- Continue only where safe.
- Ask for a source or permission when the missing evidence controls the conclusion.

If an API permission is missing:

- Use manual import or sample data for Phase 1 workflows.
- Record the missing permission.
- Do not pretend the workflow is live or real-time.

If evidence conflicts:

- Show the conflict.
- Rank sources by authority.
- Avoid final claims until the conflict is resolved.

If an output exceeds approval level:

- Generate a draft only.
- Create an approval record.
- Wait for the user before taking external action.

## 10. Testing And Acceptance

The first implementation slice is accepted when Venus can pass these smoke tests:

- Given sample hotspot notes, Venus produces a ranked hotspot brief with evidence, risk tags, filming angle, and three script options.
- Given a product name and manually supplied source links, Venus produces a product research card with filing, ingredient, claim, controversy, safe talking points, and forbidden claims.
- Given three approved writing samples, Venus generates a script that follows the persona profile and flags uncertain claims.
- Given sample comments, Venus classifies intent, sentiment, and risk, then drafts approval-gated replies.
- Given an approval decision, Venus logs the decision and updates learning notes without exposing private data.
- Given Xiaolongxia exists separately in Feishu, Venus uses separate identifiers, files, environment variables, logs, and data paths.

## 11. Source Anchors For Implementation

Implementation should revisit the current official docs before building each connector because permissions, endpoints, and platform rules can change.

- Douyin comment management: `https://open.douyin.com/platform/resource/docs/ability/interaction-management/video-comment-management-solution`
- Douyin content publishing: `https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution`
- Douyin Xingtu creator hot list: `https://open.douyin.com/platform/resource/docs/openapi/data-open-service/star-data/star-tops/get-star-author-hot-list`
- Douyin user fan count: `https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-fans-count`
- Feishu receive message event: `https://open.feishu.cn/document/server-docs/im-v1/message/events/receive`
- Feishu send message: `https://open.feishu.cn/document/server-docs/im-v1/message/create`
- Feishu reply message: `https://open.feishu.cn/document/server-docs/im-v1/message/reply`
- Feishu custom bot: `https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot`
- WeChat Mini Program message push: `https://developers.weixin.qq.com/miniprogram/dev/framework/server-ability/message-push.html`
- WeChat Mini Program customer-service message: `https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/kf-mgnt/kf-message/sendCustomerMessage.html`
- WeChat Mini Program subscribe message: `https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-message-management/subscribe-message/sendMessage.html`
- Enterprise WeChat customer detail: `https://developer.work.weixin.qq.com/document/path/92114`
- Enterprise WeChat customer group list: `https://developer.work.weixin.qq.com/document/path/92120`
- Enterprise WeChat application message: `https://developer.work.weixin.qq.com/document/path/90236`
- Enterprise WeChat callback config: `https://developer.work.weixin.qq.com/document/path/90930`
- NMPA cosmetics data search: `https://www.nmpa.gov.cn/datasearch/home-index.html`
- NMPA domestic ordinary cosmetics filing lookup: `https://hzpba.nmpa.gov.cn/gccx/`
- NMPA cosmetics raw-material safety platform notice: `https://www.nmpa.gov.cn/directory/web/nmpa/yaowen/ypjgyw/hzhpyw/20211230165501124.html`
- NMPA efficacy claim evaluation rule: `https://www.nmpa.gov.cn/xxgk/fgwj/xzhgfxwj/20210409160321110.html`

## 12. Implementation Sequence

The implementation plan should be created after this written spec is reviewed.

Recommended sequence:

1. Create local repo scaffold, config templates, and secret hygiene rules.
2. Build core schemas and sample data fixtures.
3. Build a local command-line Venus prototype for the three Phase 1 workflows.
4. Add evidence bundle and approval log.
5. Add persona profile read/write.
6. Add sample report generation.
7. Add local smoke tests.
8. Add Feishu design and connector stubs, keeping Venus isolated from Xiaolongxia.
9. Add optional Airtable sync if credentials and structure are approved.
10. Add permissioned platform connectors one at a time.

## 13. Open Decisions For Implementation Planning

These decisions do not block the design, but the implementation plan should resolve them:

- Whether Phase 1 storage starts as local JSON/SQLite, Airtable, or both.
- Whether the first runnable interface is CLI, Feishu bot, local web dashboard, or Airtable-backed workflow.
- Which OpenAI model and API key setup will be used.
- Which sample data the user wants to use first: hotspot notes, product links, writing samples, competitor accounts, or comments.
- Whether the first Feishu integration is custom bot push-only or full application bot.

## 14. Success Definition

Venus is moving in the right direction when it can repeatedly turn skincare market signals and product evidence into useful, on-brand, approval-safe content decisions.

The full long-term goal is achieved only when Venus can run the broader operating system: trend monitoring, product research, persona learning, comment and live support, video and editing support, WeChat private domain, Qianchuan/Xingtu support, competitor monitoring, self-improvement, backup, privacy protection, and Feishu mobile access with Xiaolongxia isolation.
