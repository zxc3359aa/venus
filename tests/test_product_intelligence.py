import pytest

from venus.product_intelligence import ProductIntelligenceConfig, build_product_intelligence_report


def _product_intel_payload():
    return {
        "source": "manual_product_dossier",
        "retrieved_at": "2026-06-14T16:00:00+08:00",
        "api_key": "secret-product-token",
        "live_connector_requested": True,
        "product": {
            "brand": "示例品牌",
            "name": "屏障修护精华",
            "filing_id": "国妆网备字20260001",
            "manufacturer": "示例化妆品有限公司",
            "category": "essence",
            "claims": ["舒缓", "100%修复屏障"],
            "brand_backing": [
                {"type": "dermatologist_quote", "source": "品牌手册", "status": "unverified"},
                {"type": "lab_collaboration", "source": "品牌发布会", "status": "verified"},
            ],
            "ingredients": [
                {
                    "name": "烟酰胺",
                    "role": "brightening",
                    "risk": "medium",
                    "supplier": "原料商A",
                    "coa": "coa-niacinamide-001",
                    "test_report": "test-niacinamide-001",
                },
                {
                    "name": "视黄醇",
                    "role": "renewal",
                    "risk": "high",
                    "supplier": "原料商B",
                    "coa": "",
                    "test_report": "",
                },
            ],
            "supplier_documents": [
                {"supplier": "原料商A", "document": "coa-niacinamide-001", "status": "provided"},
                {"supplier": "原料商B", "document": "", "status": "missing"},
            ],
            "test_reports": [
                {"report_id": "test-niacinamide-001", "scope": "烟酰胺纯度", "status": "provided"},
                {"report_id": "", "scope": "视黄醇稳定性", "status": "missing"},
            ],
            "controversies": [
                {"source": "douyin_comment", "issue": "用户反馈刺痛", "severity": "medium"},
                {"source": "creator_video", "issue": "达人质疑夸大修复", "severity": "high"},
            ],
            "evidence": [
                {"id": "nmpa-001", "type": "filing", "title": "备案查询"},
                {"id": "brand-001", "type": "brand", "title": "品牌手册"},
            ],
        },
    }


def test_build_product_intelligence_report_creates_precise_research_dossier():
    report = build_product_intelligence_report(_product_intel_payload())

    assert report["workflow"] == "product_intel"
    assert report["namespace"] == "venus_product_intel"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "brand_backing_count": 2,
        "unverified_brand_backing_count": 1,
        "ingredient_count": 2,
        "high_risk_ingredient_count": 1,
        "supplier_document_count": 2,
        "missing_supplier_document_count": 1,
        "test_report_count": 2,
        "missing_test_report_count": 1,
        "controversy_count": 2,
        "high_severity_controversy_count": 1,
        "forbidden_claim_count": 1,
        "retrieval_task_count": 5,
        "approval_gated_action_count": 2,
    }

    assert report["filing_check"]["status"] == "has_filing_id"
    assert report["filing_check"]["filing_id"] == "国妆网备字20260001"
    assert report["brand_backing"][0]["verification_state"] == "needs_verification"
    assert report["ingredient_matrix"][1]["name"] == "视黄醇"
    assert report["ingredient_matrix"][1]["risk_level"] == "high"
    assert report["supplier_document_checks"][1]["status"] == "missing"
    assert report["test_report_checks"][1]["status"] == "missing"
    assert report["controversy_scan"][1]["severity"] == "high"
    assert report["evidence"][0]["id"] == "nmpa-001"
    assert "100%修复屏障" in report["claim_risk"]["forbidden_claims"]
    assert report["claim_risk"]["risk_level"] == "high"
    assert {task["task_type"] for task in report["retrieval_plan"]} == {
        "brand_backing_verification",
        "ingredient_supplier_document",
        "ingredient_test_report",
        "controversy_followup",
        "live_connector_enablement",
    }
    assert all(task["execution_state"] == "blocked_until_approved" for task in report["retrieval_plan"])
    assert len(report["approval_records"]) == 2
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_product_live_connector",
        "venus_product_claim_review",
    }
    assert "secret-product-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_product_intelligence_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ProductIntelligenceConfig(namespace="xiaolongxia_product_intel")
