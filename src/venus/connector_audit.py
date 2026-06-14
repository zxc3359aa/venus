from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval


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

READY_VALUES = {"ready", "configured", "enabled"}


@dataclass(frozen=True)
class ConnectorAuditConfig:
    namespace: str = "venus_connectors"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus connector audit config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus connector audit namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus connector audit must run in dry-run mode")


def build_connector_audit_report(
    payload: dict[str, Any],
    config: ConnectorAuditConfig | None = None,
) -> dict[str, Any]:
    active_config = config or ConnectorAuditConfig()
    safe_payload = _redact(payload)
    connectors = [dict(item) for item in list(safe_payload.get("connectors") or [])]
    connector_reviews = [_review_connector(item) for item in connectors]
    permission_matrix = _build_permission_matrix(connector_reviews)
    readiness_gaps = _build_readiness_gaps(connector_reviews)
    launch_sequence = _build_launch_sequence(connector_reviews)
    approval_records = _build_approval_records(
        live_connector_requested=bool(safe_payload.get("live_connector_requested")),
        connector_reviews=connector_reviews,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("reviewed_at") or "local-time"),
    )

    return {
        "workflow": "connectors",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": str(safe_payload.get("source") or "local_connector_audit"),
        "reviewed_at": str(safe_payload.get("reviewed_at") or "local-time"),
        "summary": {
            "connector_count": len(connector_reviews),
            "ready_connector_count": sum(1 for item in connector_reviews if item["ready_for_launch"]),
            "blocked_connector_count": sum(1 for item in connector_reviews if not item["ready_for_launch"]),
            "missing_permission_count": sum(1 for item in connector_reviews if item["missing_permissions"]),
            "missing_audit_log_count": sum(1 for item in connector_reviews if not item["audit_ready"]),
            "missing_rollback_count": sum(1 for item in connector_reviews if not item["rollback_ready"]),
            "high_risk_connector_count": sum(1 for item in connector_reviews if item["risk_level"] == "high"),
            "approval_gated_connector_count": sum(
                1 for item in connector_reviews if item["requires_manual_approval"]
            ),
            "approval_record_count": len(approval_records),
        },
        "connector_reviews": connector_reviews,
        "permission_matrix": permission_matrix,
        "readiness_gaps": readiness_gaps,
        "launch_sequence": launch_sequence,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "This connector audit only reviews local metadata and approval gates.",
                "No platform credential was read, exchanged, refreshed, or tested.",
                "Live connector enablement remains blocked until permissions, audit logs, rollback plans, and owner approval are complete.",
            ],
        },
    }


def _review_connector(connector: dict[str, Any]) -> dict[str, Any]:
    connector_id = str(connector.get("connector_id") or connector.get("id") or "connector")
    required = [str(item) for item in list(connector.get("permissions_required") or [])]
    granted = [str(item) for item in list(connector.get("permissions_granted") or [])]
    missing = [item for item in required if item not in set(granted)]
    audit_state = str(connector.get("audit_log") or "").lower()
    rollback_state = str(connector.get("rollback") or "").lower()
    status = str(connector.get("status") or "unknown").lower()
    approval_level = int(connector.get("approval_level") or 1)
    audit_ready = audit_state in READY_VALUES
    rollback_ready = rollback_state in READY_VALUES
    ready_for_launch = status == "ready" and not missing and audit_ready and rollback_ready
    manual = requires_manual_approval(approval_level)
    risk_level = _risk_level(
        approval_level=approval_level,
        missing_permissions=missing,
        audit_ready=audit_ready,
        rollback_ready=rollback_ready,
        status=status,
    )

    if not ready_for_launch:
        execution_state = "blocked_by_readiness_gap"
    elif manual:
        execution_state = "blocked_until_approved"
    else:
        execution_state = "ready_for_internal_review"

    return {
        "connector_id": connector_id,
        "surface": str(connector.get("surface") or "unknown"),
        "connector_type": str(connector.get("connector_type") or "unknown"),
        "desired_workflows": [str(item) for item in list(connector.get("desired_workflows") or [])],
        "status": status,
        "permissions_required": required,
        "permissions_granted": granted,
        "missing_permissions": missing,
        "secret_refs": [str(item) for item in list(connector.get("secret_refs") or [])],
        "audit_ready": audit_ready,
        "rollback_ready": rollback_ready,
        "data_classes": [str(item) for item in list(connector.get("data_classes") or [])],
        "approval_level": approval_level,
        "requires_manual_approval": manual,
        "risk_level": risk_level,
        "ready_for_launch": ready_for_launch,
        "execution_state": execution_state,
        "external_action_enabled": False,
        "evidence_ids": [str(item) for item in list(connector.get("evidence") or [])],
    }


def _risk_level(
    approval_level: int,
    missing_permissions: list[str],
    audit_ready: bool,
    rollback_ready: bool,
    status: str,
) -> str:
    if approval_level >= 4:
        return "high"
    if missing_permissions or not audit_ready or not rollback_ready or status != "ready":
        return "medium"
    return "low"


def _build_permission_matrix(connector_reviews: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item["connector_id"]): {
            "required": list(item["permissions_required"]),
            "granted": list(item["permissions_granted"]),
            "missing": list(item["missing_permissions"]),
        }
        for item in connector_reviews
    }


def _build_readiness_gaps(connector_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for item in connector_reviews:
        reasons = []
        if item["missing_permissions"]:
            reasons.append("missing_permission")
        if not item["audit_ready"]:
            reasons.append("missing_audit_log")
        if not item["rollback_ready"]:
            reasons.append("missing_rollback")
        if item["status"] != "ready":
            reasons.append(f"status:{item['status']}")
        if not reasons:
            continue
        gaps.append(
            {
                "connector_id": item["connector_id"],
                "surface": item["surface"],
                "severity": item["risk_level"],
                "reasons": reasons,
                "recommendation": "Complete permissions, audit logs, rollback checks, and owner approval before enabling this connector.",
            }
        )
    return sorted(gaps, key=lambda item: {"high": 0, "medium": 1, "low": 2}[str(item["severity"])])


def _build_launch_sequence(connector_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sequence = []
    for item in connector_reviews:
        if not item["ready_for_launch"]:
            continue
        sequence.append(
            {
                "connector_id": item["connector_id"],
                "surface": item["surface"],
                "connector_type": item["connector_type"],
                "desired_workflows": list(item["desired_workflows"]),
                "approval_level": item["approval_level"],
                "execution_state": item["execution_state"],
                "external_action_enabled": False,
            }
        )
    return sequence


def _build_approval_records(
    live_connector_requested: bool,
    connector_reviews: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    connector_ids = [str(item["connector_id"]) for item in connector_reviews]
    if live_connector_requested:
        records.append(
            create_approval_record(
                action_type="venus_connector_live_enablement",
                approval_level=3,
                draft="Review connector permissions, audit logs, rollback plans, and launch sequence before enabling live integrations.",
                evidence_ids=connector_ids,
                reviewer=reviewer,
                created_at=created_at,
            )
        )

    high_risk = [item for item in connector_reviews if item["risk_level"] == "high"]
    if high_risk:
        records.append(
            create_approval_record(
                action_type="venus_high_risk_connector_review",
                approval_level=max(int(item["approval_level"]) for item in high_risk),
                draft="Review high-risk connector scopes such as ad budget, audience data, or public platform actions before launch.",
                evidence_ids=[str(item["connector_id"]) for item in high_risk],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


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
