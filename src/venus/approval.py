"""人在回路审批网关 + 幂等执行器（规格 §5 / §9，修订 B2）。

M0 用内存实现，保证可离线测试；生产应换为 SQLite/Postgres 持久化，
并由 Temporal/LangGraph 检查点承载“挂起-恢复”。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from venus.contracts import Action, ApprovalRequest, ApprovalStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryApprovalGate:
    """满足 contracts.ApprovalGate 协议；resolve 幂等；支持过期。"""

    def __init__(self, ttl_seconds: int = 86400):
        self._store: dict[str, ApprovalRequest] = {}
        self.ttl = ttl_seconds
        self.pushed: list[ApprovalRequest] = []  # 模拟“已推送飞书审批卡片”

    def submit(self, action: Action) -> ApprovalRequest:
        req = ApprovalRequest(
            id=str(uuid.uuid4()),
            action=action,
            status=ApprovalStatus.PENDING,
            created_at=_now(),
            expires_at=_now() + timedelta(seconds=self.ttl),
        )
        self._store[req.id] = req
        self.pushed.append(req)  # 真实：调 lark_oapi 发交互卡片（同意/修改/驳回）
        return req

    def resolve(self, approval_id, status, decided_by, edited_payload=None) -> ApprovalRequest:
        req = self._store.get(approval_id)
        if req is None:
            raise KeyError(approval_id)
        if req.status != ApprovalStatus.PENDING:
            return req  # 幂等：已决议直接返回，不重复生效
        if _now() > req.expires_at:
            req.status = ApprovalStatus.EXPIRED
            return req
        req.status = status
        req.decided_by = decided_by
        req.edited_payload = edited_payload
        return req

    def get(self, approval_id) -> ApprovalRequest | None:
        return self._store.get(approval_id)


class IdempotentExecutor:
    """保证同一 idempotency_key 的外部副作用动作只执行一次（修订：重试/重复回调安全）。"""

    def __init__(self):
        self._done: dict[str, Any] = {}

    def execute(self, action: Action, fn: Callable[[Action], Any]) -> Any:
        if action.idempotency_key in self._done:
            return self._done[action.idempotency_key]  # 幂等：不重复执行
        result = fn(action)
        self._done[action.idempotency_key] = result
        return result
