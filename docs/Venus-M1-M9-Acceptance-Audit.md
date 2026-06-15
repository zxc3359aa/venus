# 维纳斯 M1-M9 整链验收与合并清单

生成日期：2026-06-15

本文记录当前 M1-M9 交付链的可复核证据、合并顺序、已完成边界与未完成生产化事项。它用于辅助审阅与合并 PR，不替代 `AGENTS.md`、`docs/Venus-Spec-v2.0.md` 或 `src/venus/contracts.py`。

## 1. 代码与 PR 链

当前可合并链路为：

| 阶段 | PR | base | head | head SHA | 状态 |
|---|---:|---|---|---|---|
| M1 | #2 | `main` | `codex/venus-v2-m1` | `6a1432c` | open, ready |
| M2 | #3 | `codex/venus-v2-m1` | `codex/venus-v2-m2` | `15e3368` | open, ready |
| M3 | #4 | `codex/venus-v2-m2` | `codex/venus-v2-m3` | `3a7a9c6` | open, ready |
| M4 | #5 | `codex/venus-v2-m3` | `codex/venus-v2-m4` | `932414a` | open, ready |
| M5 | #6 | `codex/venus-v2-m4` | `codex/venus-v2-m5` | `0e9c5f9` | open, ready |
| M6 | #7 | `codex/venus-v2-m5` | `codex/venus-v2-m6` | `2a6b309` | open, ready |
| M7 | #8 | `codex/venus-v2-m6` | `codex/venus-v2-m7` | `e4ad4a8` | open, ready |
| M8 | #9 | `codex/venus-v2-m7` | `codex/venus-v2-m8` | `368ce6f` | open, ready |
| M9 | #10 | `codex/venus-v2-m8` | `codex/venus-v2-m9` | M9 功能提交 `38a05f3`；PR 最新 head 以 GitHub 为准 | open, ready |

建议合并顺序：#2, #3, #4, #5, #6, #7, #8, #9, #10。

## 2. 本地等价合并验证

已从 `origin/main` 创建临时本地 worktree，并按 #2 到 #10 的顺序执行：

```bash
git merge --ff-only origin/codex/venus-v2-m1
git merge --ff-only origin/codex/venus-v2-m2
git merge --ff-only origin/codex/venus-v2-m3
git merge --ff-only origin/codex/venus-v2-m4
git merge --ff-only origin/codex/venus-v2-m5
git merge --ff-only origin/codex/venus-v2-m6
git merge --ff-only origin/codex/venus-v2-m7
git merge --ff-only origin/codex/venus-v2-m8
git merge --ff-only origin/codex/venus-v2-m9
make test
make compliance-gate
make contract-conformance
make demo
make eval
```

验证结果：

- 所有阶段均可 fast-forward 合并，无本地冲突。
- M9 功能最终提交为 `38a05f3 feat(m9): add evolution and backup package`；后续仅追加验收、Context7 与平台接口生产化红线文档。
- `make test`：59 passed。
- `make compliance-gate`：PASS。
- `make contract-conformance`：PASS。
- `make demo`：隐私红线、审批挂起/恢复与幂等演示通过。
- `make eval`：4/4。

## 3. 分阶段门禁复核

已在每个阶段分支快照中复跑 `make test`、`make compliance-gate`、`make contract-conformance`：

| 分支 | 测试结果 | 合规门 | 契约门 |
|---|---:|---|---|
| `codex/venus-v2-m1` | 19 passed | PASS | PASS |
| `codex/venus-v2-m2` | 23 passed | PASS | PASS |
| `codex/venus-v2-m3` | 28 passed | PASS | PASS |
| `codex/venus-v2-m4` | 33 passed | PASS | PASS |
| `codex/venus-v2-m5` | 38 passed | PASS | PASS |
| `codex/venus-v2-m6` | 43 passed | PASS | PASS |
| `codex/venus-v2-m7` | 49 passed | PASS | PASS |
| `codex/venus-v2-m8` | 54 passed | PASS | PASS |
| `codex/venus-v2-m9` | 59 passed | PASS | PASS |

说明：远端 `main` 当前不是完整 M0 骨架入口，因此不能用远端 `main` 重新证明规格文本中的“14 项基线”。M1 分支导入了 M0 骨架与 M1 切片，当前可复核的阶段基线从 M1 的 19 项测试开始。

## 4. 当前完成边界

已完成：

- 以 `src/venus/contracts.py` 为唯一接口锚点，M1-M9 模块均使用 `Tagged`、`DataClass`、`Action` 与 `idempotency_key` 等契约字段。
- M1-M9 均为离线可测实现，不依赖真实 LLM、真实平台账号或第三方服务。
- 合规门覆盖 Tier C 关键红线、硬编码机密扫描、C3 云端流向阻断、不可逆动作审批边界。
- 契约门覆盖 LLM Provider、审批网关，以及 M1-M9 主要输出/Action 形状。
- 不可逆外部动作只构造 `Action` 草稿，不直接发视频、回评论、投流、加客户或删数据。
- M3/M9 对 C3 原始画像、语料、私域个人信息保持阻断，不允许进入云端模型或第三方训练路径。

## 5. 未完成生产化事项

以下事项尚未完成，不能被当前 PR 链声称为生产可用：

- 真实飞书长连接、抖音开放平台、巨量引擎、企业微信/小程序等生产接口。
- OAuth Token 持久化、刷新、分布式锁、生产级频控、重试、熔断与审计落库。
- 真实 3-2-1 备份执行器、备份介质写入、定期恢复演练与一键导出/彻底删除执行器。
- 生产级数据库迁移、对象存储、Redis/队列、ClickHouse/Temporal 等可选 full profile。
- 真正的私有 LLM 推理/训练环境，以及 C2/C3 的私有侧模型路由。

## 6. Context7 与平台接口红线

当前仓库 `.codex/config.toml` 已声明 Context7 MCP：

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
```

当前会话启动时还没有可调用的 Context7 工具；新增 MCP 配置通常需要重启或重载 Codex 会话后才会出现在工具列表。因此，在工具可见并完成最新官方文档核验之前，不应继续写任何真实平台接口。

接口生产化前置清单见 `docs/Platform-Interface-Readiness-Checklist.md`。

允许继续推进的安全工作：

- 保持离线 Fake/Mock 与契约测试。
- 写平台接口的设计文档、字段占位与 `// VERIFY-DOC` 标记。
- 准备 Context7 启用说明、账号资质清单与 PR 合并清单。

禁止继续推进的工作：

- 在未用 Context7 核验最新官方文档前实现飞书、抖音、巨量引擎、企业微信/小程序的真实调用。
- 绕过官方/授权数据源抓取抖音或竞品数据。
- 将 C3 画像、原始语料或私域个人信息发送给云端模型、第三方数据源或云训练服务。

## 7. 合并后建议验证

合并 #2 到 #10 后，在 `main` 上运行：

```bash
git pull --ff-only
make test
make compliance-gate
make contract-conformance
make demo
make eval
```

预期结果：

- `make test`：59 passed。
- `make compliance-gate`：PASS。
- `make contract-conformance`：PASS。
- `make demo`：展示 C3 阻断、审批挂起/恢复与幂等执行。
- `make eval`：4/4。
