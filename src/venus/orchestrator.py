from __future__ import annotations

from typing import Any

from venus.action_outbox import build_action_outbox
from venus.agent_run import build_agent_run_plan
from venus.approval_archive import build_approval_archive
from venus.approval_inbox import build_approval_inbox
from venus.approval_ledger import build_approval_ledger
from venus.airtable_export import build_airtable_sync_package
from venus.comments import analyze_comments
from venus.commercial_strategy import build_commercial_strategy_report
from venus.content_eval import build_content_eval_report
from venus.connector_audit import build_connector_audit_report
from venus.content import generate_hotspot_brief
from venus.delivery_drafts import build_delivery_drafts
from venus.delivery_status import build_delivery_status
from venus.douyin_engagement import build_douyin_engagement_report
from venus.ecommerce import build_ecommerce_report
from venus.evals import build_eval_report
from venus.memory import build_memory_report
from venus.monitoring import build_monitoring_report
from venus.persona import build_persona_profile
from venus.performance import build_performance_report
from venus.product_intelligence import build_product_intelligence_report
from venus.product_research import build_product_research_card
from venus.scheduler import build_scheduler_plan
from venus.self_improvement import build_self_improvement_report
from venus.trend_scan import build_trend_scan_report
from venus.video_production import build_video_production_package
from venus.wechat_private_domain import build_wechat_private_domain_report


class VenusOrchestrator:
    def run(self, workflow: str, payload: dict[str, Any]) -> dict[str, Any]:
        persona_samples = payload.get(
            "persona_samples",
            ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        )
        profile = build_persona_profile(list(persona_samples))

        if workflow == "hotspot":
            result = generate_hotspot_brief(list(payload["hotspots"]), profile)
        elif workflow == "product":
            products = list(payload["products"])
            result = build_product_research_card(products[0])
        elif workflow == "product_intel":
            result = build_product_intelligence_report(payload)
        elif workflow == "comments":
            result = analyze_comments(list(payload["comments"]), profile)
        elif workflow == "monitoring":
            result = build_monitoring_report(payload)
        elif workflow == "airtable":
            result = build_airtable_sync_package(payload)
        elif workflow == "approvals":
            result = build_approval_inbox(payload)
        elif workflow == "approval_ledger":
            result = build_approval_ledger(payload)
        elif workflow == "approval_archive":
            result = build_approval_archive(payload)
        elif workflow == "action_outbox":
            result = build_action_outbox(payload)
        elif workflow == "delivery_drafts":
            result = build_delivery_drafts(payload)
        elif workflow == "delivery_status":
            result = build_delivery_status(payload)
        elif workflow == "connectors":
            result = build_connector_audit_report(payload)
        elif workflow == "agent_run":
            result = build_agent_run_plan(payload)
        elif workflow == "douyin":
            result = build_douyin_engagement_report(payload)
        elif workflow == "ecommerce":
            result = build_ecommerce_report(payload)
        elif workflow == "evals":
            result = build_eval_report(payload)
        elif workflow == "memory":
            result = build_memory_report(payload)
        elif workflow == "scheduler":
            result = build_scheduler_plan(payload)
        elif workflow == "wechat":
            result = build_wechat_private_domain_report(payload)
        elif workflow == "commercial":
            result = build_commercial_strategy_report(payload)
        elif workflow == "improvement":
            result = build_self_improvement_report(payload)
        elif workflow == "production":
            result = build_video_production_package(payload)
        elif workflow == "content_eval":
            result = build_content_eval_report(payload)
        elif workflow == "performance":
            result = build_performance_report(payload)
        elif workflow == "trend_scan":
            result = build_trend_scan_report(payload)
        else:
            raise ValueError(f"Unsupported Venus workflow: {workflow}")

        return {
            "workflow": workflow,
            "approval_mode": "manual",
            "external_actions": [],
            "result": result,
        }
