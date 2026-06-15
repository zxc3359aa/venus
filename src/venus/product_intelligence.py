from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record
from venus.product_research import ABSOLUTE_CLAIM_MARKERS


SECRET_KEYS = {
    "secret",
    "token",
    "password",
    "app_secret",
    "authorization",
    "api_key",
    "openai_api_key",
    "access_token",
}


@dataclass(frozen=True)
class ProductIntelligenceConfig:
    namespace: str = "venus_product_intel"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus product intelligence config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus product intelligence namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus product intelligence workflow must run in dry-run mode")


def build_product_intelligence_report(
    payload: dict[str, Any],
    config: ProductIntelligenceConfig | None = None,
) -> dict[str, Any]:
    active_config = config or ProductIntelligenceConfig()
    safe_payload = _redact(payload)
    product = dict(safe_payload.get("product") or {})
    brand_backing = _build_brand_backing(product)
    filing_check = _build_filing_check(product)
    ingredient_matrix = _build_ingredient_matrix(product)
    supplier_checks = _build_supplier_checks(product)
    test_report_checks = _build_test_report_checks(product)
    controversy_scan = _build_controversy_scan(product)
    claim_risk = _build_claim_risk(product, ingredient_matrix, controversy_scan)
    retrieval_plan = _build_retrieval_plan(
        product=product,
        brand_backing=brand_backing,
        supplier_checks=supplier_checks,
        test_report_checks=test_report_checks,
        controversy_scan=controversy_scan,
        live_connector_requested=bool(safe_payload.get("live_connector_requested")),
    )
    approval_records = _build_approval_records(
        safe_payload=safe_payload,
        claim_risk=claim_risk,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "product_intel",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_product_dossier"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run dossier structures product evidence and retrieval tasks without live regulator, supplier, or social-platform reads.",
        },
        "summary": {
            "brand_backing_count": len(brand_backing),
            "unverified_brand_backing_count": sum(
                1 for item in brand_backing if item["verification_state"] == "needs_verification"
            ),
            "ingredient_count": len(ingredient_matrix),
            "high_risk_ingredient_count": sum(
                1 for item in ingredient_matrix if item["risk_level"] == "high"
            ),
            "supplier_document_count": len(supplier_checks),
            "missing_supplier_document_count": sum(
                1 for item in supplier_checks if item["status"] == "missing"
            ),
            "test_report_count": len(test_report_checks),
            "missing_test_report_count": sum(
                1 for item in test_report_checks if item["status"] == "missing"
            ),
            "controversy_count": len(controversy_scan),
            "high_severity_controversy_count": sum(
                1 for item in controversy_scan if item["severity"] == "high"
            ),
            "forbidden_claim_count": len(claim_risk["forbidden_claims"]),
            "retrieval_task_count": len(retrieval_plan),
            "approval_gated_action_count": len(approval_records),
        },
        "product_identity": {
            "brand": str(product.get("brand") or ""),
            "name": str(product.get("name") or ""),
            "manufacturer": str(product.get("manufacturer") or ""),
            "category": str(product.get("category") or ""),
        },
        "filing_check": filing_check,
        "brand_backing": brand_backing,
        "ingredient_matrix": ingredient_matrix,
        "supplier_document_checks": supplier_checks,
        "test_report_checks": test_report_checks,
        "controversy_scan": controversy_scan,
        "evidence": list(product.get("evidence") or []),
        "claim_risk": claim_risk,
        "retrieval_plan": retrieval_plan,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No NMPA query, supplier request, brand contact, crawler, social search, or file upload is executed in this slice.",
                "Claim-sensitive wording and live product-data connectors require manual approval.",
                "Outputs are research tasks and content-safety inputs until evidence is verified.",
            ],
        },
    }


def _build_brand_backing(product: dict[str, Any]) -> list[dict[str, Any]]:
    backing = []
    for index, item in enumerate(list(product.get("brand_backing") or []), start=1):
        status = str(item.get("status") or "unverified").lower()
        backing.append(
            {
                "backing_id": f"brand-backing-{index:03d}",
                "type": str(item.get("type") or "unknown"),
                "source": str(item.get("source") or ""),
                "status": status,
                "verification_state": "verified" if status == "verified" else "needs_verification",
                "evidence_note": "可作为背书素材" if status == "verified" else "需要查原始出处、授权和上下文",
            }
        )
    return backing


def _build_filing_check(product: dict[str, Any]) -> dict[str, Any]:
    filing_id = str(product.get("filing_id") or "")
    return {
        "status": "has_filing_id" if filing_id else "missing_filing_id",
        "filing_id": filing_id,
        "manufacturer": str(product.get("manufacturer") or ""),
        "verification_state": "needs_live_or_manual_verification",
        "retrieval_hint": "Use official filing source or imported filing evidence before making filing claims.",
    }


def _build_ingredient_matrix(product: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = []
    for index, item in enumerate(list(product.get("ingredients") or []), start=1):
        name = str(item.get("name") or item)
        risk_level = _risk_level(str(item.get("risk") or "medium"))
        matrix.append(
            {
                "ingredient_id": f"ingredient-{index:03d}",
                "name": name,
                "role": str(item.get("role") or "unknown"),
                "risk_level": risk_level,
                "supplier": str(item.get("supplier") or ""),
                "coa": str(item.get("coa") or ""),
                "test_report": str(item.get("test_report") or ""),
                "content_note": _ingredient_note(name, risk_level),
            }
        )
    return matrix


def _build_supplier_checks(product: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for index, item in enumerate(list(product.get("supplier_documents") or []), start=1):
        status = str(item.get("status") or "missing").lower()
        checks.append(
            {
                "check_id": f"supplier-doc-{index:03d}",
                "supplier": str(item.get("supplier") or ""),
                "document": str(item.get("document") or ""),
                "status": "provided" if status == "provided" and item.get("document") else "missing",
                "required_action": "archive_and_review" if status == "provided" and item.get("document") else "request_coa_or_supplier_document",
            }
        )
    return checks


def _build_test_report_checks(product: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for index, item in enumerate(list(product.get("test_reports") or []), start=1):
        status = str(item.get("status") or "missing").lower()
        report_id = str(item.get("report_id") or "")
        checks.append(
            {
                "check_id": f"test-report-{index:03d}",
                "report_id": report_id,
                "scope": str(item.get("scope") or ""),
                "status": "provided" if status == "provided" and report_id else "missing",
                "required_action": "review_test_scope_and_date" if status == "provided" and report_id else "request_or_verify_test_report",
            }
        )
    return checks


def _build_controversy_scan(product: dict[str, Any]) -> list[dict[str, Any]]:
    controversies = []
    for index, item in enumerate(list(product.get("controversies") or []), start=1):
        severity = _risk_level(str(item.get("severity") or "medium"))
        controversies.append(
            {
                "controversy_id": f"controversy-{index:03d}",
                "source": str(item.get("source") or "unknown"),
                "issue": str(item.get("issue") or item),
                "severity": severity,
                "content_boundary": "必须保留争议和个体差异，不能承诺修复或替用户诊断。",
            }
        )
    return controversies


def _build_claim_risk(
    product: dict[str, Any],
    ingredient_matrix: list[dict[str, Any]],
    controversy_scan: list[dict[str, Any]],
) -> dict[str, Any]:
    claims = [str(claim) for claim in list(product.get("claims") or [])]
    forbidden = [
        claim for claim in claims if any(marker in claim for marker in ABSOLUTE_CLAIM_MARKERS)
    ]
    has_high_ingredient = any(item["risk_level"] == "high" for item in ingredient_matrix)
    has_high_controversy = any(item["severity"] == "high" for item in controversy_scan)
    risk_level = "high" if forbidden or has_high_ingredient or has_high_controversy else "medium"
    if not forbidden and not has_high_ingredient and not has_high_controversy and product.get("filing_id"):
        risk_level = "low"
    return {
        "claims": claims,
        "forbidden_claims": forbidden,
        "risk_level": risk_level,
        "safe_claim_frame": "只说证据、备案、成分角色、适用场景和耐受边界，不承诺治疗或确定修复结果。",
    }


def _build_retrieval_plan(
    product: dict[str, Any],
    brand_backing: list[dict[str, Any]],
    supplier_checks: list[dict[str, Any]],
    test_report_checks: list[dict[str, Any]],
    controversy_scan: list[dict[str, Any]],
    live_connector_requested: bool,
) -> list[dict[str, Any]]:
    tasks = []
    if any(item["verification_state"] == "needs_verification" for item in brand_backing):
        tasks.append(_task("brand_backing_verification", "核验品牌背书原始出处、授权和上下文", [product_name(product)]))
    if any(item["status"] == "missing" for item in supplier_checks):
        tasks.append(_task("ingredient_supplier_document", "补齐缺失原料供应商文件或COA", [product_name(product)]))
    if any(item["status"] == "missing" for item in test_report_checks):
        tasks.append(_task("ingredient_test_report", "补齐缺失成分检测报告并核查检测范围", [product_name(product)]))
    if any(item["severity"] in {"medium", "high"} for item in controversy_scan):
        tasks.append(_task("controversy_followup", "追踪历史争议、达人质疑和用户反馈的来源证据", [product_name(product)]))
    if live_connector_requested:
        tasks.append(_task("live_connector_enablement", "启用备案、供应商文件和争议检索连接器前先做权限审查", [product_name(product)]))
    return tasks


def _task(task_type: str, description: str, evidence_ids: list[str]) -> dict[str, Any]:
    return {
        "task_type": task_type,
        "description": description,
        "approval_level": 2,
        "requires_manual_approval": True,
        "execution_state": "blocked_until_approved",
        "evidence_ids": evidence_ids,
        "external_action_enabled": False,
    }


def _build_approval_records(
    safe_payload: dict[str, Any],
    claim_risk: dict[str, Any],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    product = dict(safe_payload.get("product") or {})
    records = []
    if bool(safe_payload.get("live_connector_requested")):
        records.append(
            create_approval_record(
                action_type="venus_product_live_connector",
                approval_level=2,
                draft="Enable live product filing, supplier-document, test-report, and controversy retrieval only after credential and privacy review.",
                evidence_ids=[product_name(product)],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    if claim_risk["risk_level"] in {"medium", "high"}:
        records.append(
            create_approval_record(
                action_type="venus_product_claim_review",
                approval_level=2,
                draft=str(claim_risk["safe_claim_frame"]),
                evidence_ids=[product_name(product)],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def product_name(product: dict[str, Any]) -> str:
    return f"{product.get('brand', '')} {product.get('name', '')}".strip() or "product"


def _ingredient_note(name: str, risk_level: str) -> str:
    if risk_level == "high":
        return f"{name}需要强调耐受、使用频率、叠加禁忌和敏感肌风险。"
    return f"{name}需要结合浓度、配方体系和肤质场景表达。"


def _risk_level(value: str) -> str:
    lowered = value.lower()
    if lowered in {"high", "高", "severe"}:
        return "high"
    if lowered in {"low", "低"}:
        return "low"
    return "medium"


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
