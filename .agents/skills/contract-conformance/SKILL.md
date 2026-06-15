---
name: contract-conformance
description: Use before committing or submitting a PR for Venus code that touches module or core interfaces.
---

# $contract-conformance

运行：

```bash
make contract-conformance
```

必须确认：

- 实现与 `src/venus/contracts.py` 的 Protocol/ABC/dataclass 一致。
- 模块输入/输出保留 `Tagged`、`DataClass`、`Action`、`idempotency_key` 等契约字段。
- 新模块不得自行发明与 `contracts.py` 冲突的抽象。
