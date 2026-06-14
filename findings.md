# Venus Findings

## Workspace

- Current workspace: `/Users/christsang/Documents/维纳斯`.
- The workspace is a git repository with no visible project files yet.
- `git status --short` was clean before planning files were created.

## User Vision

Venus should become an all-in-one beauty and skincare operating system for a Douyin creator:

- monitor Douyin beauty/skincare hotspots, controversial topics, products, creators, comments, ingredients, tags, and trends;
- synthesize those signals into professional analysis, filming advice, and high-retention short-video scripts;
- research brands, filings, ingredient details, suppliers, testing reports, historical controversies, and product risk;
- learn the user's skincare philosophy, product judgment, speaking style, expression style, and persona;
- later connect to Douyin comments, livestream comments, e-commerce workflows, Qianchuan ads, Xingtu brand deals, WeChat mini-program, enterprise WeChat, and Feishu mobile;
- monitor competitor creators 24/7 and provide strategic recommendations;
- self-improve while protecting private data and backing up important information.

## Plugin and Capability Notes

- OpenAI Developers / Agents SDK is relevant for the future runnable agent architecture.
- Data Analytics is relevant for trend reports, competitor monitoring, KPI dashboards, and performance diagnostics. Its saved source context is currently missing, so future analytics will need explicit source setup.
- Product Design is relevant for future control panels, mini-program screens, and workflow UX. Its saved design context is currently missing.
- Airtable is a strong candidate for structured operating data: content ideas, products, ingredients, creators, competitors, comments, scripts, approvals, and performance logs.
- Atlassian Rovo is more relevant later for Jira/Confluence task management or internal knowledge search, not for the first empty-repo design pass.
- Browser and Computer Use may be needed later for inspecting local prototypes or operating logged-in web UIs when APIs are unavailable.
- Canva may be useful later for decks, campaign visuals, or brand/content assets, but it is not the first system backbone.

## Risks and Constraints

- Douyin, Qianchuan, Xingtu, WeChat, enterprise WeChat, Feishu, and e-commerce integrations depend on official APIs, permissions, accounts, compliance rules, and rate limits.
- Public replies, livestream responses, ad spend, private-domain lead capture, and medical/skincare claims are high-risk actions and should begin with human approval.
- "All automatic" should be staged: first automate analysis and drafts, then approved actions, then limited autonomous actions after logs and evals prove safety.
- Beauty/skincare content must distinguish evidence-backed claims from opinion, avoid illegal medical claims, and preserve trust.

## Official Platform Checks

- Douyin Open Platform documents a video comment management solution that can retrieve, reply to, and pin video comments after applying for the interaction-management permission and `video.comment` scope.
- Douyin Open Platform documents content publishing through OpenAPI, including publishing videos/images, carrying topics, and viewing playback/interaction data, with moderation and format constraints.
- Douyin Open Platform exposes a Xingtu creator hot-list API under `star_tops`, which suggests competitor and creator-rank monitoring should be treated as an official permissioned data source when possible.
- Douyin user-data APIs such as fan-count retrieval require permissions and user authorization, and at least some metrics update with delay rather than true real time.
- Feishu Open Platform supports message events for bots, which makes a separated Venus Feishu bot a reasonable future control surface.
- OceanEngine Commercial Open Platform covers Marketing API capabilities for marketing automation, reporting, creative assets, and audience/DMP management, so Qianchuan/Xingtu should be a later permissioned integration rather than a phase-one assumption.
- NMPA has official cosmetics data and service surfaces relevant to product research: domestic ordinary cosmetics filing lookup, cosmetics registration/filing service platform, cosmetics raw-material safety information registration, cosmetics efficacy claim evaluation rules, labeling management rules, and broader NMPA data search.
- Product research should separate evidence types: filing/registration identity, ingredient list, raw-material safety evidence, efficacy-claim evidence, labeling/compliance risk, supplier/testing documents, public controversy history, and creator-safe talking points.
- Feishu official documentation confirms the relevant bot surfaces: receive message events, send messages, reply to messages, and custom bot webhook usage. For Venus, this supports a mobile command/report/approval surface; custom bot webhooks are useful for one-way pushes, while application bots are needed for richer two-way control.
- WeChat Mini Program official documentation exposes message push, customer service messaging, subscribe-message sending, and customer-service entry components. For Venus, this supports a future skincare Q&A mini-program flow, but outbound messages and customer-service replies need platform rules and user/session constraints.
- Enterprise WeChat official documentation exposes customer detail, customer group list, application message sending, and callback configuration pages. For Venus, this supports future private-domain routing and customer handoff, but it must stay approval-gated and privacy-audited.

## Requirement Matrix

| Area | Phase 1 Requirement | Later Requirement | Proof Needed |
|---|---|---|---|
| Content trend intelligence | Generate beauty/skincare hotspot briefs, controversy briefs, filming advice, and scripts from reviewed sources or imported samples. | 24/7 official/API-based Douyin monitoring and alerting. | Sample hotspot report and script pack. |
| Product research | Build a structured product-risk analysis workflow covering filing, ingredients, claims, suppliers/testing docs, and controversy. | Automated official-source lookup and recurring product watchlists. | Sample product research card with evidence links and risk labels. |
| Persona learning | Store and apply user philosophy, speaking style, persona boundaries, preferred claims, and banned expressions. | Continuous feedback loop from approved/rejected drafts and published performance. | Script output visibly follows a saved style profile. |
| Douyin comments | No direct public reply by default; analyze imported comments or permissioned API data. | Retrieve, summarize, draft replies, and optionally reply after approval via official permissions. | Comment summary plus approval-gated reply drafts. |
| Video production | Generate script, title, hook, shot list, editing notes, cover-title ideas, and CTA. | Connect to editing tools or Canva/video tooling for semi-automatic assets. | One complete content production brief. |
| Feishu mobile | Design as a separate Venus entry with isolated app identity and storage. | Receive commands, send cards/reports, approvals, and reminders in Feishu. | Separate config paths and app identifiers from Xiaolongxia. |
| WeChat private domain | Document future answer-and-routing flow only. | Mini-program skincare Q&A and enterprise WeChat lead routing with compliance logs. | Approved mini-program/enterprise WeChat integration plan. |
| Qianchuan and Xingtu | Treat as strategy/reporting only until credentials and permissions exist. | Budget suggestions, audience analysis, ad report diagnostics, Xingtu brief generation. | Approval-gated ad action workflow and spend limits. |
| Competitor monitoring | Define competitor account schema and manual/sample analysis. | 24/7 watchlist, video/live/ad frequency tracking, dashboards, and alerts. | Competitor analysis report with tracked metrics. |
| Self-improvement | Keep logs, feedback, eval criteria, and backups in the design. | Automated regression tests, periodic learning summaries, backup health checks. | Audit log, eval cases, and backup verification. |

## Source Strategy

- Treat official platform APIs and government/regulatory sources as highest authority where available.
- Treat screenshots, exports, manually supplied URLs, and logged-in browser evidence as secondary operational evidence.
- Treat general web/social search as trend-discovery evidence, not final proof for product safety or compliance claims.
- Every generated script should carry an internal evidence bundle: source list, freshness, confidence, risk notes, and claims that need human review.

## Pre-Implementation Checklist

### Account And Permission Readiness

- Douyin Open Platform app, OAuth setup, and permission requests for comment management, content publishing, user/video data, and any hotspot or Xingtu data endpoints.
- OceanEngine/Qianchuan/Xingtu developer access, advertiser/account IDs, token management, report permissions, and explicit budget-spend approval limits.
- Feishu app for Venus only, separate from Xiaolongxia, with independent app ID, secret, event callback, bot identity, storage, and logs.
- WeChat Mini Program app and message/callback configuration for future skincare Q&A and customer-service flows.
- Enterprise WeChat app, customer contact permissions, callback URL, visible scope, and customer-data access policy for private-domain handoff.
- Airtable workspace/base or local database choice for structured records. Airtable is suitable if the user wants fast human-editable operations; a local database is suitable if privacy and code-first control are higher priority.
- OpenAI API key and model access for agent execution, stored only in local environment files or secret stores, never committed.

### Candidate Structured Data Objects

- `sources`: official APIs, manual imports, browser captures, public web pages, regulatory pages, screenshots, and documents.
- `hotspots`: topic/product/creator/comment/ingredient/tag trend items with score, freshness, controversy, and evidence links.
- `products`: brand, product name, filing/registration ID, category, claims, ingredient summary, risk score, and research status.
- `ingredients`: INCI/common name, function, sensitivity concerns, regulatory notes, supplier references, and evidence quality.
- `creators`: competitor or reference accounts, positioning, content style, commercial intensity, live behavior, and tracked metrics.
- `comments`: imported or API-collected comments, intent, sentiment, risk class, suggested reply, and approval status.
- `scripts`: hook, body, turning point, CTA, title, cover text, shot list, editing notes, compliance notes, and expected interaction driver.
- `persona_profile`: skincare beliefs, product standards, speaking style, preferred vocabulary, banned claims, boundary examples, and approved samples.
- `approvals`: action type, generated draft, evidence bundle, reviewer decision, timestamp, and final action taken.
- `experiments`: published content, hypothesis, topic source, script version, performance metrics, learning, and next recommendation.
- `backups`: backup target, schedule, checksum/status, last verified timestamp, and recovery note.

### Approval Levels

- Level 0, safe analysis: summarize sources, classify topics, draft internal notes, and generate private recommendations.
- Level 1, creator draft: generate scripts, titles, shot lists, content briefs, and reply drafts for review.
- Level 2, external communication: send Feishu messages, publish reports to a private channel, or answer mini-program users after approval.
- Level 3, public platform action: reply to Douyin comments, publish content, pin comments, or interact with users. Requires explicit approval until the user changes policy.
- Level 4, money or reputation risk: ad budget changes, Qianchuan campaigns, Xingtu acceptance guidance, medical-like claims, crisis replies, or lead-routing automation. Requires explicit approval, audit log, and rollback plan.

### Isolation Rules For Venus And Xiaolongxia

- Separate Feishu app identity, callback URL, app secrets, bot name, command namespace, storage folder, logs, and database/base.
- Separate environment variable prefix, for example `VENUS_...`, never reuse Xiaolongxia variables.
- Separate Airtable base or at least separate tables/views with no shared automation unless explicitly approved.
- Separate backup path and retention policy.
- Any shared library code must be generic and must not contain agent-specific secrets, persona memory, user data, or platform tokens.

### First Useful Smoke Tests

- Given a small batch of sample hotspot notes, Venus produces a ranked hotspot brief with evidence, risk tags, filming angle, and three script options.
- Given a product name and manually supplied source links, Venus produces a product research card with filing/ingredient/claim/controversy sections and safe talking points.
- Given three approved writing samples, Venus generates a script that follows the persona profile and flags uncertain claims.
- Given sample comments, Venus classifies intent/sentiment/risk and drafts approval-gated replies.
- Given an approval record, Venus logs the decision and updates learning notes without exposing private data.

## Official URLs To Revisit During Implementation

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

## Working Assumption

The first useful deliverable should be a Phase 1 design and implementation roadmap, not immediate integration with every external platform.

The user confirmed that the first version should include all three previously proposed centers:

- content center: hotspot/trend intelligence, professional analysis, filming advice, and high-retention short-video scripts;
- product research center: brand, filing, ingredient, supplier/testing evidence, and controversy/risk analysis;
- persona center: skincare philosophy, product judgment, speaking style, expression style, and creator persona learning.
