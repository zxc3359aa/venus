from __future__ import annotations

from typing import Any

ABSOLUTE_CLAIM_MARKERS = ["100%", "根治", "包治", "永久", "一定"]


def build_product_research_card(product: dict[str, Any]) -> dict[str, Any]:
    brand = product.get("brand", "").strip()
    name = product.get("name", "").strip()
    filing_id = product.get("filing_id", "").strip()
    ingredients = list(product.get("ingredients", []))
    claims = list(product.get("claims", []))
    controversies = list(product.get("controversies", []))
    supplier_docs = list(product.get("supplier_docs", []))
    evidence = list(product.get("evidence", []))

    forbidden_claims = [
        claim
        for claim in claims
        if any(marker in claim for marker in ABSOLUTE_CLAIM_MARKERS)
    ]
    risk_level = "high" if forbidden_claims or controversies else "medium"
    if filing_id and not forbidden_claims and not controversies:
        risk_level = "low"

    safe_talking_points = [
        "可以说支持屏障护理，但不要承诺修复结果",
        "把成分作用、适合人群和可能不耐受情况分开讲",
        "涉及功效宣称时提醒以备案、检测和个人耐受为准",
    ]

    return {
        "product": f"{brand} {name}".strip(),
        "risk_level": risk_level,
        "sections": {
            "filing": {
                "status": "has_filing_id" if filing_id else "missing_filing_id",
                "filing_id": filing_id,
            },
            "ingredients": {
                "items": ingredients,
                "notes": ["需要结合浓度、配方体系和使用场景判断"],
            },
            "claims": {
                "items": claims,
                "forbidden": forbidden_claims,
            },
            "supplier_testing": {
                "documents": supplier_docs,
                "status": "provided" if supplier_docs else "missing",
            },
            "controversy": {
                "items": controversies,
                "status": "has_controversy" if controversies else "none_recorded",
            },
        },
        "evidence": evidence,
        "safe_talking_points": safe_talking_points,
        "forbidden_claims": forbidden_claims,
    }
