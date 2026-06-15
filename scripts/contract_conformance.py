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
from venus.modules.m4_community import build_m4_community_report, build_reply_action
from venus.modules.m5_video_editing import build_m5_video_package, build_video_publish_action
from venus.modules.m6_private_domain import (
    build_m6_private_domain_report,
    build_wecom_add_contact_action,
)


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_llm_provider())
    failures.extend(_check_approval_gate_shape())
    failures.extend(_check_m1_contracts())
    failures.extend(_check_m2_contracts())
    failures.extend(_check_m3_contracts())
    failures.extend(_check_m4_contracts())
    failures.extend(_check_m5_contracts())
    failures.extend(_check_m6_contracts())

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


def _check_m4_contracts() -> list[str]:
    source = Tagged(
        payload={
            "video_id": "contract-video",
            "comments": [
                {"id": "c1", "text": "敏感肌叠加刺痛怎么办", "like_count": 3},
                {"id": "c2", "text": "视黄醇和酸能不能一起用", "like_count": 2},
            ],
            "live_mode": True,
            "auto_send_barrage": True,
        },
        data_class=DataClass.C1_INTERNAL,
    )
    report = build_m4_community_report(source)
    action = build_reply_action(video_id="contract-video", comment_id="c1", draft=report.payload["reply_drafts"][0]["draft"])
    failures = []
    if not isinstance(report, Tagged):
        failures.append("M4 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL or report.pii:
        failures.append("M4 输出必须是无 PII 的 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M4 报告不应直接产生外部动作")
    if not isinstance(action, Action):
        failures.append("M4 回复动作必须是 Action")
    if action.kind != "reply_comment" or not action.idempotency_key:
        failures.append("M4 回复 Action 必须带 reply_comment 与 idempotency_key")
    if action.reversible:
        failures.append("M4 公开回复动作必须标为不可逆")
    live = report.payload.get("live_assist") or {}
    if not live.get("auto_send_blocked") or not live.get("tier_c_blocked"):
        failures.append("M4 必须阻止非官方弹幕自动发送")
    return failures


def _check_m5_contracts() -> list[str]:
    source = Tagged(
        payload={
            "script": {
                "topic": "契约核对短视频",
                "full_text": "千万别急着跟风，先看屏障状态。评论区留下肤质和产品名，关注我少踩坑。",
            },
            "assets": [{"id": "asset-1", "type": "video", "uri": "local://asset.mp4", "license": "owned", "authorized": True}],
        },
        data_class=DataClass.C1_INTERNAL,
    )
    package = build_m5_video_package(source)
    action = build_video_publish_action(project_id=package.payload["project_id"], platform="douyin")
    failures = []
    if not isinstance(package, Tagged):
        failures.append("M5 输出必须是 Tagged")
    if package.data_class != DataClass.C1_INTERNAL or package.pii:
        failures.append("M5 输出必须是无 PII 的 C1_INTERNAL")
    if package.payload.get("external_actions") != []:
        failures.append("M5 工程包不应直接产生外部动作")
    if (package.payload.get("authorization_gate") or {}).get("status") != "passed":
        failures.append("M5 必须通过素材授权门禁")
    if not package.payload.get("editable_project"):
        failures.append("M5 必须生成可编辑工程描述")
    if not isinstance(action, Action):
        failures.append("M5 发布动作必须是 Action")
    if action.kind != "publish_video" or not action.idempotency_key:
        failures.append("M5 发布 Action 必须带 publish_video 与 idempotency_key")
    if action.reversible:
        failures.append("M5 发布动作必须标为不可逆")
    return failures


def _check_m6_contracts() -> list[str]:
    source = Tagged(
        payload={
            "question": "契约核对：敏感肌早C晚A刺痛怎么办？",
            "consent": {"privacy_notice_accepted": True},
            "lead": {"lead_hash": "contract-lead", "skin_type": "sensitive"},
        },
        data_class=DataClass.C1_INTERNAL,
    )
    try:
        report = build_m6_private_domain_report(source)
        action = build_wecom_add_contact_action(lead_id="contract-lead", contact_ref="wecom-ref")
    except NotImplementedError:
        return ["M6 私域模块尚未实现"]

    failures = []
    if not isinstance(report, Tagged):
        failures.append("M6 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL or report.pii:
        failures.append("M6 输出必须是无 PII 的 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M6 报告不应直接产生外部动作")
    consent = report.payload.get("pipl_consent") or {}
    if not consent.get("requires_explicit_notice"):
        failures.append("M6 必须声明 PIPL 明示告知与同意")
    funnel = report.payload.get("funnel_dashboard") or {}
    if funnel.get("method") != "cohort_conversion_retention_payback":
        failures.append("M6 漏斗必须使用 cohort + 留存 + 回本周期方法")
    if not isinstance(action, Action):
        failures.append("M6 企微加客动作必须是 Action")
    if action.kind != "add_contact" or not action.idempotency_key:
        failures.append("M6 企微 Action 必须带 add_contact 与 idempotency_key")
    if action.reversible:
        failures.append("M6 加客户动作必须标为不可逆")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
