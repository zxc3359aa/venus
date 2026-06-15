---
name: compliance-gate
description: Use before committing or submitting a PR for Venus module work.
---

# $compliance-gate

运行：

```bash
make compliance-gate
```

必须通过以下红线：

- 无 Tier C 实现、模拟登录、绕验证码、刷量或非官方抓取。
- C3 不可外发云 LLM、第三方数据或日志。
- 不可逆动作必须经 `ApprovalGate`，且 `Action` 带 `idempotency_key`。
- 无硬编码密钥、Token、密码或真实凭据。
