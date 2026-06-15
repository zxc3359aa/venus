# 维纳斯（Venus）· M0 工程骨架

美妆护肤全自动智能体系统的 **M0 最小可运行骨架**。配套《交付级工程规格 v2.0》。
本骨架**零三方依赖即可跑测试**（标准库 + pytest），用于给 Codex 一个可执行的起点与接口锚点。

## 这套骨架证明了什么（可交付的逻辑闭环）
- **隐私红线运行期生效**：C3（个人画像/语料/私域 PII）被数据流向矩阵拦截，禁止外发云 LLM（`src/venus/privacy.py`）。
- **人在回路 + 审批挂起/恢复**：不可逆动作（如发布视频）提交审批后挂起，飞书回调批准后凭 `approval_id` 恢复执行（`src/venus/orchestrator.py` + `approval.py`）。
- **幂等执行**：同一 `idempotency_key` 只执行一次，重试/重复回调安全。
- **确定性可测**：LLM 用 Fake 注入，离线可测；内容质量用 golden 评测器（`eval/`）。
- **日志脱敏**：密钥/手机号等自动打码（`src/venus/logging_setup.py`）。

## 运行
```bash
make setup      # 安装 pytest
make test       # 14 项单元测试应全绿
make demo       # 端到端演示（隐私红线 + 审批挂起/恢复 + 幂等）
make eval       # 内容质量评测（4/4）
```

## 给 Codex
**先读 `AGENTS.md`**（Codex 自动读取的项目指令：红线、工具/技能/插件、操作手册）。
接口唯一锚点：`src/venus/contracts.py`。MCP/技能配置见 `.codex/config.toml` 与 `.agents/skills/`。

## 目录
```
AGENTS.md                 # Codex 操作指令（红线 + 工具/技能/MCP + 手册）
.codex/config.toml        # 审批/沙箱/MCP servers
.agents/skills/           # 项目技能：$add-module / $compliance-gate / $contract-conformance
src/venus/contracts.py    # 接口唯一锚点（§5）
src/venus/privacy.py      # 隐私防火墙三位一体（§3.2/§9）
src/venus/llm.py          # LLM 双拓扑（Fake + OpenAI 兼容占位）
src/venus/approval.py     # 审批网关(幂等/超时) + 幂等执行器
src/venus/orchestrator.py # 编排状态机(审批挂起/恢复)
src/venus/logging_setup.py# 日志脱敏
src/venus/connectors_feishu.py  # 飞书长连接(真实 lark-oapi + 离线 Fake)
src/venus/modules/m1_hotspot.py # M1 切片(map-reduce 汇总 + 文案校验)
src/venus/demo_e2e.py     # 端到端演示
eval/                     # golden 集 + 评分器
tests/                    # 单元 + 端到端测试
docker-compose.yml        # 分级基础设施(mvp/full profile)
```
> M0 用扁平包结构与内存实现；生产按规格 §4.5 展开到完整目录树，并把内存实现替换为 Postgres/Redis/Temporal 持久化。
