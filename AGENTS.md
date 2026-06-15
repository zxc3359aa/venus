# AGENTS.md — 维纳斯（Venus）项目 · Codex 操作指令

> Codex 会自动读取本文件作为项目指令。**开工前必须读完本文件与《交付级工程规格 v2.0》。**
> 本文件 = 工程纪律 + 红线 + 你（Codex）应使用的工具/技能/插件 + 操作手册。

## 1. 项目身份与目标
维纳斯：美妆护肤全自动智能体系统，目标是把账号做成抖音头部达人。全能、全自动、超强大、**绝对忠诚（=可控+对齐+讲真话，非谄媚）**、**隐私绝对底线**。完整规格见 `docs/Venus-Spec-v2.0.md`（或随附的 v2.0 文档）。

## 2. 不可违背的红线（最高优先级，高于功能完成度）
1. **合规分级**：严守规格 §2 三级分层。**禁止生成 Tier C 代码**（爬抖音、模拟登录批量、绕验证码、刷量、弹幕非官方自动发送）。只能 Tier C 实现时**停止**并注释 `// TIER-C-BLOCKED: 见 §2`，给 Tier A/B 替代。
2. **数据红线**：任何数据带 `DataClass` 标签；出网前过隐私防火墙三位一体（`src/venus/privacy.py`）。**C3（个人画像/语料/私域 PII）禁止进入云 LLM、第三方数据、云训练。** 含 C3 语料的微调只在私有算力。
3. **人在回路**：所有对外不可逆动作（发视频、公开回评/弹幕、投放花钱、加客户、发私信、删数据）必须经 `ApprovalGate`（`src/venus/approval.py`）：草稿→飞书卡片审批→确认→执行。自动化默认关，逐项 feature flag 开启。
4. **幂等**：外部动作带 `idempotency_key`，重放只生效一次（`IdempotentExecutor`）。审批为异步挂起/恢复，**不得阻塞线程等待人审**。
5. **机密零硬编码**：密钥/Token 一律 `.env`+配置中心；**禁止打印到日志或写进提交**（日志走 `src/venus/logging_setup.py` 的脱敏处理器）。
6. **不臆造**：会随平台更新的接口/Scope/资质，以官方最新文档为准，标 `// VERIFY-DOC:`，并用 Context7 MCP 核对（见 §4）。

## 3. 唯一接口锚点
**`src/venus/contracts.py` 是全系统接口的唯一来源。** 实现任何模块都以它为准，禁止发明不一致的抽象。新增能力前先看是否已有契约；缺则先补契约再实现（接口先行）。

## 4. 你（Codex）应使用的工具 / 技能 / 插件
### 4.1 项目内技能（`.agents/skills/`，用 `$名称` 调用）
- `$add-module`：按规格 §8 模板新增一个 M 模块（目标/IO/数据源 Tier/流程/合规/验收 + 接口实现 + 测试）。
- `$compliance-gate`：提交前自检——Tier 分层无 Tier C、数据流向矩阵无 C3 外发、不可逆动作走审批、机密未泄露。
- `$contract-conformance`：核对新代码与 `contracts.py` 一致（签名、数据类标签、幂等键）。
> 需要新增可复用工作流时，用 `$skill-creator` 创建新的项目技能（写入 `.agents/skills/<name>/SKILL.md`）。

### 4.2 MCP servers（在 `.codex/config.toml` 的 `[mcp_servers.*]` 配置；模板已给）
- **context7**（强烈推荐）：查最新 SDK/库/API 文档，**专门用于消解所有 `// VERIFY-DOC` 项**（飞书 lark-oapi、巨量引擎、抖音开放平台、企业微信、LangGraph、Temporal 等）。写集成代码前先查文档，不要凭记忆。
- **github**：管理 PR/Issue（git 之外的协作）。
- **postgres**：连库核对 schema / 迁移 / 查询（数据层开发）。
- **openai-docs**：查 Codex/OpenAI 文档。
- **playwright / chrome-devtools**：**仅限合规用途**（渲染/巡检自有页面、NMPA 公开查询的人工辅助）。**严禁用于抓取抖音或竞品数据（=Tier C）。**

### 4.3 执行策略规则（Starlark，建议放入 `~/.codex/rules/` 或团队 `requirements.toml`）
```starlark
prefix_rule(pattern=["git","push"], decision="forbidden", justification="只走 PR，不直接推主干")
prefix_rule(pattern=["rm","-rf"], decision="prompt", justification="破坏性操作需确认")
prefix_rule(pattern=["curl"], decision="prompt", justification="出网须经隐私防火墙白名单，禁止绕过")
prefix_rule(pattern=["wget"], decision="prompt", justification="同上")
```

### 4.4 Python 库与官方 SDK（分阶段引入，装包用 `uv`/`pip --break-system-packages`）
- **M0 核心**：标准库 + `pytest`（当前骨架零三方依赖即可跑）。
- **编排**：`langgraph`、`langgraph-checkpoint-sqlite`/`-postgres`；后期 `temporalio`（持久长流程）。
- **数据**：`psycopg`/`sqlalchemy` + `pgvector`、`redis`、`minio`；后期 `clickhouse-connect`、`milvus`/`qdrant-client`。
- **网络/重试**：`httpx`、`tenacity`（指数退避）。
- **可观测**：`structlog`、`opentelemetry-sdk`、`prometheus-client`。
- **测试/评测**：`pytest`、`pytest-asyncio`、`respx`/`vcrpy`（HTTP 录制回放，离线测外部调用）、`hypothesis`；内容质量用本仓 `eval/` 评分器（可选 `deepeval`/`ragas`）。
- **集成 SDK**：飞书 `lark-oapi`（官方，`lark.ws.Client` 长连接 + `EventDispatcherHandler`）；企业微信用 `wechatpy` 或自封装；巨量引擎/抖音开放平台多为 OpenAPI/HTTP，用 `httpx` 自封装客户端 + Context7 查文档（`// VERIFY-DOC`）。
- **视频/语音**：`ffmpeg`（二进制）+ `ffmpeg-python`；ASR `faster-whisper`；TTS 用厂商 SDK（需授权）。
- **LLM**：`openai`（兼容多数 OpenAI 兼容端点）；私有侧用 vLLM/Ollama 暴露 OpenAI 兼容 API（承担 C2/C3 任务）。

## 5. 运行命令
- `make test` —— 跑单元测试（应全绿）。
- `make demo` —— 端到端演示（隐私红线 + 审批挂起/恢复 + 幂等执行）。
- `make eval` —— 内容质量评测（golden 集）。
- `make lint` —— 配置 ruff/black/mypy 后启用。

## 6. 操作手册（Operating Procedure，每个任务都照此执行）
1. 读 AGENTS.md 与规格 v2.0；先 `make test` 确认基线全绿。
2. 以 `contracts.py` 为锚点；新增能力用 `$add-module`。
3. 写集成代码前，用 **Context7 MCP** 核对该平台的最新接口/Scope/资质（消解 `// VERIFY-DOC`）。
4. 任何对外不可逆动作必须经 `ApprovalGate`；任何外发必须经隐私防火墙；C3 绝不外发云。
5. 为新逻辑写测试；依赖 LLM/外部 API 的逻辑用 Fake/Mock + 录制回放，保证离线可测。
6. 提交前依次跑：`make lint` → `make test` → `$compliance-gate` → `$contract-conformance`。
7. 约定式提交（`feat(m1): …`/`fix(privacy): …`）；走 PR，不直接 push 主干。
8. 每个阶段结束输出"已完成 / 未完成 / 阻塞项 / 下一步"。

## 7. 与"小龙虾"的隔离
维纳斯是**独立飞书自建应用**：独立 App ID/Secret、独立长连接进程、独立指令前缀、`venus_` 独立数据前缀与独立文件空间。绝不复用或干扰小龙虾的凭据/进程/数据/文件。
