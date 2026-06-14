from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval
from venus.airtable_export import build_airtable_sync_package
from venus.comments import analyze_comments
from venus.commercial_strategy import build_commercial_strategy_report
from venus.content import generate_hotspot_brief
from venus.douyin_engagement import build_douyin_engagement_report
from venus.monitoring import build_monitoring_report
from venus.persona import build_persona_profile
from venus.product_research import build_product_research_card
from venus.wechat_private_domain import build_wechat_private_domain_report


SECRET_KEYS = {
    "secret",
    "token",
    "password",
    "app_secret",
    "authorization",
    "api_key",
    "openai_api_key",
}

SURFACE_ACTIONS = {
    "feishu_mobile_report": {
        "approval_level": 2,
        "title": "Send private Feishu mobile report",
        "draft": "Prepare a Feishu card-ready Venus run summary for private review.",
        "surface": "feishu",
    },
    "airtable_sync_review": {
        "approval_level": 2,
        "title": "Review Airtable operations sync",
        "draft": "Prepare Airtable-ready records for human review before any base write.",
        "surface": "airtable",
    },
    "douyin_comment_reply_queue": {
        "approval_level": 3,
        "title": "Queue Douyin comment reply drafts",
        "draft": "Prepare high-risk Douyin reply drafts, but do not publish without approval.",
        "surface": "douyin",
    },
    "qianchuan_budget_review": {
        "approval_level": 4,
        "title": "Review Qianchuan budget recommendation",
        "draft": "Prepare budget and audience recommendations without changing spend.",
        "surface": "qianchuan",
    },
    "xingtu_brief_response": {
        "approval_level": 4,
        "title": "Review Xingtu brand brief response",
        "draft": "Prepare commercial brief guidance without accepting or rejecting tasks.",
        "surface": "xingtu",
    },
    "wechat_private_domain_handoff": {
        "approval_level": 4,
        "title": "Review WeChat private-domain handoff",
        "draft": "Prepare customer handoff notes without contacting or routing users.",
        "surface": "wechat",
    },
}


@dataclass(frozen=True)
class AgentRunConfig:
    namespace: str = "venus_agent_run"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus agent run config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus agent run namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus agent run must run in dry-run mode")


def build_agent_run_plan(
    payload: dict[str, Any],
    config: AgentRunConfig | None = None,
) -> dict[str, Any]:
    active_config = config or AgentRunConfig()
    safe_payload = _redact(payload)
    persona_samples = list(
        safe_payload.get("persona_samples")
        or ["姐妹们，先看屏障状态，证据和体验都要说清楚。"]
    )
    profile = build_persona_profile(persona_samples)

    executed_workflows: list[str] = []
    workflow_summaries: dict[str, dict[str, Any]] = {}
    evidence_ids: list[str] = []

    hotspots = list(safe_payload.get("hotspots") or [])
    products = list(safe_payload.get("products") or [])
    comments = list(safe_payload.get("comments") or [])
    douyin_engagement = safe_payload.get("douyin_engagement")
    wechat_private_domain = safe_payload.get("wechat_private_domain")
    commercial_strategy = safe_payload.get("commercial_strategy")
    competitors = _competitor_payload(safe_payload.get("competitors"))

    if hotspots:
        result = generate_hotspot_brief(hotspots, profile)
        executed_workflows.append("hotspot")
        workflow_summaries["hotspot"] = {
            "top_topic": result["top_topic"],
            "script_count": len(result["scripts"]),
            "risk_tag_count": len(result["risk_tags"]),
        }
        evidence_ids.extend(str(item) for item in list(result.get("evidence_ids") or []))

    if products:
        result = build_product_research_card(products[0])
        executed_workflows.append("product")
        workflow_summaries["product"] = {
            "product": result["product"],
            "risk_level": result["risk_level"],
            "forbidden_claim_count": len(result["forbidden_claims"]),
        }
        evidence_ids.extend(_product_evidence_ids(result))

    if comments:
        result = analyze_comments(comments, profile)
        executed_workflows.append("comments")
        workflow_summaries["comments"] = {
            "total": result["summary"]["total"],
            "high_risk": result["summary"]["high_risk"],
            "approval_gated": result["summary"]["approval_gated"],
        }

    if isinstance(douyin_engagement, dict):
        result = build_douyin_engagement_report(douyin_engagement)
        executed_workflows.append("douyin")
        workflow_summaries["douyin"] = {
            "comment_count": result["summary"]["comment_count"],
            "live_message_count": result["summary"]["live_message_count"],
            "approval_gated_reply_count": result["summary"]["approval_gated_reply_count"],
        }

    if isinstance(wechat_private_domain, dict):
        result = build_wechat_private_domain_report(wechat_private_domain)
        executed_workflows.append("wechat")
        workflow_summaries["wechat"] = {
            "question_count": result["summary"]["question_count"],
            "enterprise_wechat_handoff_count": result["summary"]["enterprise_wechat_handoff_count"],
            "approval_gated_action_count": result["summary"]["approval_gated_action_count"],
        }

    if isinstance(commercial_strategy, dict):
        result = build_commercial_strategy_report(commercial_strategy)
        executed_workflows.append("commercial")
        workflow_summaries["commercial"] = {
            "budget_recommendation_count": result["summary"]["budget_recommendation_count"],
            "high_risk_brief_count": result["summary"]["high_risk_brief_count"],
            "approval_gated_action_count": result["summary"]["approval_gated_action_count"],
        }

    if competitors.get("competitors"):
        result = build_monitoring_report(competitors)
        executed_workflows.append("monitoring")
        workflow_summaries["monitoring"] = {
            "top_account": result["summary"]["top_account"],
            "competitor_count": result["summary"]["competitor_count"],
            "risk_count": result["summary"]["risk_count"],
            "opportunity_count": len(result["opportunities"]),
        }

    airtable_result = build_airtable_sync_package(
        {
            "hotspots": hotspots,
            "products": products,
            "comments": comments,
            "competitors": competitors,
            "persona_samples": persona_samples,
            "approvals": [],
        }
    )
    executed_workflows.append("airtable")
    workflow_summaries["airtable"] = {
        "table_count": airtable_result["summary"]["table_count"],
        "record_count": airtable_result["summary"]["record_count"],
    }

    action_plan = _build_action_plan(
        safe_payload=safe_payload,
        workflow_summaries=workflow_summaries,
    )
    approval_records = _build_approval_records(
        action_plan=action_plan,
        evidence_ids=sorted(set(evidence_ids)),
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("requested_at") or "local-time"),
    )

    return {
        "workflow": "agent_run",
        "run_id": str(safe_payload.get("run_id") or "venus-run-local"),
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "trigger": str(safe_payload.get("trigger") or "manual"),
        "requested_at": str(safe_payload.get("requested_at") or "local-time"),
        "executed_workflows": executed_workflows,
        "workflow_summaries": workflow_summaries,
        "action_plan": action_plan,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "This local agent run only produces internal analysis, drafts, and review records.",
                "No Feishu message, Airtable write, Douyin reply, ad spend, Xingtu decision, or WeChat handoff was executed.",
                "Future OpenAI Agents SDK runners can call this contract after API credentials and eval gates are configured.",
            ],
        },
    }


def _build_action_plan(
    safe_payload: dict[str, Any],
    workflow_summaries: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    hotspot = workflow_summaries.get("hotspot", {})
    if hotspot:
        actions.append(
            _action(
                action_type="draft_short_video",
                title="Draft short-video script pack",
                approval_level=1,
                draft=f"Draft around {hotspot['top_topic']} with evidence, skin-state framing, and comment prompts.",
                surface="local_content",
            )
        )

    for action_type in list(safe_payload.get("requested_surfaces") or []):
        template = SURFACE_ACTIONS.get(str(action_type))
        if not template:
            continue
        actions.append(
            _action(
                action_type=str(action_type),
                title=str(template["title"]),
                approval_level=int(template["approval_level"]),
                draft=str(template["draft"]),
                surface=str(template["surface"]),
            )
        )
    return actions


def _action(
    action_type: str,
    title: str,
    approval_level: int,
    draft: str,
    surface: str,
) -> dict[str, Any]:
    manual = requires_manual_approval(approval_level)
    return {
        "action_type": action_type,
        "title": title,
        "surface": surface,
        "approval_level": approval_level,
        "requires_manual_approval": manual,
        "execution_state": "blocked_until_approved" if manual else "ready_for_internal_review",
        "draft": draft,
        "external_action_enabled": False,
    }


def _build_approval_records(
    action_plan: list[dict[str, Any]],
    evidence_ids: list[str],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    for action in action_plan:
        if not action["requires_manual_approval"]:
            continue
        records.append(
            create_approval_record(
                action_type=str(action["action_type"]),
                approval_level=int(action["approval_level"]),
                draft=str(action["draft"]),
                evidence_ids=evidence_ids,
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _competitor_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"competitors": value}
    return {"competitors": []}


def _product_evidence_ids(card: dict[str, Any]) -> list[str]:
    ids = []
    for item in list(card.get("evidence") or []):
        if isinstance(item, dict):
            ids.append(str(item.get("id") or item.get("title") or "product-evidence"))
        else:
            ids.append(str(item))
    return ids


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
