from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record
from venus.persona import build_persona_profile, rewrite_in_persona


SECRET_KEYS = {
    "secret",
    "token",
    "password",
    "app_secret",
    "authorization",
    "api_key",
    "access_token",
    "advertiser_id",
    "account_id",
}


@dataclass(frozen=True)
class CommercialStrategyConfig:
    namespace: str = "venus_commercial"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus commercial config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus commercial namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus commercial strategy connector must run in dry-run mode")


def build_commercial_strategy_report(
    payload: dict[str, Any],
    config: CommercialStrategyConfig | None = None,
) -> dict[str, Any]:
    active_config = config or CommercialStrategyConfig()
    safe_payload = _redact(payload)
    profile = build_persona_profile(
        list(safe_payload.get("persona_samples") or ["姐妹们，先看屏障状态，证据和体验都要说清楚。"])
    )

    qianchuan = dict(safe_payload.get("qianchuan") or {})
    xingtu = dict(safe_payload.get("xingtu") or {})
    qianchuan_recommendations = _build_qianchuan_recommendations(qianchuan)
    xingtu_reviews = _build_xingtu_reviews(xingtu)
    script_recommendations = _build_script_recommendations(qianchuan, xingtu, profile)
    approval_records = _build_approval_records(
        qianchuan_recommendations=qianchuan_recommendations,
        xingtu_reviews=xingtu_reviews,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "commercial",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_commercial_brief"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "Replace this local import with permissioned OceanEngine/Qianchuan and Xingtu APIs after credentials and approvals are configured.",
        },
        "summary": {
            "qianchuan_campaign_count": 1 if qianchuan else 0,
            "xingtu_brief_count": 1 if xingtu else 0,
            "high_risk_brief_count": sum(1 for review in xingtu_reviews if review["risk_level"] == "high"),
            "budget_recommendation_count": len(qianchuan_recommendations),
            "script_recommendation_count": len(script_recommendations),
            "approval_gated_action_count": len(approval_records),
        },
        "qianchuan_recommendations": qianchuan_recommendations,
        "xingtu_brief_reviews": xingtu_reviews,
        "commercial_script_recommendations": script_recommendations,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "Commercial strategy is read from local/manual briefs in this slice.",
                "No budget, campaign, audience, Xingtu task, brand commitment, or creator acceptance is executed.",
                "Ad spend and brand commitments require approval level 4.",
            ],
        },
    }


def _build_qianchuan_recommendations(qianchuan: dict[str, Any]) -> list[dict[str, Any]]:
    if not qianchuan:
        return []
    roi = _number(qianchuan.get("roi"))
    target_roi = _number(qianchuan.get("target_roi"))
    spent_today = _number(qianchuan.get("spent_today"))
    daily_budget = _number(qianchuan.get("daily_budget"))
    campaign_id = str(qianchuan.get("campaign_id") or "local-qianchuan-campaign")

    if target_roi and roi < target_roi:
        recommendation = (
            f"当前ROI {roi:g} 低于目标 {target_roi:g}，不要加预算；先把预算锁在"
            f"{int(daily_budget)}以内，复盘高完播素材和人群标签。"
        )
    elif spent_today > daily_budget * 0.8:
        recommendation = "今日消耗接近预算上限，先暂停扩大预算，只保留高转化素材观察。"
    else:
        recommendation = "预算可以维持观察，但新增预算前仍要人工确认ROI、素材疲劳和直播承接。"

    return [
        {
            "action_type": "qianchuan_budget_recommendation",
            "campaign_id": campaign_id,
            "objective": str(qianchuan.get("objective") or ""),
            "recommendation_type": "budget_guardrail",
            "approval_level": 4,
            "requires_manual_approval": True,
            "execution_state": "blocked_until_approved",
            "recommendation": recommendation,
            "audience_notes": _audience_notes(list(qianchuan.get("audiences") or [])),
            "creative_diagnostics": _creative_diagnostics(list(qianchuan.get("creatives") or [])),
            "external_action_enabled": False,
        }
    ]


def _build_xingtu_reviews(xingtu: dict[str, Any]) -> list[dict[str, Any]]:
    if not xingtu:
        return []
    forbidden_claims = list(xingtu.get("forbidden_claims") or [])
    requirements = list(xingtu.get("requirements") or [])
    risk_level = "high" if forbidden_claims or _has_absolute_claim(requirements) else "medium"
    return [
        {
            "action_type": "xingtu_brief_decision",
            "brief_id": str(xingtu.get("brief_id") or "local-xingtu-brief"),
            "brand": str(xingtu.get("brand") or ""),
            "product": str(xingtu.get("product") or ""),
            "budget": _number(xingtu.get("budget")),
            "risk_level": risk_level,
            "requirements": requirements,
            "forbidden_claims": forbidden_claims,
            "deliverables": list(xingtu.get("deliverables") or []),
            "approval_level": 4,
            "requires_manual_approval": True,
            "execution_state": "blocked_until_approved",
            "decision_guidance": _brief_guidance(risk_level, forbidden_claims),
            "external_action_enabled": False,
        }
    ]


def _build_script_recommendations(
    qianchuan: dict[str, Any],
    xingtu: dict[str, Any],
    profile: Any,
) -> list[dict[str, Any]]:
    product = str(xingtu.get("product") or "产品")
    top_creative = _top_creative(list(qianchuan.get("creatives") or []))
    base_hook = f"先看证据，再看{product}适不适合你的屏障状态。"
    return [
        {
            "script_type": "short_video_ad",
            "approval_level": 1,
            "hook": rewrite_in_persona(base_hook, profile),
            "angle": f"复用{top_creative}的高完播结构，开头抛出肤质差异，避免绝对功效承诺。",
            "cta": "评论区留下肤质和正在用的搭配，只做风险拆解，不承诺效果。",
        },
        {
            "script_type": "live_slice",
            "approval_level": 1,
            "hook": rewrite_in_persona("直播切片先回答争议，再给判断框架。", profile),
            "angle": "把品牌要求改写成证据、适用人群、禁忌场景三段，不口播夸大承诺。",
            "cta": "想让我帮你看搭配，先发肤质和使用频率。",
        },
    ]


def _build_approval_records(
    qianchuan_recommendations: list[dict[str, Any]],
    xingtu_reviews: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    for item in qianchuan_recommendations:
        records.append(
            create_approval_record(
                action_type=str(item["action_type"]),
                approval_level=int(item["approval_level"]),
                draft=str(item["recommendation"]),
                evidence_ids=[str(item["campaign_id"])],
                reviewer=reviewer,
                created_at=created_at,
            )
        )

    for item in xingtu_reviews:
        records.append(
            create_approval_record(
                action_type="xingtu_brief_decision",
                approval_level=4,
                draft=str(item["decision_guidance"]),
                evidence_ids=[str(item["brief_id"])],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
        records.append(
            create_approval_record(
                action_type="xingtu_brand_commitment",
                approval_level=4,
                draft="Any brand-facing acceptance, claim commitment, quote, or publishing promise requires explicit approval.",
                evidence_ids=[str(item["brief_id"])],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _audience_notes(audiences: list[Any]) -> list[str]:
    if not audiences:
        return ["No audience tags provided; keep spend paused until audience assumptions are reviewed."]
    return [f"优先观察{audience}人群的停留、评论质量和直播承接，不自动扩量。" for audience in audiences]


def _creative_diagnostics(creatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics = []
    for creative in creatives:
        completion_rate = _number(creative.get("completion_rate"))
        conversion_rate = _number(creative.get("conversion_rate"))
        status = "scale_candidate" if completion_rate >= 0.65 and conversion_rate >= 0.015 else "needs_rewrite"
        diagnostics.append(
            {
                "creative_id": str(creative.get("creative_id") or ""),
                "title": str(creative.get("title") or ""),
                "status": status,
                "note": "保留高完播结构" if status == "scale_candidate" else "先重写开头和承接，不加预算",
            }
        )
    return diagnostics


def _top_creative(creatives: list[dict[str, Any]]) -> str:
    if not creatives:
        return "当前最佳素材"
    ranked = sorted(
        creatives,
        key=lambda creative: (
            _number(creative.get("completion_rate")),
            _number(creative.get("conversion_rate")),
            _number(creative.get("ctr")),
        ),
        reverse=True,
    )
    return str(ranked[0].get("title") or ranked[0].get("creative_id") or "当前最佳素材")


def _brief_guidance(risk_level: str, forbidden_claims: list[Any]) -> str:
    if risk_level == "high":
        claims = "、".join(str(claim) for claim in forbidden_claims) or "绝对功效表达"
        return f"先要求品牌修改brief，移除或改写{claims}，再讨论报价、接单或脚本。"
    return "brief可以进入报价和脚本讨论，但仍需确认备案、证据、口播边界和评论区引导方式。"


def _has_absolute_claim(requirements: list[Any]) -> bool:
    markers = ["100%", "根治", "包治", "永久", "一定"]
    return any(any(marker in str(requirement) for marker in markers) for requirement in requirements)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
