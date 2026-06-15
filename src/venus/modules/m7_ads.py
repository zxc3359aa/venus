"""M7 千川投流与巨量星图离线决策包。

本模块只生成投放计划、复盘判断、星图接单建议和审批动作草稿；
不调用巨量引擎、千川或星图真实接口。
"""
from __future__ import annotations

from typing import Any

from venus.contracts import Action, DataClass, Tagged


AD_SCRIPT_BANNED_TERMS = ("根治", "100%", "第一", "最有效", "包好", "确诊", "处方")
DEFAULT_LEARNING_DAYS = 3


def build_m7_ads_report(source: Tagged) -> Tagged:
    """生成 M7 投流与星图离线报告。"""
    _reject_private_payload(source)
    payload = source.payload if isinstance(source.payload, dict) else {}
    objective = _normalize_objective(payload.get("objective") or {})
    ad_groups = [_summarize_ad_group(item, objective) for item in list(payload.get("ad_groups") or [])]
    xingtu_guidance = _build_xingtu_guidance(payload.get("xingtu_offer") or {}, str(payload.get("persona_descriptor") or ""))

    return Tagged(
        payload={
            "module": "m7_ads",
            "plan_id": str(payload.get("plan_id") or "m7-offline-plan"),
            "optimization_policy": {
                "objective": _objective_label(objective),
                "secondary_constraint": {
                    "roas_floor": objective["roas_floor"],
                    "cpa_ceiling": objective["cpa_ceiling"],
                    "budget_cap": objective["budget_cap"],
                },
                "exploration_method": "discounted_sliding_window_thompson_sampling",
                "attribution_window_days": objective["attribution_window_days"],
                "learning_phase_policy": "protect_before_attribution_matures",
                "stop_loss_policy": "only_after_learning_and_attribution_mature",
            },
            "media_plan": _build_media_plan(ad_groups, objective),
            "sequential_testing": _build_sequential_testing(list(payload.get("experiments") or [])),
            "xingtu_guidance": xingtu_guidance,
            "anomaly_alerts": _build_anomaly_alerts(ad_groups),
            "official_api_status": "no_platform_api_calls_pending_context7_verification",
            "external_actions": [],
            "safety_boundary": {
                "money_actions_require_approval": True,
                "xingtu_acceptance_requires_approval": True,
                "budget_hard_cap": objective["budget_cap"],
                "no_platform_connector_written": True,
            },
        },
        data_class=DataClass.C2_SENSITIVE,
        pii=False,
    )


def validate_ad_script(text: str) -> list[str]:
    """校验广告脚本是否踩绝对化或医疗化风险边界。"""
    issues: list[str] = []
    if not text.strip():
        issues.append("广告脚本为空")
    for term in AD_SCRIPT_BANNED_TERMS:
        if term in text:
            issues.append(f"广告脚本含高风险词：{term}")
    if "医疗诊断" not in text:
        issues.append("缺少不做医疗诊断的边界")
    if "不承诺" not in text and "不夸大" not in text:
        issues.append("缺少不夸大功效的边界")
    return issues


def build_campaign_approval_action(*, plan_id: str, budget: float, platform: str = "oceanengine") -> Action:
    """构造投放建计划动作草稿；花钱动作必须先经 ApprovalGate。"""
    if not plan_id:
        raise ValueError("投放审批动作需要 plan_id")
    if float(budget) <= 0:
        raise ValueError("投放审批动作需要正预算")
    return Action(
        kind="create_campaign",
        summary=f"按 M7 计划 {plan_id} 在 {platform} 创建投放，预算硬上限 {float(budget):.2f}",
        payload={
            "platform": platform,
            "plan_id": plan_id,
            "budget": round(float(budget), 2),
            "budget_guard": "hard_cap",
            "requires_approval": True,
            "official_api_status": "pending_context7_verification",
        },
        idempotency_key=f"create-campaign-{plan_id}",
        data_class=DataClass.C2_SENSITIVE,
        reversible=False,
    )


def build_xingtu_accept_order_action(*, order_id: str, quoted_fee: float) -> Action:
    """构造星图接单动作草稿；接单默认人审。"""
    if not order_id:
        raise ValueError("星图接单动作需要 order_id")
    if float(quoted_fee) <= 0:
        raise ValueError("星图接单动作需要正报价")
    return Action(
        kind="accept_xingtu_order",
        summary=f"接受星图订单 {order_id}，报价 {float(quoted_fee):.2f}",
        payload={
            "platform": "xingtu",
            "order_id": order_id,
            "quoted_fee": round(float(quoted_fee), 2),
            "requires_approval": True,
            "official_api_status": "pending_context7_verification",
        },
        idempotency_key=f"accept-xingtu-order-{order_id}",
        data_class=DataClass.C2_SENSITIVE,
        reversible=False,
    )


def _reject_private_payload(source: Tagged) -> None:
    if source.data_class == DataClass.C3_SECRET or source.pii:
        raise ValueError("M7 不接收 C3/PII；投放与星图分析只使用脱敏后的 C2/C1 数据。")


def _normalize_objective(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "primary": str(raw.get("primary") or "maximize_gmv"),
        "budget_cap": max(0.0, _float(raw.get("budget_cap"), default=0.0)),
        "roas_floor": max(0.0, _float(raw.get("roas_floor"), default=2.5)),
        "cpa_ceiling": max(0.0, _float(raw.get("cpa_ceiling"), default=999999.0)),
        "attribution_window_days": max(1, int(_float(raw.get("attribution_window_days"), default=3))),
    }


def _objective_label(objective: dict[str, Any]) -> str:
    if objective["primary"] == "maximize_roas":
        return "maximize_roas_under_gmv_constraint"
    return "maximize_gmv_under_roas_constraint"


def _summarize_ad_group(raw: dict[str, Any], objective: dict[str, Any]) -> dict[str, Any]:
    spend = _float(raw.get("spend"))
    gmv = _float(raw.get("gmv"))
    orders = _float(raw.get("orders"))
    impressions = _float(raw.get("impressions"))
    clicks = _float(raw.get("clicks"))
    stage = str(raw.get("stage") or "active")
    attribution_mature = bool(raw.get("attribution_mature"))
    learning_day = int(_float(raw.get("learning_day"), default=0))

    metrics = {
        "spend": round(spend, 2),
        "gmv": round(gmv, 2),
        "orders": int(orders),
        "roas": _rate(gmv, spend),
        "cpa": round(spend / orders, 2) if orders > 0 else None,
        "ctr": _rate(clicks, impressions),
        "cvr": _rate(orders, clicks),
        "cpm": round(spend / impressions * 1000, 2) if impressions > 0 else None,
        "aov": round(gmv / orders, 2) if orders > 0 else None,
    }
    decision, reasons, can_pause = _decision(stage, learning_day, attribution_mature, metrics, objective)
    proposed_budget = _proposed_budget(decision, spend, objective)

    return {
        "ad_group_id": str(raw.get("id") or raw.get("name") or "unknown-ad-group"),
        "name": str(raw.get("name") or raw.get("id") or "unknown-ad-group"),
        "stage": stage,
        "learning_day": learning_day,
        "attribution_mature": attribution_mature,
        "metrics": metrics,
        "decision": decision,
        "reasons": reasons,
        "can_pause_now": can_pause,
        "current_spend": round(spend, 2),
        "proposed_budget": proposed_budget,
        "guardrails": {
            "roas_floor": objective["roas_floor"],
            "cpa_ceiling": objective["cpa_ceiling"],
            "budget_hard_cap": objective["budget_cap"],
        },
    }


def _decision(
    stage: str,
    learning_day: int,
    attribution_mature: bool,
    metrics: dict[str, Any],
    objective: dict[str, Any],
) -> tuple[str, list[str], bool]:
    reasons: list[str] = []
    if stage == "learning" or learning_day < DEFAULT_LEARNING_DAYS:
        reasons.append("learning_phase")
    if not attribution_mature:
        reasons.append("attribution_not_mature")
    if reasons:
        return "protect_learning_phase", reasons, False

    roas = float(metrics["roas"])
    cpa = metrics["cpa"]
    if roas < objective["roas_floor"]:
        reasons.append("roas_guardrail_breach")
    if cpa is not None and cpa > objective["cpa_ceiling"]:
        reasons.append("cpa_guardrail_breach")
    if reasons:
        return "pause_requires_approval", reasons, True
    if roas >= objective["roas_floor"]:
        return "scale_with_guardrails", ["roas_constraint_satisfied"], False
    return "hold", ["insufficient_signal"], False


def _proposed_budget(decision: str, spend: float, objective: dict[str, Any]) -> float:
    if decision == "pause_requires_approval":
        return 0.0
    if decision == "scale_with_guardrails":
        target = spend * 1.2 if spend > 0 else min(100.0, objective["budget_cap"])
        return round(min(target, objective["budget_cap"] or target), 2)
    return round(spend, 2)


def _build_media_plan(ad_groups: list[dict[str, Any]], objective: dict[str, Any]) -> dict[str, Any]:
    total_proposed = round(sum(float(row["proposed_budget"]) for row in ad_groups), 2)
    return {
        "budget_cap": objective["budget_cap"],
        "total_proposed_budget": min(total_proposed, objective["budget_cap"]) if objective["budget_cap"] else total_proposed,
        "ad_group_decisions": ad_groups,
        "gmv_decomposition": "ROAS=GMV/spend; impressions->clicks(CTR)->orders(CVR)->AOV; bottlenecks use CPM/CTR/CVR/AOV",
    }


def _build_sequential_testing(experiments: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for raw in experiments:
        a = dict(raw.get("variant_a") or {})
        b = dict(raw.get("variant_b") or {})
        orders_a = _float(a.get("orders"))
        orders_b = _float(b.get("orders"))
        lift = _rate(orders_b - orders_a, max(orders_a, 1.0))
        rows.append(
            {
                "experiment_id": str(raw.get("id") or "unknown-experiment"),
                "predeclared_mde": _float(raw.get("mde"), default=0.15),
                "observed_lift": lift,
                "decision": "continue_collecting",
                "reason": "avoid_p_hacking_until_guardrails_and_mde_are_met",
            }
        )
    return {
        "method": "bayesian_sequential_with_predeclared_mde",
        "peek_policy": "no_continuous_peeking_decision_without_guardrails",
        "experiments": rows,
    }


def _build_xingtu_guidance(offer: dict[str, Any], persona_descriptor: str) -> dict[str, Any]:
    if not offer:
        return {"status": "no_offer", "method": "expected_value_minus_costs_risk_discounted"}

    fee = _float(offer.get("fee"))
    production_cost = _float(offer.get("production_cost"))
    opportunity_cost = _float(offer.get("opportunity_cost"))
    audience_match = _bounded(_float(offer.get("audience_match"), default=0.5))
    brand_safety = _bounded(_float(offer.get("brand_safety"), default=0.5))
    reputation_risk = _bounded(_float(offer.get("reputation_risk"), default=0.5))
    compliance_risk = _bounded(_float(offer.get("compliance_risk"), default=0.5))
    risk_discount = round(audience_match * brand_safety * (1 - reputation_risk) * (1 - compliance_risk), 4)
    expected_value = round((fee - production_cost - opportunity_cost) * risk_discount, 2)
    total_cost = production_cost + opportunity_cost
    floor = round(max(total_cost, fee * 0.35), 2)
    ceiling = round(max(fee, floor * 1.25), 2)

    recommendation = "reject"
    if expected_value >= total_cost and compliance_risk <= 0.2 and reputation_risk <= 0.25:
        recommendation = "accept_with_review"
    elif expected_value > 0:
        recommendation = "negotiate"

    script = _xingtu_script(offer, persona_descriptor)
    return {
        "status": "draft_ready",
        "method": "expected_value_minus_costs_risk_discounted",
        "order_id": str(offer.get("order_id") or "unknown-order"),
        "brand": str(offer.get("brand") or "unknown-brand"),
        "fee": round(fee, 2),
        "risk_discount": risk_discount,
        "expected_value": expected_value,
        "recommendation": recommendation,
        "quote_range": {"floor": floor, "ceiling": ceiling},
        "risk_factors": {
            "audience_match": audience_match,
            "brand_safety": brand_safety,
            "reputation_risk": reputation_risk,
            "compliance_risk": compliance_risk,
        },
        "script_draft": script,
        "script_validation_issues": validate_ad_script(script),
        "acceptance_requires_approval": True,
    }


def _xingtu_script(offer: dict[str, Any], persona_descriptor: str) -> str:
    brand = str(offer.get("brand") or "这个品牌")
    brief = str(offer.get("brief") or "围绕产品证据、适用肤质和使用边界表达。")
    tone = persona_descriptor.strip() or "口语、证据先行，不夸大功效。"
    return (
        f"{tone} 这条合作我会先把 {brand} 的适用人群和使用边界讲清楚，"
        f"再结合成分证据回应大家最关心的问题：{brief}"
        "全程不做医疗诊断，不夸大功效，最后引导观众按肤质和耐受情况理性选择。"
    )


def _build_anomaly_alerts(ad_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts = []
    for row in ad_groups:
        if row["decision"] == "pause_requires_approval":
            alerts.append(
                {
                    "ad_group_id": row["ad_group_id"],
                    "severity": "high",
                    "reason": ",".join(row["reasons"]),
                    "suggested_action": "pause_or_reduce_budget_after_approval",
                    "requires_human_review": True,
                }
            )
    return alerts


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rate(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return round(num / den, 4)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
