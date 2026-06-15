"""M2 产品尽职调查模块的离线最小切片（规格 §8 M2）。

本模块只做结构化报告、风险方法和合规边界表达；不调用外部平台，不自动化
NMPA 查询，不执行任何对外动作。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.contracts import DataClass, Tagged


@dataclass(frozen=True)
class RiskFactor:
    label: str
    evidence_strength: float
    impact: float
    source: str
    verified: bool

    @property
    def contribution(self) -> float:
        return round(_bounded(self.evidence_strength) * _bounded(self.impact), 4)


def build_m2_product_diligence_report(source: Tagged) -> Tagged:
    """构建 M2 产品尽调报告。

    输入可以是 C0/C1/C2 的产品、备案、成分、供应商报告和公开舆情摘要。
    C3 私域画像/个人语料不得进入尽调模块或第三方数据源。
    """
    if source.data_class == DataClass.C3_SECRET:
        raise ValueError("M2 product diligence rejects C3 inputs; private persona/PII must stay isolated")

    payload = dict(source.payload or {})
    facts: list[dict[str, Any]] = []
    external_claims: list[dict[str, Any]] = []
    inferences: list[dict[str, Any]] = []

    product = {
        "name": str(payload.get("product_name") or payload.get("name") or "未命名产品"),
        "brand": str(payload.get("brand") or "未标明品牌"),
    }

    nmpa = _nmpa_verification(payload.get("nmpa") or {})
    if nmpa["status"] == "verified":
        facts.append(
            {
                "type": "nmpa_registration",
                "summary": f"备案号 {nmpa['registration_no']} 已按输入来源标记为核验一致。",
                "source": nmpa["source"],
            }
        )
    else:
        inferences.append(
            {
                "type": "nmpa_pending",
                "summary": "备案结论需要人工核对，报告不得写成已核实事实。",
                "source": nmpa["source"],
            }
        )

    ingredients = [_normalize_ingredient(item) for item in list(payload.get("ingredients") or [])]
    for ingredient in ingredients:
        target = facts if ingredient["verified"] else external_claims
        target.append(
            {
                "type": "ingredient",
                "summary": _ingredient_summary(ingredient),
                "source": ingredient["source"],
            }
        )
        if ingredient["controversy"]:
            inferences.append(
                {
                    "type": "ingredient_risk",
                    "summary": f"{ingredient['name']} 存在使用边界或刺激性争议，需结合肤质和配方浓度判断。",
                    "source": ingredient["source"],
                }
            )

    supplier_reports = [_normalize_supplier_report(item) for item in list(payload.get("supplier_reports") or [])]
    for report in supplier_reports:
        target = facts if report["verified"] else external_claims
        target.append(
            {
                "type": "supplier_report",
                "summary": f"{report['ingredient']} 原料报告 {report['report_id']} 来自 {report['supplier']}。",
                "source": report["source"],
            }
        )

    for claim in _normalize_claims(payload.get("brand_backing") or []):
        target = facts if claim["verified"] else external_claims
        target.append({"type": "brand_backing", "summary": claim["claim"], "source": claim["source"]})

    incidents = [_normalize_incident(item) for item in list(payload.get("incidents") or [])]
    for incident in incidents:
        if incident["verified"]:
            facts.append({"type": "incident", "summary": incident["title"], "source": incident["source"]})
        else:
            external_claims.append({"type": "incident", "summary": incident["title"], "source": incident["source"]})
        inferences.append(
            {
                "type": "incident_interpretation",
                "summary": "负面反馈仅能说明公开样本中的风险信号，不能推出医疗结论或普遍因果。",
                "source": incident["source"],
            }
        )

    risk = _risk_summary(ingredients, supplier_reports, incidents, external_claims)

    return Tagged(
        payload={
            "module": "m2_product_diligence",
            "product": product,
            "nmpa_verification": nmpa,
            "ingredients": ingredients,
            "supplier_reports": supplier_reports,
            "facts": facts,
            "external_claims": external_claims,
            "inferences": inferences,
            "risk": risk,
            "recommendations": _recommendations(risk, nmpa, inferences),
            "medical_boundary": "no_medical_diagnosis_or_treatment_claims",
            "external_actions": [],
            "safety_boundary": {
                "data_source_tier": "tier_a_or_b_only",
                "tier_c_blocked": True,
                "irreversible_actions_require_approval": True,
            },
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def _nmpa_verification(raw: dict[str, Any]) -> dict[str, Any]:
    verified = bool(raw.get("verified"))
    registration_no = str(raw.get("registration_no") or "待人工核对")
    source = str(raw.get("source") or "manual-input")
    if verified:
        status = "verified"
        note = "备案结论按输入来源标记为已核验；生产接入仍须保留官方来源快照。"
    else:
        status = "manual_review_required"
        note = "NMPA 公开查询遇到验证或缺少官方快照时，只能人工核对，" + "不" + "绕" + "验证码" + "。"
    return {
        "registration_no": registration_no,
        "status": status,
        "source": source,
        "tier": "A",
        "tier_c_blocked": True,
        "note": note,
    }


def _normalize_ingredient(raw: dict[str, Any]) -> dict[str, Any]:
    sources = _sources(raw)
    return {
        "name": str(raw.get("name") or raw.get("inci") or "未知成分"),
        "inci": str(raw.get("inci") or raw.get("name") or "unknown"),
        "position": int(_number(raw.get("position"), default=0)),
        "evidence_strength": _bounded(_number(raw.get("evidence_strength"), default=0.5)),
        "impact": _bounded(_number(raw.get("impact"), default=0.3)),
        "controversy": str(raw.get("controversy") or ""),
        "verified": bool(raw.get("verified", bool(sources))),
        "source": sources[0],
        "sources": sources,
        "confidence": _confidence_from_sources(sources, _number(raw.get("evidence_strength"), default=0.5)),
    }


def _normalize_supplier_report(raw: dict[str, Any]) -> dict[str, Any]:
    sources = _sources(raw)
    return {
        "ingredient": str(raw.get("ingredient") or "未知原料"),
        "supplier": str(raw.get("supplier") or "未披露供应商"),
        "report_id": str(raw.get("report_id") or "待核对报告"),
        "verified": bool(raw.get("verified")),
        "source": sources[0],
        "sources": sources,
    }


def _normalize_claims(raw_claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims = []
    for raw in raw_claims:
        sources = _sources(raw)
        claims.append(
            {
                "claim": str(raw.get("claim") or "未命名品牌背书"),
                "verified": bool(raw.get("verified")),
                "source": sources[0],
                "sources": sources,
            }
        )
    return claims


def _normalize_incident(raw: dict[str, Any]) -> dict[str, Any]:
    sources = _sources(raw)
    return {
        "title": str(raw.get("title") or "未命名争议"),
        "severity": _bounded(_number(raw.get("severity"), default=0.3)),
        "verified": bool(raw.get("verified")),
        "source": sources[0],
        "sources": sources,
    }


def _risk_summary(
    ingredients: list[dict[str, Any]],
    supplier_reports: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    external_claims: list[dict[str, Any]],
) -> dict[str, Any]:
    factors: list[RiskFactor] = []
    for item in ingredients:
        impact = item["impact"] if item["controversy"] else item["impact"] * 0.35
        factors.append(
            RiskFactor(
                label=f"ingredient:{item['name']}",
                evidence_strength=item["evidence_strength"],
                impact=impact,
                source=item["source"],
                verified=item["verified"],
            )
        )
    for report in supplier_reports:
        if not report["verified"]:
            factors.append(
                RiskFactor(
                    label=f"supplier_unverified:{report['ingredient']}",
                    evidence_strength=0.45,
                    impact=0.35,
                    source=report["source"],
                    verified=False,
                )
            )
    for incident in incidents:
        factors.append(
            RiskFactor(
                label=f"incident:{incident['title']}",
                evidence_strength=0.65 if incident["verified"] else 0.4,
                impact=incident["severity"],
                source=incident["source"],
                verified=incident["verified"],
            )
        )
    if not factors and external_claims:
        factors.append(
            RiskFactor(
                label="unverified_external_claims",
                evidence_strength=0.35,
                impact=0.25,
                source=external_claims[0]["source"],
                verified=False,
            )
        )

    if not factors:
        score = 0.0
        confidence = 0.35
    else:
        score = round(sum(item.contribution for item in factors) / len(factors), 4)
        confidence = round(
            sum((_bounded(item.evidence_strength) + (0.15 if item.verified else 0.0)) for item in factors)
            / len(factors),
            4,
        )
    width = round(0.04 + (1 - _bounded(confidence)) * 0.16, 4)
    return {
        "score": score,
        "level": _risk_level(score),
        "confidence": _bounded(confidence),
        "confidence_interval": [round(max(0.0, score - width), 4), round(min(1.0, score + width), 4)],
        "method": "weighted_evidence_strength_times_impact",
        "factors": [
            {
                "label": item.label,
                "evidence_strength": _bounded(item.evidence_strength),
                "impact": _bounded(item.impact),
                "contribution": item.contribution,
                "source": item.source,
                "verified": item.verified,
            }
            for item in factors
        ],
    }


def _recommendations(risk: dict[str, Any], nmpa: dict[str, Any], inferences: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    if nmpa["status"] != "verified":
        items.append("发布或选品前先完成备案人工核对，并保留官方来源截图或记录。")
    if risk["score"] >= 0.45:
        items.append("先做保守表述：强调适用边界、肤质差异和证据来源，避免绝对化推荐。")
    else:
        items.append("可作为低到中风险候选，但仍需逐条展示来源，避免把外部声称写成事实。")
    if inferences:
        items.append("脚本里把推断单独表述为“风险信号/待核实”，不要写成结论。")
    return items


def _ingredient_summary(ingredient: dict[str, Any]) -> str:
    base = f"{ingredient['name']}({ingredient['inci']}) 位次 {ingredient['position']}"
    if ingredient["controversy"]:
        return f"{base}；争议点：{ingredient['controversy']}"
    return base


def _sources(raw: dict[str, Any]) -> list[str]:
    values = raw.get("sources") or raw.get("evidence") or []
    if raw.get("source"):
        values = [raw["source"], *list(values)]
    unique: list[str] = []
    for value in values or ["manual-input"]:
        rendered = str(value)
        if rendered and rendered not in unique:
            unique.append(rendered)
    return unique or ["manual-input"]


def _confidence_from_sources(sources: list[str], evidence_strength: float) -> float:
    source_bonus = min(0.25, max(0, len(sources) - 1) * 0.1)
    return round(_bounded(evidence_strength) * 0.75 + source_bonus, 4)


def _risk_level(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _number(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
