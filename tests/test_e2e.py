"""编排器端到端：不可逆动作的审批挂起→批准恢复→幂等执行；以及驳回路径。"""
from __future__ import annotations

from venus.approval import IdempotentExecutor, InMemoryApprovalGate
from venus.contracts import Action, ApprovalStatus, DataClass, GraphState
from venus.orchestrator import Orchestrator, RunContext, State


def _make(reversible=False):
    return Action(
        kind="publish_video", summary="发布视频", payload={"id": 1},
        idempotency_key="pub-1", data_class=DataClass.C1_INTERNAL, reversible=reversible,
    )


def _orch():
    calls = {"n": 0}

    def execute_fn(action):
        calls["n"] += 1
        return f"posted:{action.kind}"

    gate = InMemoryApprovalGate()
    orch = Orchestrator(RunContext(gate=gate, executor=IdempotentExecutor(), execute_fn=execute_fn))
    return orch, gate, calls


def test_irreversible_action_suspends_then_executes_on_approval():
    orch, gate, calls = _orch()
    state = GraphState(task_id="t1", intent="publish", inputs={})
    action = _make(reversible=False)

    s, state = orch.run_until_suspend(state, action)
    assert s == State.WAITING_APPROVAL
    assert state.pending_approval_id is not None
    assert len(gate.pushed) == 1  # 已推审批卡片
    assert calls["n"] == 0  # 未审批前不执行

    gate.resolve(state.pending_approval_id, ApprovalStatus.APPROVED, decided_by="owner")
    s, state = orch.resume(state, action)
    assert s == State.DONE
    assert calls["n"] == 1
    assert state.outputs["execute_result"] == "posted:publish_video"


def test_rejected_action_does_not_execute():
    orch, gate, calls = _orch()
    state = GraphState(task_id="t2", intent="publish", inputs={})
    action = _make(reversible=False)
    s, state = orch.run_until_suspend(state, action)
    gate.resolve(state.pending_approval_id, ApprovalStatus.REJECTED, decided_by="owner")
    s, state = orch.resume(state, action)
    assert s == State.FAILED
    assert calls["n"] == 0
    assert state.errors


def test_reversible_action_executes_without_approval():
    orch, gate, calls = _orch()
    state = GraphState(task_id="t3", intent="draft", inputs={})
    action = _make(reversible=True)
    s, state = orch.run_until_suspend(state, action)
    assert s == State.DONE
    assert calls["n"] == 1
    assert len(gate.pushed) == 0  # 可逆动作不进审批
