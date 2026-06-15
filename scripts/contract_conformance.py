"""维纳斯契约核对：确认实现仍以 contracts.py 为接口锚点。"""
from __future__ import annotations

from venus.approval import InMemoryApprovalGate
from venus.contracts import Action, ApprovalStatus, DataClass, LLMProvider, MemoryStore, Tagged
from venus.llm import FakeLLMProvider
from venus.modules.m1_hotspot import build_m1_hotspot_package, build_publish_action
from venus.modules.m2_product_diligence import build_m2_product_diligence_report
from venus.modules.m3_persona_memory import (
    InMemoryPersonaMemoryStore,
    build_m3_persona_learning_report,
    distill_persona_descriptor,
)


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_llm_provider())
    failures.extend(_check_approval_gate_shape())
    failures.extend(_check_m1_contracts())
    failures.extend(_check_m2_contracts())
    failures.extend(_check_m3_contracts())

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


def _check_m2_contracts() -> list[str]:
    source = Tagged(
        payload={
            "product_name": "契约核对精华",
            "nmpa": {"verified": False, "source": "manual-contract-check"},
            "ingredients": [{"name": "烟酰胺", "sources": ["ingredient-db"], "impact": 0.2}],
        },
        data_class=DataClass.C0_PUBLIC,
    )
    report = build_m2_product_diligence_report(source)
    failures = []
    if not isinstance(report, Tagged):
        failures.append("M2 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL:
        failures.append("M2 输出 data_class 必须是 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M2 不应产生对外动作")
    risk = report.payload.get("risk") or {}
    if risk.get("method") != "weighted_evidence_strength_times_impact":
        failures.append("M2 风险评分必须给透明方法")
    nmpa = report.payload.get("nmpa_verification") or {}
    if not nmpa.get("tier_c_blocked"):
        failures.append("M2 NMPA 边界必须保留 Tier 限制")
    return failures


def _check_m3_contracts() -> list[str]:
    store = InMemoryPersonaMemoryStore()
    source = Tagged(
        payload={
            "raw_corpus": ["私有原始语料只留本地"],
            "values": ["先证据后建议"],
            "tone": ["口语、克制"],
            "events": [
                {
                    "id": "contract-m3",
                    "kind": "episodic",
                    "content": "外部真实信号：证据型脚本互动更好",
                    "source": "external_metric:script",
                    "confidence": 0.8,
                }
            ],
        },
        data_class=DataClass.C3_SECRET,
        pii=True,
    )
    descriptor = distill_persona_descriptor(source)
    report = build_m3_persona_learning_report(source, store)
    failures = []
    if not isinstance(store, MemoryStore):
        failures.append("M3 记忆实现必须满足 MemoryStore")
    if not isinstance(descriptor, Tagged):
        failures.append("M3 风格描述符必须是 Tagged")
    if descriptor.data_class != DataClass.C1_INTERNAL or descriptor.pii:
        failures.append("M3 C3 蒸馏输出必须降级为无 PII 的 C1")
    if not isinstance(report, Tagged):
        failures.append("M3 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL:
        failures.append("M3 报告输出 data_class 必须是 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M3 不应产生对外动作")
    if report.payload.get("slow_layer_policy") != "core_identity_changes_require_approval":
        failures.append("M3 慢层核心身份变更必须人审")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
