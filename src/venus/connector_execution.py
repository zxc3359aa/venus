from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.approvals import create_approval_record
from venus.storage import JsonStore


SUPPORTED_ADAPTERS = {
    "feishu": "feishu_card_send_candidate",
    "airtable": "airtable_record_write_candidate",
    "douyin": "douyin_reply_or_metric_candidate",
    "wechat": "wechat_private_domain_candidate",
    "qianchuan": "oceanengine_budget_candidate",
    "xingtu": "xingtu_brand_task_candidate",
    "openai": "openai_agents_sdk_candidate",
    "backup": "backup_write_candidate",
}
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
class ConnectorExecutionConfig:
    workspace_root: Path | str
    namespace: str = "venus_connector_execution"
    collection: str = "connector_execution_manifests"
    approval_mode: str = "manual"
    reviewer: str = "owner"
    external_dry_run: bool = True

    def __post_init__(self) -> None:
        root = Path(self.workspace_root)
        object.__setattr__(self, "workspace_root", root)
        values = (
            f"{root} {self.namespace} {self.collection} "
            f"{self.approval_mode} {self.reviewer}"
        ).lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus connector execution config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus connector execution namespace must start with venus_")
        if self.collection != "connector_execution_manifests":
            raise ValueError(
                "Venus connector execution collection must be connector_execution_manifests"
            )
        if not self.external_dry_run:
            raise ValueError("Venus connector execution must keep external actions in dry-run mode")


def build_connector_execution_plan(
    payload: dict[str, Any],
    config: ConnectorExecutionConfig | None = None,
) -> dict[str, Any]:
    safe_payload = _redact(payload)
    workspace_root = safe_payload.get("workspace_root") or "."
    active_config = config or ConnectorExecutionConfig(workspace_root=workspace_root)
    storage_path = _storage_path(active_config)
    draft_records = _draft_records(safe_payload, active_config)
    connector_reviews = [dict(item) for item in list(safe_payload.get("connector_reviews") or [])]
    connectors_by_surface = _connectors_by_surface(connector_reviews)
    surface_readiness = _surface_readiness(connector_reviews)
    overrides = _overrides_by_draft(safe_payload)
    executed_at = str(safe_payload.get("executed_at") or "local-time")

    if not bool(safe_payload.get("execution_requested")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            source=str(safe_payload.get("source") or "local_connector_execution"),
            executed_at=executed_at,
            draft_records=draft_records,
            connector_reviews=connector_reviews,
            surface_readiness=surface_readiness,
            execution_records=[],
            duplicate_items=[],
            blocked_items=[],
            approval_records=[],
            existing_count=0,
            execution_state="blocked_execution_not_requested",
            execution_requested=False,
            approved_execution_review=False,
        )

    if not bool(safe_payload.get("approved_execution_review")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            source=str(safe_payload.get("source") or "local_connector_execution"),
            executed_at=executed_at,
            draft_records=draft_records,
            connector_reviews=connector_reviews,
            surface_readiness=surface_readiness,
            execution_records=[],
            duplicate_items=[],
            blocked_items=[],
            approval_records=[],
            existing_count=0,
            execution_state="blocked_until_execution_review",
            execution_requested=True,
            approved_execution_review=False,
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_extra = [
        dict(item) for item in list(safe_payload.get("existing_execution_manifests") or [])
    ]
    existing_keys = _existing_keys(existing_records + existing_extra)

    execution_records: list[dict[str, Any]] = []
    duplicate_items: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []

    for draft in draft_records:
        draft_id = str(draft.get("draft_id") or "")
        surface = _surface(draft)
        connector = connectors_by_surface.get(surface)
        override = overrides.get(draft_id)
        block_reason = _block_reason(draft, surface, connector, override)
        if block_reason:
            blocked_items.append(_blocked_item(draft, surface, block_reason, connector))
            continue

        assert connector is not None
        record = _execution_record(draft, connector, surface, executed_at)
        if _execution_key(record) in existing_keys:
            duplicate_items.append(_duplicate_item(record))
            continue
        execution_records.append(record)
        existing_keys.add(_execution_key(record))

    if execution_records:
        store.write_collection(active_config.collection, existing_records + execution_records)

    approval_records = _approval_records(
        safe_payload=safe_payload,
        execution_records=execution_records,
        blocked_items=blocked_items,
        reviewer=active_config.reviewer,
        created_at=executed_at,
    )

    if execution_records:
        execution_state = "local_manifests_written"
    elif duplicate_items:
        execution_state = "already_manifested"
    elif blocked_items:
        execution_state = "no_executable_manifests"
    else:
        execution_state = "empty_drafts"

    return _report(
        config=active_config,
        storage_path=storage_path,
        source=str(safe_payload.get("source") or "local_connector_execution"),
        executed_at=executed_at,
        draft_records=draft_records,
        connector_reviews=connector_reviews,
        surface_readiness=surface_readiness,
        execution_records=execution_records,
        duplicate_items=duplicate_items,
        blocked_items=blocked_items,
        approval_records=approval_records,
        existing_count=len(existing_records),
        execution_state=execution_state,
        execution_requested=True,
        approved_execution_review=True,
    )


def _report(
    config: ConnectorExecutionConfig,
    storage_path: Path,
    source: str,
    executed_at: str,
    draft_records: list[dict[str, Any]],
    connector_reviews: list[dict[str, Any]],
    surface_readiness: dict[str, dict[str, Any]],
    execution_records: list[dict[str, Any]],
    duplicate_items: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    approval_records: list[dict[str, Any]],
    existing_count: int,
    execution_state: str,
    execution_requested: bool,
    approved_execution_review: bool,
) -> dict[str, Any]:
    return {
        "workflow": "connector_execution",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "source": source,
        "executed_at": executed_at,
        "execution_state": execution_state,
        "summary": {
            "draft_count": len(draft_records),
            "execution_record_count": len(execution_records),
            "duplicate_count": len(duplicate_items),
            "blocked_count": len(blocked_items),
            "approval_record_count": len(approval_records),
            "stored_total_count": existing_count + len(execution_records),
        },
        "execution_records": execution_records,
        "duplicate_items": duplicate_items,
        "blocked_items": blocked_items,
        "approval_records": approval_records,
        "surface_readiness": surface_readiness,
        "connector_count": len(connector_reviews),
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "execution_requested": execution_requested,
            "approved_execution_review": approved_execution_review,
            "record_count": len(execution_records),
            "execution_state": execution_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "execution_ids_to_remove": [str(item["execution_id"]) for item in execution_records],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/connector_execution_manifests.json",
            "notes": [
                "Only local Venus connector execution manifest records can be written.",
                "All platform adapters remain candidates with external_action_enabled false.",
                "No Feishu message, Airtable write, Douyin reply, publish action, ad spend, Xingtu commitment, WeChat contact, OpenAI model call, memory state, backup state, or external platform state is changed.",
            ],
        },
    }


def _draft_records(payload: dict[str, Any], config: ConnectorExecutionConfig) -> list[dict[str, Any]]:
    if payload.get("draft_records") is not None:
        return [dict(item) for item in list(payload.get("draft_records") or [])]
    return JsonStore(config.workspace_root).read_collection("delivery_drafts")


def _connectors_by_surface(connectors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for connector in connectors:
        surface = str(connector.get("surface") or "").lower()
        if surface and surface not in indexed:
            indexed[surface] = connector
    return indexed


def _surface_readiness(connectors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    readiness = {}
    for connector in connectors:
        surface = str(connector.get("surface") or "unknown").lower()
        missing = [str(item) for item in list(connector.get("missing_permissions") or [])]
        readiness[surface] = {
            "connector_id": str(connector.get("connector_id") or ""),
            "connector_type": str(connector.get("connector_type") or ""),
            "ready_for_launch": bool(connector.get("ready_for_launch")),
            "missing_permissions": missing,
            "audit_ready": bool(connector.get("audit_ready")),
            "rollback_ready": bool(connector.get("rollback_ready")),
            "approval_level": int(_number(connector.get("approval_level"))),
            "external_action_enabled": False,
        }
    return readiness


def _overrides_by_draft(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed = {}
    for override in [dict(item) for item in list(payload.get("execution_overrides") or [])]:
        for key in (
            str(override.get("draft_id") or ""),
            str(override.get("outbox_id") or ""),
            str(override.get("action_id") or ""),
        ):
            if key and key not in indexed:
                indexed[key] = override
    return indexed


def _surface(draft: dict[str, Any]) -> str:
    return str(draft.get("target_surface") or draft.get("surface") or "").lower()


def _block_reason(
    draft: dict[str, Any],
    surface: str,
    connector: dict[str, Any] | None,
    override: dict[str, Any] | None,
) -> str:
    if override and bool(override.get("external_action_enabled")):
        return "external_override_blocked"
    if bool(draft.get("external_action_enabled")):
        return "external_draft_blocked"
    if str(draft.get("dispatch_state") or "") != "local_review_required":
        return "draft_not_local_review"
    if surface not in SUPPORTED_ADAPTERS:
        return "unsupported_surface"
    if connector is None:
        return "missing_connector_review"

    missing_permissions = [str(item) for item in list(connector.get("missing_permissions") or [])]
    if missing_permissions:
        return "missing_connector_permission"
    if not bool(connector.get("audit_ready")) or not bool(connector.get("rollback_ready")):
        return "missing_audit_or_rollback"
    if not bool(connector.get("ready_for_launch")):
        return "connector_not_ready"

    approval_level = max(
        int(_number(draft.get("approval_level"))),
        int(_number(connector.get("approval_level"))),
    )
    if approval_level >= 4:
        return "high_risk_live_action"
    return ""


def _execution_record(
    draft: dict[str, Any],
    connector: dict[str, Any],
    surface: str,
    executed_at: str,
) -> dict[str, Any]:
    connector_id = str(connector.get("connector_id") or surface)
    draft_id = str(draft.get("draft_id") or "")
    return {
        "execution_id": "-".join(["exec", _slug(draft_id), _slug(connector_id)]),
        "draft_id": draft_id,
        "outbox_id": str(draft.get("outbox_id") or ""),
        "action_id": str(draft.get("action_id") or ""),
        "action_type": str(draft.get("action_type") or ""),
        "artifact_type": str(draft.get("artifact_type") or ""),
        "target_surface": surface,
        "connector_id": connector_id,
        "connector_type": str(connector.get("connector_type") or ""),
        "adapter_type": SUPPORTED_ADAPTERS[surface],
        "required_secret_refs": [str(item) for item in list(connector.get("secret_refs") or [])],
        "permission_snapshot": {
            "required": [str(item) for item in list(connector.get("permissions_required") or [])],
            "granted": [str(item) for item in list(connector.get("permissions_granted") or [])],
            "missing": [str(item) for item in list(connector.get("missing_permissions") or [])],
        },
        "audit_log_ref": f"venus_connector_audit:{connector_id}",
        "rollback_ref": f"venus_connector_rollback:{connector_id}",
        "manifest_payload": dict(draft.get("draft_payload") or {}),
        "executed_at": executed_at,
        "execution_state": "local_manifest_ready",
        "dispatch_state": "blocked_until_live_connector_enabled",
        "external_action_enabled": False,
    }


def _blocked_item(
    draft: dict[str, Any],
    surface: str,
    reason: str,
    connector: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "draft_id": str(draft.get("draft_id") or ""),
        "outbox_id": str(draft.get("outbox_id") or ""),
        "action_id": str(draft.get("action_id") or ""),
        "action_type": str(draft.get("action_type") or ""),
        "target_surface": surface,
        "connector_id": str((connector or {}).get("connector_id") or ""),
        "skip_reason": reason,
    }


def _duplicate_item(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "execution_id": str(record["execution_id"]),
        "draft_id": str(record["draft_id"]),
        "connector_id": str(record["connector_id"]),
        "skip_reason": "already_manifested",
    }


def _approval_records(
    safe_payload: dict[str, Any],
    execution_records: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    evidence_ids = [str(item.get("execution_id") or item.get("draft_id")) for item in execution_records]
    evidence_ids.extend(str(item.get("draft_id") or "") for item in blocked_items)
    evidence_ids = [item for item in evidence_ids if item]

    if bool(safe_payload.get("live_dispatch_requested")):
        records.append(
            create_approval_record(
                action_type="venus_live_connector_dispatch_review",
                approval_level=4,
                draft="Review connector execution manifests before any live platform dispatch is enabled.",
                evidence_ids=evidence_ids,
                reviewer=reviewer,
                created_at=created_at,
            )
        )

    high_risk = [item for item in blocked_items if item["skip_reason"] == "high_risk_live_action"]
    if high_risk:
        records.append(
            create_approval_record(
                action_type="venus_high_risk_connector_execution_review",
                approval_level=4,
                draft="Review high-risk connector execution candidates before any ad spend, brand commitment, public reply, or customer contact is enabled.",
                evidence_ids=[str(item["draft_id"]) for item in high_risk],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_execution_key(record) for record in records}


def _execution_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("execution_id") or ""),
            str(item.get("draft_id") or ""),
            str(item.get("connector_id") or ""),
        ]
    )


def _storage_path(config: ConnectorExecutionConfig) -> Path:
    return Path(config.workspace_root) / "data" / "venus" / f"{config.collection}.json"


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "-" for ch in value).strip("-")


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
