import pytest

from venus.ecommerce import EcommerceConfig, build_ecommerce_report


def _ecommerce_payload():
    return {
        "source": "manual_douyin_shop_export",
        "retrieved_at": "2026-06-14T17:00:00+08:00",
        "access_token": "secret-ecommerce-token",
        "live_connector_requested": True,
        "shop": {
            "shop_id": "shop-001",
            "name": "维纳斯护肤小店",
            "channel": "douyin_shop",
        },
        "products": [
            {
                "product_id": "sku-001",
                "title": "屏障修护精华",
                "price": 199,
                "sale_price": 169,
                "stock": 36,
                "target_stock": 120,
                "margin_rate": 0.42,
                "commission_rate": 0.18,
                "conversion_rate": 0.032,
                "return_rate": 0.06,
                "claim_risk": "high",
                "evidence": ["shop-product-001"],
            },
            {
                "product_id": "sku-002",
                "title": "温和洁面",
                "price": 89,
                "sale_price": 79,
                "stock": 320,
                "target_stock": 80,
                "margin_rate": 0.35,
                "commission_rate": 0.12,
                "conversion_rate": 0.018,
                "return_rate": 0.18,
                "claim_risk": "medium",
                "evidence": ["shop-product-002"],
            },
        ],
        "live_rooms": [
            {
                "session_id": "live-001",
                "title": "屏障护理专场",
                "planned_products": ["sku-001", "sku-002"],
                "viewers": 18000,
                "gmv": 128000,
                "product_card_click_rate": 0.21,
                "conversion_rate": 0.026,
            }
        ],
        "promotions": [
            {
                "promotion_id": "promo-001",
                "product_id": "sku-001",
                "type": "coupon",
                "discount": 30,
                "budget": 3000,
            }
        ],
        "after_sales": [
            {"product_id": "sku-001", "issue": "敏感肌刺痛咨询", "severity": "medium"},
            {"product_id": "sku-002", "issue": "退货率偏高", "severity": "high"},
        ],
    }


def test_build_ecommerce_report_creates_shop_product_live_and_after_sales_plan():
    report = build_ecommerce_report(_ecommerce_payload())

    assert report["workflow"] == "ecommerce"
    assert report["namespace"] == "venus_ecommerce"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "product_count": 2,
        "low_stock_count": 1,
        "high_return_product_count": 1,
        "live_room_count": 1,
        "promotion_count": 1,
        "after_sales_issue_count": 2,
        "conversion_recommendation_count": 3,
        "approval_gated_action_count": 3,
    }

    assert report["shop"]["shop_id"] == "shop-001"
    assert report["catalog_checks"][0]["product_id"] == "sku-001"
    assert report["catalog_checks"][0]["claim_risk"] == "high"
    assert report["inventory_alerts"][0]["product_id"] == "sku-001"
    assert report["inventory_alerts"][0]["status"] == "low_stock"
    assert report["pricing_recommendations"][0]["promotion_id"] == "promo-001"
    assert report["pricing_recommendations"][0]["execution_state"] == "blocked_until_approved"
    assert report["live_product_card_plan"][0]["session_id"] == "live-001"
    assert report["live_product_card_plan"][0]["execution_state"] == "blocked_until_approved"
    assert report["after_sales_watchlist"][1]["severity"] == "high"
    assert report["conversion_recommendations"][0]["recommendation_type"] == "product_card_order"
    assert len(report["approval_records"]) == 3
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_ecommerce_live_connector",
        "venus_product_card_update",
        "venus_promotion_or_price_change",
    }
    assert "secret-ecommerce-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_ecommerce_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        EcommerceConfig(namespace="xiaolongxia_ecommerce")
