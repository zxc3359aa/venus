"""维纳斯契约核对：确认实现仍以 contracts.py 为接口锚点。"""
from __future__ import annotations

from venus.approval import InMemoryApprovalGate
from venus.contracts import Action, ApprovalStatus, DataClass, LLMProvider, Tagged
from venus.llm import FakeLLMProvider
from venus.modules.m1_hotspot import build_m1_hotspot_package, build_publish_action


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_llm_provider())
    failures.extend(_check_approval_gate_shape())
    failures.extend(_check_m1_contracts())

    if failures:
        print("contract-conformance: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("contract-conformance: PASS")
    return 0


def _check_llm_provider() -> list[str]:
    if isinstance(FakeLLMProvider(), LLMProvider):
        return []
    return ["FakeLLMProvider 不满足 LLMProvider Protocol"]


def _check_approval_gate_shape() -> list[str]:
    gate = InMemoryApprovalGate()
    required = ["submit", "resolve", "get"]
    missing = [name for name in required if not callable(getattr(gate, name, None))]
    if missing:
        return [f"InMemoryApprovalGate 缺少方法: {', '.join(missing)}"]
    action = Action(
        kind="publish_video",
        summary="发布",
        payload={"id": 1},
        idempotency_key="contract-check",
        data_class=DataClass.C1_INTERNAL,
    )
    req = gate.submit(action)
    resolved = gate.resolve(req.id, ApprovalStatus.APPROVED, "owner")
    again = gate.resolve(req.id, ApprovalStatus.REJECTED, "owner")
    if resolved.status != again.status:
        return ["ApprovalGate.resolve 非幂等"]
    return []


def _check_m1_contracts() -> list[str]:
    llm = FakeLLMProvider()
    source = Tagged(
        payload={"hotspots": [{"topic": "早C晚A翻车", "mentions": 100, "evidence": ["a", "b"]}]},
        data_class=DataClass.C0_PUBLIC,
    )
    package = build_m1_hotspot_package(source, llm)
    failures = []
    if not isinstance(package, Tagged):
        failures.append("M1 输出必须是 Tagged")
    if package.data_class != DataClass.C1_INTERNAL:
        failures.append("M1 输出 data_class 必须是 C1_INTERNAL")
    action = build_publish_action(package.payload["brief"])
    if not isinstance(action, Action):
        failures.append("build_publish_action 必须返回 Action")
    if not action.idempotency_key:
        failures.append("Action 必须带 idempotency_key")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
