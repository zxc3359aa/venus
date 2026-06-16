from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.comments import analyze_comments
from venus.content import generate_hotspot_brief, score_hotspot
from venus.monitoring import build_monitoring_report
from venus.persona import build_persona_profile
from venus.product_research import build_product_research_card


SECRET_KEYS = {"secret", "token", "password", "app_secret", "authorization"}


@dataclass(frozen=True)
class AirtableExportConfig:
    base_name: str = "Venus Ops"
    namespace: str = "venus_airtable"
    dry_run: bool = True

    def __post_init__(self) -> None:
        values = f"{self.base_name} {self.namespace}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus Airtable export must not reference Xiaolongxia")
        if not self.dry_run:
            raise ValueError("Venus Airtable export must run in dry-run mode")


def build_airtable_sync_package(
    payload: dict[str, Any],
    config: AirtableExportConfig | None = None,
) -> dict[str, Any]:
    active_config = config or AirtableExportConfig()
    safe_payload = _redact(payload)
    profile = build_persona_profile(
        list(safe_payload.get("persona_samples") or ["姐妹们，先看屏障状态，证据和体验都要说清楚。"])
    )

    hotspots = list(safe_payload.get("hotspots") or [])
    products = list(safe_payload.get("products") or [])
    comments = list(safe_payload.get("comments") or [])
    competitor_payload = _competitor_payload(safe_payload.get("competitors"))

    hotspot_brief = generate_hotspot_brief(hotspots, profile) if hotspots else None
    product_cards = [build_product_research_card(product) for product in products]
    comment_report = analyze_comments(comments, profile) if comments else {"items": [], "summary": {}}
    monitoring_report = (
        build_monitoring_report(competitor_payload)
        if competitor_payload.get("competitors")
        else {"leaderboard": [], "opportunities": []}
    )

    tables = [
        _hotspots_table(hotspots, hotspot_brief, active_config),
        _products_table(product_cards, active_config),
        _comments_table(comment_report, active_config),
        _competitors_table(monitoring_report, active_config),
        _monitoring_opportunities_table(monitoring_report, active_config),
        _approvals_table(list(safe_payload.get("approvals") or []), active_config),
    ]

    return {
        "dry_run": active_config.dry_run,
        "external_actions": [],
        "base": {
            "name": active_config.base_name,
            "namespace": active_config.namespace,
            "description": "Venus beauty and skincare operations base package.",
        },
        "tables": tables,
        "summary": {
            "table_count": len(tables),
            "record_count": sum(len(table["records"]) for table in tables),
            "tables": [table["name"] for table in tables],
        },
        "sync_boundary": {
            "can_import_later": True,
            "notes": [
                "Airtable write is disabled in this dry-run package.",
                "No bases, tables, records, automations, or interfaces were created.",
                "Public replies, publishing, lead routing, and ad changes remain approval-gated.",
            ],
        },
    }


def _hotspots_table(
    hotspots: list[dict[str, Any]],
    hotspot_brief: dict[str, Any] | None,
    config: AirtableExportConfig,
) -> dict[str, Any]:
    top_topic = hotspot_brief["top_topic"] if hotspot_brief else ""
    records = []
    for item in hotspots:
        topic = str(item.get("topic", "Untitled hotspot"))
        records.append(
            _record(
                {
                    "Name": topic,
                    "Topic": topic,
                    "Type": item.get("type", ""),
                    "Freshness": _number(item.get("freshness")),
                    "Relevance": _number(item.get("relevance")),
                    "Controversy": _number(item.get("controversy")),
                    "Score": score_hotspot(item),
                    "Is Top Topic": topic == top_topic,
                    "Evidence IDs": ", ".join(str(value) for value in list(item.get("evidence") or [])),
                    "Venus Namespace": config.namespace,
                }
            )
        )
    return _table(
        "Hotspots",
        [
            _field("Name", "singleLineText"),
            _field("Topic", "singleLineText"),
            _field("Type", "singleSelect"),
            _field("Freshness", "number"),
            _field("Relevance", "number"),
            _field("Controversy", "number"),
            _field("Score", "number"),
            _field("Is Top Topic", "checkbox"),
            _field("Evidence IDs", "longText"),
            _field("Venus Namespace", "singleLineText"),
        ],
        records,
        ["Daily Hotspots", "High Controversy"],
    )


def _products_table(product_cards: list[dict[str, Any]], config: AirtableExportConfig) -> dict[str, Any]:
    records = []
    for card in product_cards:
        product_name = str(card.get("product", "Untitled product"))
        product_parts = product_name.split(" ", 1)
        filing = dict(card.get("sections", {}).get("filing", {}))
        ingredients = dict(card.get("sections", {}).get("ingredients", {}))
        evidence = list(card.get("evidence") or [])
        records.append(
            _record(
                {
                    "Name": product_name,
                    "Brand": product_parts[0] if product_parts else "",
                    "Product": product_parts[1] if len(product_parts) > 1 else product_name,
                    "Filing ID": filing.get("filing_id", ""),
                    "Risk Level": card["risk_level"],
                    "Ingredients": ", ".join(list(ingredients.get("items") or [])),
                    "Forbidden Claims": ", ".join(card["forbidden_claims"]),
                    "Safe Talking Points": "\n".join(card["safe_talking_points"]),
                    "Evidence Confidence": _evidence_confidence(evidence),
                    "Venus Namespace": config.namespace,
                }
            )
        )
    return _table(
        "Products",
        [
            _field("Name", "singleLineText"),
            _field("Brand", "singleLineText"),
            _field("Product", "singleLineText"),
            _field("Filing ID", "singleLineText"),
            _field("Risk Level", "singleSelect"),
            _field("Ingredients", "longText"),
            _field("Forbidden Claims", "longText"),
            _field("Safe Talking Points", "longText"),
            _field("Evidence Confidence", "singleSelect"),
            _field("Venus Namespace", "singleLineText"),
        ],
        records,
        ["Research Queue", "High Risk Products"],
    )


def _comments_table(comment_report: dict[str, Any], config: AirtableExportConfig) -> dict[str, Any]:
    records = []
    for item in list(comment_report.get("items") or []):
        records.append(
            _record(
                {
                    "Name": item.get("id") or item.get("text", "")[:24],
                    "Comment ID": item.get("id", ""),
                    "Text": item.get("text", ""),
                    "Intent": item.get("intent", ""),
                    "Risk": item.get("risk", ""),
                    "Approval Level": item.get("approval_level", 0),
                    "Draft Reply": item.get("draft_reply", ""),
                    "Venus Namespace": config.namespace,
                }
            )
        )
    return _table(
        "Comments",
        [
            _field("Name", "singleLineText"),
            _field("Comment ID", "singleLineText"),
            _field("Text", "longText"),
            _field("Intent", "singleSelect"),
            _field("Risk", "singleSelect"),
            _field("Approval Level", "number"),
            _field("Draft Reply", "longText"),
            _field("Venus Namespace", "singleLineText"),
        ],
        records,
        ["Needs Approval", "Reply Drafts"],
    )


def _competitors_table(monitoring_report: dict[str, Any], config: AirtableExportConfig) -> dict[str, Any]:
    records = []
    for row in list(monitoring_report.get("leaderboard") or []):
        records.append(
            _record(
                {
                    "Name": row["handle"],
                    "Handle": row["handle"],
                    "Followers": row["followers"],
                    "Video Count": row["video_count"],
                    "Avg Completion Rate": row["avg_completion_rate"],
                    "Avg Engagement Rate": row["avg_engagement_rate"],
                    "Ad Ratio": row["ad_ratio"],
                    "Live Hours": row["live_hours"],
                    "Risk Count": row["risk_count"],
                    "Growth Signal Score": row["growth_signal_score"],
                    "Top Topics": ", ".join(row["top_topics"]),
                    "Venus Namespace": config.namespace,
                }
            )
        )
    return _table(
        "Competitors",
        [
            _field("Name", "singleLineText"),
            _field("Handle", "singleLineText"),
            _field("Followers", "number"),
            _field("Video Count", "number"),
            _field("Avg Completion Rate", "number"),
            _field("Avg Engagement Rate", "number"),
            _field("Ad Ratio", "number"),
            _field("Live Hours", "number"),
            _field("Risk Count", "number"),
            _field("Growth Signal Score", "number"),
            _field("Top Topics", "longText"),
            _field("Venus Namespace", "singleLineText"),
        ],
        records,
        ["Competitor Leaderboard", "Risk Watch"],
    )


def _monitoring_opportunities_table(
    monitoring_report: dict[str, Any],
    config: AirtableExportConfig,
) -> dict[str, Any]:
    records = []
    for index, item in enumerate(list(monitoring_report.get("opportunities") or []), start=1):
        records.append(
            _record(
                {
                    "Name": f"{index}. {item['action_type']} - {item['based_on']}",
                    "Action Type": item["action_type"],
                    "Priority": item["priority"],
                    "Based On": item["based_on"],
                    "Recommendation": item["recommendation"],
                    "Venus Namespace": config.namespace,
                }
            )
        )
    return _table(
        "Monitoring Opportunities",
        [
            _field("Name", "singleLineText"),
            _field("Action Type", "singleSelect"),
            _field("Priority", "singleSelect"),
            _field("Based On", "singleLineText"),
            _field("Recommendation", "longText"),
            _field("Venus Namespace", "singleLineText"),
        ],
        records,
        ["Next Actions"],
    )


def _approvals_table(approvals: list[dict[str, Any]], config: AirtableExportConfig) -> dict[str, Any]:
    records = []
    for approval in approvals:
        records.append(
            _record(
                {
                    "Name": approval.get("action_type", "approval"),
                    "Action Type": approval.get("action_type", ""),
                    "Approval Level": approval.get("approval_level", 0),
                    "Status": approval.get("status", "pending"),
                    "Reviewer": approval.get("reviewer", ""),
                    "Draft": approval.get("draft", ""),
                    "Evidence IDs": ", ".join(str(value) for value in list(approval.get("evidence_ids") or [])),
                    "Venus Namespace": config.namespace,
                }
            )
        )
    return _table(
        "Approvals",
        [
            _field("Name", "singleLineText"),
            _field("Action Type", "singleSelect"),
            _field("Approval Level", "number"),
            _field("Status", "singleSelect"),
            _field("Reviewer", "singleLineText"),
            _field("Draft", "longText"),
            _field("Evidence IDs", "longText"),
            _field("Venus Namespace", "singleLineText"),
        ],
        records,
        ["Pending Review"],
    )


def _table(
    name: str,
    fields: list[dict[str, str]],
    records: list[dict[str, dict[str, Any]]],
    views: list[str],
) -> dict[str, Any]:
    return {"name": name, "fields": fields, "views": views, "records": records}


def _field(name: str, field_type: str) -> dict[str, str]:
    return {"name": name, "type": field_type}


def _record(fields: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {"fields": fields}


def _competitor_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {"competitors": list(value.get("competitors") or [])}
    if isinstance(value, list):
        return {"competitors": value}
    return {"competitors": []}


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SECRET_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _evidence_confidence(evidence: list[dict[str, Any]]) -> str:
    confidences = {str(item.get("confidence", "")).lower() for item in evidence}
    if "high" in confidences:
        return "high"
    if "medium" in confidences:
        return "medium"
    return "low"
