"""编排状态机（规格 §4.3）。

实现“执行命中不可逆动作 → 提交审批并挂起（不阻塞线程）→ 飞书回调后凭 approval_id 恢复”的闭环。
生产用 LangGraph 状态图 + Temporal 持久化承载；此处给出可测试的最小内核。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from venus.approval import IdempotentExecutor, InMemoryApprovalGate
from venus.contracts import Action, ApprovalStatus, GraphState


class State(str, Enum):
    PLANNING = "planning"
    ROUTING = "routing"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    CRITIQUING = "critiquing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class RunContext:
    gate: InMemoryApprovalGate
    executor: IdempotentExecutor
    execute_fn: Callable[[Action], Any]              # 真实执行（平台 API）；可注入
    critic_fn: Callable[[dict], bool] = lambda outputs: True  # CRITIQUING 校验


class Orchestrator:
    def __init__(self, ctx: RunContext):
        self.ctx = ctx

    def run_until_suspend(self, state: GraphState, action: Action) -> tuple[State, GraphState]:
        """PLANNING → ROUTING → EXECUTING；命中不可逆动作则提交审批并挂起。"""
        if not action.reversible:
            req = self.ctx.gate.submit(action)
            state.pending_approval_id = req.id
            return State.WAITING_APPROVAL, state
        return self._execute_and_finish(state, action)

    def resume(self, state: GraphState, action: Action) -> tuple[State, GraphState]:
        """飞书回调后恢复。审批通过则执行（幂等）；驳回/过期则失败。"""
        if state.pending_approval_id is None:
            raise RuntimeError("无挂起审批可恢复")
        req = self.ctx.gate.get(state.pending_approval_id)
        if req is None:
            raise RuntimeError("审批不存在")
        if req.status == ApprovalStatus.PENDING:
            return State.WAITING_APPROVAL, state  # 仍在等待
        if req.status == ApprovalStatus.APPROVED:
            eff = action
            if req.edited_payload is not None:  # 用户改后批准
                eff = Action(**{**action.__dict__, "payload": req.edited_payload})
            state.pending_approval_id = None
            return self._execute_and_finish(state, eff)
        # REJECTED / EXPIRED
        state.pending_approval_id = None
        state.errors.append(f"审批未通过: {req.status.value}")
        return State.FAILED, state

    def _execute_and_finish(self, state: GraphState, action: Action) -> tuple[State, GraphState]:
        result = self.ctx.executor.execute(action, self.ctx.execute_fn)  # 幂等执行
        state.outputs["execute_result"] = result
        ok = self.ctx.critic_fn(state.outputs)  # CRITIQUING
        return (State.DONE if ok else State.FAILED), state
