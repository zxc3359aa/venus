"""维纳斯 M0 端到端演示：热点→简报→（不可逆）发布→审批挂起→批准→幂等执行。

运行：  PYTHONPATH=src python -m venus.demo_e2e
同时演示隐私红线：C3（我的语料）禁止发往云 LLM。
"""
from __future__ import annotations

from venus.approval import IdempotentExecutor, InMemoryApprovalGate
from venus.connectors_feishu import FakeFeishuGateway
from venus.contracts import (
    ApprovalStatus,
    DataClass,
    Destination,
    GraphState,
    Tagged,
)
from venus.llm import FakeLLMProvider
from venus.logging_setup import get_logger
from venus.modules.m1_hotspot import build_publish_action, map_reduce_summarize, validate_copy
from venus.orchestrator import Orchestrator, RunContext
from venus.privacy import DefaultPrivacyFirewall

log = get_logger("venus.demo")


def main() -> None:
    llm = FakeLLMProvider(
        scripted={"汇总要点成简报": "你知道吗？这个三秒钩子让你看完想关注，并在评论区扣1"}
    )
    fw = DefaultPrivacyFirewall()
    gate = InMemoryApprovalGate()
    executor = IdempotentExecutor()
    feishu = FakeFeishuGateway()
    posted = {"n": 0}

    def execute_fn(action):
        posted["n"] += 1
        return f"executed:{action.kind}"

    orch = Orchestrator(RunContext(gate=gate, executor=executor, execute_fn=execute_fn))

    # 1) 隐私红线：C3（我的语料）禁止外发云 LLM
    persona = Tagged(payload={"语料": "我的口播原文……"}, data_class=DataClass.C3_SECRET, pii=True)
    log.info("C3→云LLM 允许? %s", fw.allow_egress(Destination.CLOUD_LLM, persona))

    # 2) map-reduce 汇总（私有 LLM，C1 任务）
    brief = map_reduce_summarize(llm, ["热点A……", "热点B……", "争议成分C……"])
    log.info("简报: %s", brief)
    log.info("文案校验: %s", validate_copy(brief) or "通过")

    # 3) 发布视频=不可逆 → 审批挂起
    state = GraphState(task_id="demo", intent="publish", inputs={})
    action = build_publish_action(brief)
    s, state = orch.run_until_suspend(state, action)
    log.info("状态: %s | 已推审批卡片: %d", s.value, len(gate.pushed))
    feishu.send_approval_card(gate.pushed[-1])

    # 4) 用户在飞书点“同意”，恢复并幂等执行
    gate.resolve(state.pending_approval_id, ApprovalStatus.APPROVED, decided_by="owner")
    s, state = orch.resume(state, action)
    log.info("状态: %s | 执行次数: %d", s.value, posted["n"])


if __name__ == "__main__":
    main()
