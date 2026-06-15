"""M6 微信小程序私域与企微引流离线核心包。

本模块只生成离线、可审阅的私域运营包；不调用小程序或企业微信真实 API。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from venus.contracts import Action, DataClass, Tagged


MEDICAL_RISK_TERMS = ("根治", "确诊", "处方", "用药方案", "激素脸诊断", "治疗方案")
FUNNEL_STAGES = ("visit", "qa_completed", "wecom_intent", "wecom_added", "purchase", "retained_7d")


def build_m6_private_domain_report(source: Tagged) -> Tagged:
    """生成 M6 小程序答疑、企微引流与私域漏斗离线报告。"""
    _reject_private_payload(source)
    payload = source.payload if isinstance(source.payload, dict) else {}

    consent = _build_pipl_consent(payload.get("consent") or {})
    answer = _build_answer_draft(str(payload.get("question") or "请描述你的护肤问题。"))
    lead_record = _build_lead_record(payload.get("lead") or {}, consent)
    funnel = _build_funnel_dashboard(payload.get("funnel_events") or [])
    wecom_handoff = _build_wecom_handoff(lead_record, consent)

    return Tagged(
        payload={
            "module": "m6_private_domain",
            "answer_draft": answer,
            "pipl_consent": consent,
            "lead_record": lead_record,
            "wecom_handoff": wecom_handoff,
            "funnel_dashboard": funnel,
            "safety_boundary": {
                "medical_boundary": "小程序答疑只做护肤教育与风险提示，不做医疗诊断、处方或治疗承诺。",
                "pipl_boundary": "收集线索前必须明示用途、范围、保存方式与撤回路径。",
            },
            "official_api_status": "no_platform_api_calls_pending_context7_verification",
            "external_actions": [],
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def validate_miniprogram_answer(text: str) -> list[str]:
    """校验小程序答疑是否越过医疗/广告法边界。"""
    issues: list[str] = []
    for term in MEDICAL_RISK_TERMS:
        if term in text:
            issues.append(f"小程序答疑含医疗或绝对化风险词：{term}")
    required_boundaries = ("不做医疗诊断", "线下就医")
    if not any(boundary in text for boundary in required_boundaries):
        issues.append("缺少医疗边界提示")
    if "企微" in text and "同意" not in text:
        issues.append("引导企微前缺少同意提示")
    return issues


def build_wecom_add_contact_action(*, lead_id: str, contact_ref: str) -> Action:
    """构造企微加客动作草稿，真实执行必须经 ApprovalGate。"""
    if not lead_id or not contact_ref:
        raise ValueError("企微加客动作需要 lead_id 与 contact_ref")
    return Action(
        kind="add_contact",
        summary=f"将已同意的私域线索 {lead_id} 引导加入企业微信",
        payload={
            "platform": "wecom",
            "lead_ref": lead_id,
            "contact_ref": contact_ref,
            "official_api_status": "pending_context7_verification",
            "requires_approval": True,
        },
        idempotency_key=f"add-contact-{lead_id}",
        data_class=DataClass.C1_INTERNAL,
        reversible=False,
    )


def _reject_private_payload(source: Tagged) -> None:
    if source.data_class == DataClass.C3_SECRET or source.pii:
        raise ValueError("M6 不接收 C3/PII 明文；请先在私有侧脱敏为 lead_hash 等 C1 描述。")


def _build_pipl_consent(consent: dict[str, Any]) -> dict[str, Any]:
    accepted = bool(consent.get("privacy_notice_accepted"))
    return {
        "status": "consented" if accepted else "blocked_pending_consent",
        "privacy_notice_accepted": accepted,
        "marketing_opt_in": bool(consent.get("marketing_opt_in")) if accepted else False,
        "requires_explicit_notice": True,
        "notice_items": [
            "收集目的：护肤问题答疑与企微服务承接",
            "收集范围：脱敏线索、肤质标签、问题分类、同意状态",
            "处理位置：默认境内化处理与加密备份",
            "用户权利：可撤回同意、导出或删除个人信息",
        ],
    }


def _build_answer_draft(question: str) -> str:
    risk_hint = "先暂停叠加刺激，观察屏障状态，再看产品成分和使用频率。"
    if any(word in question for word in ("烂", "激素", "过敏", "红肿", "刺痛")):
        risk_hint = "先停用高刺激叠加，记录泛红、刺痛、脱皮持续时间和近期用过的产品。"
    return (
        f"{risk_hint}"
        "我不能在小程序里给你做医疗诊断；如果持续红肿、渗出或疼痛，请及时线下就医。"
        "你可以补充肤质、产品名和使用频率；如同意隐私告知，我再把问题整理成企微服务单继续跟进。"
    )


def _build_lead_record(lead: dict[str, Any], consent: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = {
        "lead_hash": lead.get("lead_hash") or "anonymous-lead",
        "skin_type": lead.get("skin_type") or "unknown",
        "concerns": list(lead.get("concerns") or []),
        "consent": consent["status"],
    }
    return {
        "table": "venus_leads",
        "data_class": "C3_SECRET_AT_REST",
        "storage_policy": "strong_redaction_and_encrypted_domestic_storage",
        "stored_fields": ["lead_hash", "skin_type", "concerns", "consent"],
        "record": allowed_fields,
    }


def _build_wecom_handoff(lead_record: dict[str, Any], consent: dict[str, Any]) -> dict[str, Any]:
    if consent["status"] != "consented":
        return {
            "status": "blocked_pending_consent",
            "reason": "未获得明示隐私告知与加企微承接同意",
            "action_required": "展示隐私告知并等待用户主动同意",
        }
    lead_hash = lead_record["record"]["lead_hash"]
    return {
        "status": "draft_ready",
        "lead_ref": lead_hash,
        "welcome_message": "欢迎来企微，我会先按你的肤质、产品和频率做安全边界梳理，不做医疗诊断。",
        "sop_stage": "new_sensitive_skin_lead",
        "requires_approval_before_add_contact": True,
    }


def _build_funnel_dashboard(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_cohort: dict[str, dict[str, float]] = defaultdict(lambda: {stage: 0.0 for stage in FUNNEL_STAGES})
    for event in events:
        cohort = str(event.get("cohort") or "unknown")
        stage = str(event.get("stage") or "")
        if stage in FUNNEL_STAGES:
            by_cohort[cohort][stage] += float(event.get("count") or 0)
        by_cohort[cohort]["spend"] = by_cohort[cohort].get("spend", 0.0) + float(event.get("spend") or 0)
        by_cohort[cohort]["revenue"] = by_cohort[cohort].get("revenue", 0.0) + float(event.get("revenue") or 0)

    cohorts = [_summarize_cohort(cohort, values) for cohort, values in sorted(by_cohort.items())]
    return {
        "method": "cohort_conversion_retention_payback",
        "cohorts": cohorts,
        "metrics": [
            "visit_to_qa_rate",
            "qa_to_wecom_intent_rate",
            "wecom_intent_to_added_rate",
            "purchase_rate",
            "retention_7d_rate",
            "payback_days",
        ],
    }


def _summarize_cohort(cohort: str, values: dict[str, float]) -> dict[str, Any]:
    visits = values.get("visit", 0.0)
    qa = values.get("qa_completed", 0.0)
    intent = values.get("wecom_intent", 0.0)
    added = values.get("wecom_added", 0.0)
    purchase = values.get("purchase", 0.0)
    retained = values.get("retained_7d", 0.0)
    spend = values.get("spend", 0.0)
    revenue = values.get("revenue", 0.0)
    payback_days = None
    if revenue > 0 and spend > 0:
        payback_days = round(min(30.0, spend / revenue * 30.0), 2)
    return {
        "cohort": cohort,
        "visits": int(visits),
        "visit_to_qa_rate": _rate(qa, visits),
        "qa_to_wecom_intent_rate": _rate(intent, qa),
        "wecom_intent_to_added_rate": _rate(added, intent),
        "purchase_rate": _rate(purchase, visits),
        "retention_7d_rate": _rate(retained, added),
        "revenue": round(revenue, 2),
        "spend": round(spend, 2),
        "payback_days": payback_days,
    }


def _rate(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return round(num / den, 4)
