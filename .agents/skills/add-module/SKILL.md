---
name: add-module
description: Use when adding a Venus M-series module or expanding one against the v2.0 specification.
---

# $add-module

新增或扩展 M 模块时必须：

1. 先读 `docs/Venus-Spec-v2.0.md` 中对应模块的目标、IO、数据源 Tier、流程、合规和验收。
2. 以 `src/venus/contracts.py` 为唯一接口锚点；输入/输出必须用 `Tagged` 和 `DataClass` 表达数据边界。
3. 禁止 Tier C；如果只能 Tier C，停止并写 `// TIER-C-BLOCKED: 见 §2`，给 Tier A/B 替代。
4. C3 不得进入云 LLM、第三方数据或日志；需要个性化时先在私有侧蒸馏成 C1 风格描述符。
5. 对外不可逆动作只构造 `Action` 草稿，必须带 `idempotency_key` 并经 `ApprovalGate`。
6. 先写失败测试，再写实现；外部 API/LLM 用 Fake/Mock，保证离线可测。
7. 模块完成后运行 `make test`、`make compliance-gate`、`make contract-conformance`。
