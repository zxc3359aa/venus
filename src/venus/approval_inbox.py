from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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

PUBLIC_OR_SPEND_SURFACES = {
    "ad_spend",
    "brand_commercial",
    "public_reply",
    "publishing",
    "private_domain",
}

SURFACE_PRIORITY = {
    "autopilot": 0,
    "ad_spend": 1,
    "brand_commercial": 2,
    "public_reply": 3,
    "publishing": 4,
    "private_domain": 5,
    "memory": 6,
    "connector": 7,
    "feishu": 8,
    "operations": 9,
}


@dataclass(frozen=True)
class ApprovalInboxConfig:
    namespace: str = "venus_approvals"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus approval inbox config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus approval inbox namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus approval inbox must run in dry-run mode")


def build_approval_inbox(
    payload: dict[str, Any],
    config: ApprovalInboxConfig | None = None,
) -> dict[str, Any]:
    active_config = config or ApprovalInboxConfig()
    safe_payload = _redact(payload)
    approval_items = [
        _approval_item(dict(record), index)
        for index, record in enumerate(list(safe_payload.get("approval_records") or []), start=1)
    ]
    priority_queue = _priority_queue(approval_items)
    decision_intents = _decision_intents(
        requested_decisions=[dict(item) for item in list(safe_payload.get("requested_decisions") or [])],
        approval_items=approval_items,
    )
    surface_summary = _surface_summary(approval_items)
    next_actions = _next_actions(priority_queue, decision_intents)

    return {
        "workflow": "approvals",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_approval_export"),
            "reviewed_at": str(safe_payload.get("reviewed_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run inbox centralizes approval records and records decision intents without applying them.",
        },
        "summary": {
            "approval_count": len(approval_items),
            "pending_count": sum(1 for item in approval_items if item["status"] == "pending"),
            "approved_count": sum(1 for item in approval_items if item["status"] == "approved"),
            "rejected_count": sum(1 for item in approval_items if item["status"] == "rejected"),
            "level4_count": sum(1 for item in approval_items if item["approval_level"] == 4),
            "public_or_spend_or_contact_count": sum(
                1 for item in approval_items if item["is_public_or_spend_or_contact"]
            ),
            "decision_intent_count": len(decision_intents),
            "second_review_count": sum(
                1 for item in decision_intents if item["requires_second_review"]
            ),
        },
        "approval_items": approval_items,
        "priority_queue": priority_queue,
        "surface_summary": surface_summary,
        "decision_intents": decision_intents,
        "next_actions": next_actions,
        "policy": {
            "max_auto_approval_level": 1,
            "decision_application": "recorded_only",
            "second_review_required_for": sorted(PUBLIC_OR_SPEND_SURFACES | {"approval_level_4"}),
            "notes": [
                "Approval level 2+ requires manual review.",
                "Public reply, publishing, private-domain contact, ad spend, and brand commitments require extra caution.",
                "Decision intents do not mutate source approval records.",
            ],
        },
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "This inbox only organizes approval records and decision intents.",
                "No approval, rejection, Feishu message, Douyin reply, video publish, ad spend, brand task, WeChat contact, memory write, or platform action is executed.",
            ],
        },
    }


def _approval_item(record: dict[str, Any], index: int) -> dict[str, Any]:
    action_type = str(record.get("action_type") or f"approval_{index}")
    approval_level = int(_number(record.get("approval_level")))
    surface = _surface_for(action_type)
    status = str(record.get("status") or "pending").lower()
    return {
        "approval_id": _approval_id(action_type, str(record.get("created_at") or ""), index),
        "action_type": action_type,
        "approval_level": approval_level,
        "risk_band": _risk_band(approval_level),
        "surface": surface,
        "is_public_or_spend_or_contact": surface in PUBLIC_OR_SPEND_SURFACES,
        "status": status,
        "draft": str(record.get("draft") or ""),
        "evidence_ids": [str(item) for item in list(record.get("evidence_ids") or [])],
        "reviewer": str(record.get("reviewer") or "owner"),
        "created_at": str(record.get("created_at") or "local-time"),
        "execution_state": "blocked_until_approved"
        if status == "pending" and approval_level >= 2
        else "recorded",
        "external_action_enabled": False,
    }


def _priority_queue(approval_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending = [item for item in approval_items if item["status"] == "pending"]
    return sorted(
        pending,
        key=lambda item: (
            -int(item["approval_level"]),
            SURFACE_PRIORITY.get(str(item["surface"]), 99),
            str(item["created_at"]),
        ),
    )


def _decision_intents(
    requested_decisions: list[dict[str, Any]],
    approval_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_action_type = {str(item["action_type"]): item for item in approval_items}
    intents = []
    for decision in requested_decisions:
        action_type = str(decision.get("action_type") or "unknown_action")
        matched = by_action_type.get(action_type)
        requires_second_review = bool(
            matched
            and (
                int(matched["approval_level"]) >= 4
                or bool(matched["is_public_or_spend_or_contact"])
            )
            and str(decision.get("decision") or "").lower() == "approve"
        )
        intents.append(
            {
                "action_type": action_type,
                "decision": str(decision.get("decision") or "needs_changes").lower(),
                "reason": str(decision.get("reason") or ""),
                "reviewer": str(decision.get("reviewer") or "owner"),
                "match_status": "matched" if matched else "missing_approval_record",
                "matched_approval_id": str(matched["approval_id"]) if matched else "",
                "approval_level": int(matched["approval_level"]) if matched else 0,
                "surface": str(matched["surface"]) if matched else "unknown",
                "requires_second_review": requires_second_review,
                "execution_state": "recorded_only",
                "external_action_enabled": False,
            }
        )
    return intents


def _surface_summary(approval_items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for item in approval_items:
        surface = str(item["surface"])
        if surface not in summary:
            summary[surface] = {"total_count": 0, "pending_count": 0, "level4_count": 0}
        summary[surface]["total_count"] += 1
        if item["status"] == "pending":
            summary[surface]["pending_count"] += 1
        if item["approval_level"] == 4:
            summary[surface]["level4_count"] += 1
    return summary


def _next_actions(
    priority_queue: list[dict[str, Any]],
    decision_intents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    critical = [item for item in priority_queue if item["approval_level"] == 4]
    if critical:
        actions.append(
            {
                "action_type": "review_critical_approvals",
                "title": "Review level-4 approval items first",
                "approval_level": 4,
                "execution_state": "blocked_until_approved",
                "draft": "Review autopilot, ad spend, brand, connector, or customer-contact items before any lower-risk work.",
                "evidence_ids": [str(item["approval_id"]) for item in critical],
                "external_action_enabled": False,
            }
        )
    second_review = [item for item in decision_intents if item["requires_second_review"]]
    if second_review:
        actions.append(
            {
                "action_type": "second_review_required",
                "title": "Second review required before applying high-risk decisions",
                "approval_level": 4,
                "execution_state": "blocked_until_approved",
                "draft": "High-risk approval intents are recorded only and need second review before any live execution.",
                "evidence_ids": [str(item["matched_approval_id"]) for item in second_review],
                "external_action_enabled": False,
            }
        )
    if priority_queue:
        actions.append(
            {
                "action_type": "clear_pending_approval_queue",
                "title": "Clear pending approval queue",
                "approval_level": 2,
                "execution_state": "blocked_until_approved",
                "draft": "Review pending approval items from highest approval level to lowest.",
                "evidence_ids": [str(item["approval_id"]) for item in priority_queue],
                "external_action_enabled": False,
            }
        )
    return actions


def _surface_for(action_type: str) -> str:
    value = action_type.lower()
    if "autopilot" in value or "eval" in value:
        return "autopilot"
    if "qianchuan" in value or "budget" in value or "campaign" in value:
        return "ad_spend"
    if "xingtu" in value or "brand" in value or "brief" in value:
        return "brand_commercial"
    if "douyin" in value or "reply" in value or "comment" in value:
        return "public_reply"
    if "publish" in value or "production" in value or "content" in value:
        return "publishing"
    if "wechat" in value or "handoff" in value or "enterprise" in value:
        return "private_domain"
    if "memory" in value or "learning" in value:
        return "memory"
    if "connector" in value or "live_connector" in value:
        return "connector"
    if "feishu" in value:
        return "feishu"
    return "operations"


def _risk_band(approval_level: int) -> str:
    if approval_level >= 4:
        return "critical"
    if approval_level == 3:
        return "high"
    if approval_level == 2:
        return "medium"
    return "low"


def _approval_id(action_type: str, created_at: str, index: int) -> str:
    suffix = created_at.replace(":", "").replace("-", "").replace("+", "").replace("T", "-")
    return f"{action_type}-{suffix or index}"


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
