from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record


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
class EcommerceConfig:
    namespace: str = "venus_ecommerce"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus ecommerce config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus ecommerce namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus ecommerce workflow must run in dry-run mode")


def build_ecommerce_report(
    payload: dict[str, Any],
    config: EcommerceConfig | None = None,
) -> dict[str, Any]:
    active_config = config or EcommerceConfig()
    safe_payload = _redact(payload)
    products = [dict(item) for item in list(safe_payload.get("products") or [])]
    live_rooms = [dict(item) for item in list(safe_payload.get("live_rooms") or [])]
    promotions = [dict(item) for item in list(safe_payload.get("promotions") or [])]
    after_sales = [dict(item) for item in list(safe_payload.get("after_sales") or [])]

    catalog_checks = _build_catalog_checks(products)
    inventory_alerts = _build_inventory_alerts(products)
    pricing_recommendations = _build_pricing_recommendations(promotions, products)
    live_product_card_plan = _build_live_product_card_plan(live_rooms, catalog_checks)
    after_sales_watchlist = _build_after_sales_watchlist(after_sales)
    conversion_recommendations = _build_conversion_recommendations(
        catalog_checks=catalog_checks,
        inventory_alerts=inventory_alerts,
        live_product_card_plan=live_product_card_plan,
        after_sales_watchlist=after_sales_watchlist,
    )
    approval_records = _build_approval_records(
        safe_payload=safe_payload,
        live_product_card_plan=live_product_card_plan,
        pricing_recommendations=pricing_recommendations,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "ecommerce",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_douyin_shop_export"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run report analyzes local/imported ecommerce signals without changing shop, product card, order, price, or promotion state.",
        },
        "summary": {
            "product_count": len(catalog_checks),
            "low_stock_count": len(inventory_alerts),
            "high_return_product_count": sum(
                1 for item in catalog_checks if item["return_risk"] == "high"
            ),
            "live_room_count": len(live_rooms),
            "promotion_count": len(promotions),
            "after_sales_issue_count": len(after_sales_watchlist),
            "conversion_recommendation_count": len(conversion_recommendations),
            "approval_gated_action_count": len(approval_records),
        },
        "shop": dict(safe_payload.get("shop") or {}),
        "catalog_checks": catalog_checks,
        "inventory_alerts": inventory_alerts,
        "pricing_recommendations": pricing_recommendations,
        "live_product_card_plan": live_product_card_plan,
        "after_sales_watchlist": after_sales_watchlist,
        "conversion_recommendations": conversion_recommendations,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No Douyin Shop product card, price, coupon, inventory, order, refund, or after-sales state is changed.",
                "Live ecommerce connectors, product-card changes, and promotion or price changes require manual approval.",
                "Outputs are internal recommendations until shop credentials, audit logs, and rollback controls are configured.",
            ],
        },
    }


def _build_catalog_checks(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = []
    for product in products:
        conversion_rate = _number(product.get("conversion_rate"))
        return_rate = _number(product.get("return_rate"))
        checks.append(
            {
                "product_id": str(product.get("product_id") or ""),
                "title": str(product.get("title") or ""),
                "price": _number(product.get("price")),
                "sale_price": _number(product.get("sale_price")),
                "stock": int(_number(product.get("stock"))),
                "target_stock": int(_number(product.get("target_stock"))),
                "margin_rate": _number(product.get("margin_rate")),
                "commission_rate": _number(product.get("commission_rate")),
                "conversion_rate": conversion_rate,
                "return_rate": return_rate,
                "claim_risk": _risk_level(str(product.get("claim_risk") or "medium")),
                "return_risk": "high" if return_rate >= 0.15 else "normal",
                "evidence_ids": [str(item) for item in list(product.get("evidence") or [])],
                "content_boundary": "商品卖点必须回到证据、肤质、耐受和售后风险，不能承诺修复结果。",
            }
        )
    return checks


def _build_inventory_alerts(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts = []
    for product in products:
        stock = int(_number(product.get("stock")))
        target_stock = int(_number(product.get("target_stock")))
        if target_stock and stock < target_stock * 0.5:
            alerts.append(
                {
                    "product_id": str(product.get("product_id") or ""),
                    "title": str(product.get("title") or ""),
                    "stock": stock,
                    "target_stock": target_stock,
                    "status": "low_stock",
                    "recommendation": "直播挂品前先确认补货节奏，避免高转化素材带来缺货和售后压力。",
                }
            )
    return alerts


def _build_pricing_recommendations(
    promotions: list[dict[str, Any]],
    products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(product.get("product_id") or ""): product for product in products}
    recommendations = []
    for item in promotions:
        product_id = str(item.get("product_id") or "")
        product = by_id.get(product_id, {})
        recommendations.append(
            {
                "promotion_id": str(item.get("promotion_id") or "local-promo"),
                "product_id": product_id,
                "type": str(item.get("type") or ""),
                "discount": _number(item.get("discount")),
                "budget": _number(item.get("budget")),
                "margin_rate": _number(product.get("margin_rate")),
                "recommendation": "优惠可以作为直播转化钩子，但改价、券包和预算必须人工确认毛利和售后承接。",
                "approval_level": 4,
                "requires_manual_approval": True,
                "execution_state": "blocked_until_approved",
                "external_action_enabled": False,
            }
        )
    return recommendations


def _build_live_product_card_plan(
    live_rooms: list[dict[str, Any]],
    catalog_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {item["product_id"]: item for item in catalog_checks}
    plans = []
    for room in live_rooms:
        planned = [str(item) for item in list(room.get("planned_products") or [])]
        ordered = sorted(
            [by_id[item] for item in planned if item in by_id],
            key=lambda item: (item["claim_risk"] == "high", item["conversion_rate"]),
            reverse=True,
        )
        plans.append(
            {
                "session_id": str(room.get("session_id") or "local-live"),
                "title": str(room.get("title") or ""),
                "planned_products": planned,
                "recommended_product_order": [item["product_id"] for item in ordered],
                "product_card_click_rate": _number(room.get("product_card_click_rate")),
                "conversion_rate": _number(room.get("conversion_rate")),
                "guidance": "先讲低争议利益点，再承接高风险成分/功效问题，商品卡顺序需人工确认。",
                "approval_level": 3,
                "requires_manual_approval": True,
                "execution_state": "blocked_until_approved",
                "external_action_enabled": False,
            }
        )
    return plans


def _build_after_sales_watchlist(after_sales: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "product_id": str(item.get("product_id") or ""),
            "issue": str(item.get("issue") or ""),
            "severity": _risk_level(str(item.get("severity") or "medium")),
            "reply_boundary": "售后问题先确认使用频率、肤质、订单状态和平台规则，不做医疗诊断或效果承诺。",
        }
        for item in after_sales
    ]


def _build_conversion_recommendations(
    catalog_checks: list[dict[str, Any]],
    inventory_alerts: list[dict[str, Any]],
    live_product_card_plan: list[dict[str, Any]],
    after_sales_watchlist: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recommendations = [
        {
            "recommendation_type": "product_card_order",
            "recommendation": "直播商品卡先放库存和毛利可承接、争议较低的商品；高争议商品需要先讲清适用人群和售后边界。",
        },
        {
            "recommendation_type": "comment_to_cart",
            "recommendation": "评论区引导用户留下肤质和当前搭配，再把合适商品作为备选，不直接承诺效果。",
        },
        {
            "recommendation_type": "after_sales_guardrail",
            "recommendation": "高退货或高售后商品在直播口播前必须补充禁忌、耐受和客服承接话术。",
        },
    ]
    if inventory_alerts:
        recommendations[0]["inventory_note"] = "存在低库存商品，放大投流或直播主推前先确认补货。"
    if live_product_card_plan:
        recommendations[0]["live_session_count"] = len(live_product_card_plan)
    if any(item["severity"] == "high" for item in after_sales_watchlist):
        recommendations[2]["priority"] = "high"
    if any(item["claim_risk"] == "high" for item in catalog_checks):
        recommendations[1]["claim_note"] = "存在高宣称风险商品，转化话术必须克制。"
    return recommendations


def _build_approval_records(
    safe_payload: dict[str, Any],
    live_product_card_plan: list[dict[str, Any]],
    pricing_recommendations: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    if bool(safe_payload.get("live_connector_requested")):
        records.append(
            create_approval_record(
                action_type="venus_ecommerce_live_connector",
                approval_level=2,
                draft="Enable Douyin ecommerce connector only after shop credential, order privacy, rate-limit, and rollback review.",
                evidence_ids=[str(safe_payload.get("shop", {}).get("shop_id") or "local-shop")],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    if live_product_card_plan:
        records.append(
            create_approval_record(
                action_type="venus_product_card_update",
                approval_level=3,
                draft="Review live product-card order and talking points before changing any live room product card.",
                evidence_ids=[str(item["session_id"]) for item in live_product_card_plan],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    if pricing_recommendations:
        records.append(
            create_approval_record(
                action_type="venus_promotion_or_price_change",
                approval_level=4,
                draft="Review coupon, price, budget, margin, inventory, and after-sales capacity before changing promotion state.",
                evidence_ids=[str(item["promotion_id"]) for item in pricing_recommendations],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


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


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
