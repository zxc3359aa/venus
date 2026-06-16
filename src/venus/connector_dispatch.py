from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.approvals import create_approval_record
from venus.storage import JsonStore


REQUEST_TEMPLATES = {
    "feishu": {"method": "POST", "endpoint_label": "feishu.private_card"},
    "airtable": {"method": "POST", "endpoint_label": "airtable.records"},
    "douyin": {"method": "POST", "endpoint_label": "douyin.reply_or_metric"},
    "wechat": {"method": "POST", "endpoint_label": "wechat.private_domain"},
    "qianchuan": {"method": "POST", "endpoint_label": "qianchuan.campaign_budget"},
    "xingtu": {"method": "POST", "endpoint_label": "xingtu.brand_task"},
    "openai": {"method": "POST", "endpoint_label": "openai.agents_sdk"},
    "backup": {"method": "PUT", "endpoint_label": "backup.snapshot"},
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
class ConnectorDispatchConfig:
    workspace_root: Path | str
    namespace: str = "venus_connector_dispatch"
    collection: str = "connector_dispatch_rehearsals"
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
            raise ValueError("Venus connector dispatch config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus connector dispatch namespace must start with venus_")
        if self.collection != "connector_dispatch_rehearsals":
            raise ValueError("Venus connector dispatch collection must be connector_dispatch_rehearsals")
        if not self.external_dry_run:
            raise ValueError("Venus connector dispatch must keep external actions in dry-run mode")


def build_connector_dispatch_rehearsal(
    payload: dict[str, Any],
    config: ConnectorDispatchConfig | None = None,
) -> dict[str, Any]:
    safe_payload = _redact(payload)
    workspace_root = safe_payload.get("workspace_root") or "."
    active_config = config or ConnectorDispatchConfig(workspace_root=workspace_root)
    storage_path = _storage_path(active_config)
    execution_records = _execution_records(safe_payload, active_config)
    credential_readiness = _credential_readiness(
        execution_records,
        dict(safe_payload.get("environment") or {}),
    )
    overrides = _overrides_by_execution(safe_payload)
    rehearsed_at = str(safe_payload.get("rehearsed_at") or "local-time")

    if not bool(safe_payload.get("dispatch_requested")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            source=str(safe_payload.get("source") or "local_connector_dispatch"),
            rehearsed_at=rehearsed_at,
            execution_records=execution_records,
            credential_readiness=credential_readiness,
            rehearsal_records=[],
            duplicate_items=[],
            blocked_items=[],
            approval_records=[],
            existing_count=0,
            dispatch_state="blocked_dispatch_not_requested",
            dispatch_requested=False,
            approved_dispatch_review=False,
        )

    if not bool(safe_payload.get("approved_dispatch_review")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            source=str(safe_payload.get("source") or "local_connector_dispatch"),
            rehearsed_at=rehearsed_at,
            execution_records=execution_records,
            credential_readiness=credential_readiness,
            rehearsal_records=[],
            duplicate_items=[],
            blocked_items=[],
            approval_records=[],
            existing_count=0,
            dispatch_state="blocked_until_dispatch_review",
            dispatch_requested=True,
            approved_dispatch_review=False,
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_extra = [dict(item) for item in list(safe_payload.get("existing_rehearsals") or [])]
    existing_keys = _existing_keys(existing_records + existing_extra)

    rehearsal_records: list[dict[str, Any]] = []
    duplicate_items: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []

    for execution in execution_records:
        execution_id = str(execution.get("execution_id") or "")
        override = overrides.get(execution_id)
        block_reason = _block_reason(execution, credential_readiness, override)
        if block_reason:
            blocked_items.append(_blocked_item(execution, block_reason, credential_readiness))
            continue

        record = _rehearsal_record(execution, rehearsed_at)
        if _rehearsal_key(record) in existing_keys:
            duplicate_items.append(_duplicate_item(record))
            continue
        rehearsal_records.append(record)
        existing_keys.add(_rehearsal_key(record))

    if rehearsal_records:
        store.write_collection(active_config.collection, existing_records + rehearsal_records)

    approval_records = _approval_records(
        safe_payload=safe_payload,
        rehearsal_records=rehearsal_records,
        blocked_items=blocked_items,
        reviewer=active_config.reviewer,
        created_at=rehearsed_at,
    )

    if rehearsal_records:
        dispatch_state = "local_rehearsals_written"
    elif duplicate_items:
        dispatch_state = "already_rehearsed"
    elif blocked_items:
        dispatch_state = "no_rehearsable_dispatches"
    else:
        dispatch_state = "empty_execution_manifests"

    return _report(
        config=active_config,
        storage_path=storage_path,
        source=str(safe_payload.get("source") or "local_connector_dispatch"),
        rehearsed_at=rehearsed_at,
        execution_records=execution_records,
        credential_readiness=credential_readiness,
        rehearsal_records=rehearsal_records,
        duplicate_items=duplicate_items,
        blocked_items=blocked_items,
        approval_records=approval_records,
        existing_count=len(existing_records),
        dispatch_state=dispatch_state,
        dispatch_requested=True,
        approved_dispatch_review=True,
    )


def _report(
    config: ConnectorDispatchConfig,
    storage_path: Path,
    source: str,
    rehearsed_at: str,
    execution_records: list[dict[str, Any]],
    credential_readiness: dict[str, dict[str, Any]],
    rehearsal_records: list[dict[str, Any]],
    duplicate_items: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    approval_records: list[dict[str, Any]],
    existing_count: int,
    dispatch_state: str,
    dispatch_requested: bool,
    approved_dispatch_review: bool,
) -> dict[str, Any]:
    return {
        "workflow": "connector_dispatch",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "source": source,
        "rehearsed_at": rehearsed_at,
        "dispatch_state": dispatch_state,
        "summary": {
            "execution_count": len(execution_records),
            "rehearsal_record_count": len(rehearsal_records),
            "duplicate_count": len(duplicate_items),
            "blocked_count": len(blocked_items),
            "approval_record_count": len(approval_records),
            "stored_total_count": existing_count + len(rehearsal_records),
        },
        "rehearsal_records": rehearsal_records,
        "duplicate_items": duplicate_items,
        "blocked_items": blocked_items,
        "approval_records": approval_records,
        "credential_readiness": credential_readiness,
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "dispatch_requested": dispatch_requested,
            "approved_dispatch_review": approved_dispatch_review,
            "record_count": len(rehearsal_records),
            "execution_state": dispatch_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "rehearsal_ids_to_remove": [str(item["rehearsal_id"]) for item in rehearsal_records],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/connector_dispatch_rehearsals.json",
            "notes": [
                "Only local Venus connector dispatch rehearsal records can be written.",
                "Request envelopes are drafts and keep external_action_enabled false.",
                "No Feishu message, Airtable write, Douyin reply, publish action, ad spend, Xingtu commitment, WeChat contact, OpenAI model call, backup write, memory state, or external platform state is changed.",
            ],
        },
    }


def _execution_records(payload: dict[str, Any], config: ConnectorDispatchConfig) -> list[dict[str, Any]]:
    if payload.get("execution_records") is not None:
        return [dict(item) for item in list(payload.get("execution_records") or [])]
    return JsonStore(config.workspace_root).read_collection("connector_execution_manifests")


def _credential_readiness(
    execution_records: list[dict[str, Any]],
    environment: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    refs: list[str] = []
    for record in execution_records:
        for ref in [str(item) for item in list(record.get("required_secret_refs") or [])]:
            if ref not in refs:
                refs.append(ref)
    return {
        ref: {
            "configured": bool(environment.get(f"{ref}_configured")),
            "source": "payload_environment_readiness",
            "secret_value_read": False,
        }
        for ref in refs
    }


def _overrides_by_execution(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed = {}
    for override in [dict(item) for item in list(payload.get("dispatch_overrides") or [])]:
        for key in (
            str(override.get("execution_id") or ""),
            str(override.get("draft_id") or ""),
            str(override.get("action_id") or ""),
        ):
            if key and key not in indexed:
                indexed[key] = override
    return indexed


def _block_reason(
    execution: dict[str, Any],
    credential_readiness: dict[str, dict[str, Any]],
    override: dict[str, Any] | None,
) -> str:
    if override and bool(override.get("external_action_enabled")):
        return "external_override_blocked"
    if bool(execution.get("external_action_enabled")):
        return "external_execution_blocked"
    if str(execution.get("execution_state") or "") != "local_manifest_ready":
        return "execution_not_ready"
    if str(execution.get("dispatch_state") or "") != "blocked_until_live_connector_enabled":
        return "execution_not_ready"
    surface = str(execution.get("target_surface") or "").lower()
    if surface not in REQUEST_TEMPLATES:
        return "unsupported_surface"
    missing = _missing_credentials(execution, credential_readiness)
    if missing:
        return "missing_credential_ref"
    if int(_number(execution.get("approval_level"))) >= 4:
        return "high_risk_dispatch"
    return ""


def _missing_credentials(
    execution: dict[str, Any],
    credential_readiness: dict[str, dict[str, Any]],
) -> list[str]:
    missing = []
    for ref in [str(item) for item in list(execution.get("required_secret_refs") or [])]:
        if not bool(credential_readiness.get(ref, {}).get("configured")):
            missing.append(ref)
    return missing


def _rehearsal_record(execution: dict[str, Any], rehearsed_at: str) -> dict[str, Any]:
    execution_id = str(execution.get("execution_id") or "")
    surface = str(execution.get("target_surface") or "").lower()
    template = REQUEST_TEMPLATES[surface]
    credential_refs = [str(item) for item in list(execution.get("required_secret_refs") or [])]
    rehearsal_id = "-".join(["rehearsal", _slug(execution_id), _slug(surface)])
    return {
        "rehearsal_id": rehearsal_id,
        "execution_id": execution_id,
        "draft_id": str(execution.get("draft_id") or ""),
        "outbox_id": str(execution.get("outbox_id") or ""),
        "action_id": str(execution.get("action_id") or ""),
        "action_type": str(execution.get("action_type") or ""),
        "artifact_type": str(execution.get("artifact_type") or ""),
        "target_surface": surface,
        "connector_id": str(execution.get("connector_id") or ""),
        "connector_type": str(execution.get("connector_type") or ""),
        "adapter_type": str(execution.get("adapter_type") or ""),
        "credential_refs": credential_refs,
        "request_envelope": {
            "method": str(template["method"]),
            "endpoint_label": str(template["endpoint_label"]),
            "headers_by_ref": credential_refs,
            "idempotency_key": rehearsal_id,
            "payload_preview": dict(execution.get("manifest_payload") or {}),
            "external_action_enabled": False,
        },
        "audit_packet": {
            "audit_id": f"audit-{_slug(rehearsal_id)}",
            "source_execution_id": execution_id,
            "surface": surface,
            "rehearsed_at": rehearsed_at,
            "external_action_enabled": False,
        },
        "rollback_packet": {
            "rollback_id": f"rollback-{_slug(rehearsal_id)}",
            "strategy": "no_platform_state_changed",
            "external_action_enabled": False,
        },
        "rehearsed_at": rehearsed_at,
        "dispatch_state": "blocked_until_live_dispatch_enabled",
        "external_action_enabled": False,
    }


def _blocked_item(
    execution: dict[str, Any],
    reason: str,
    credential_readiness: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "execution_id": str(execution.get("execution_id") or ""),
        "draft_id": str(execution.get("draft_id") or ""),
        "action_id": str(execution.get("action_id") or ""),
        "action_type": str(execution.get("action_type") or ""),
        "target_surface": str(execution.get("target_surface") or ""),
        "connector_id": str(execution.get("connector_id") or ""),
        "missing_credentials": _missing_credentials(execution, credential_readiness),
        "skip_reason": reason,
    }


def _duplicate_item(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "rehearsal_id": str(record["rehearsal_id"]),
        "execution_id": str(record["execution_id"]),
        "target_surface": str(record["target_surface"]),
        "skip_reason": "already_rehearsed",
    }


def _approval_records(
    safe_payload: dict[str, Any],
    rehearsal_records: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    evidence_ids = [str(item.get("rehearsal_id") or "") for item in rehearsal_records]
    evidence_ids.extend(str(item.get("execution_id") or "") for item in blocked_items)
    evidence_ids = [item for item in evidence_ids if item]

    if bool(safe_payload.get("live_dispatch_requested")):
        records.append(
            create_approval_record(
                action_type="venus_live_connector_dispatch_rehearsal_review",
                approval_level=4,
                draft="Review dispatch rehearsal request envelopes before any live connector dispatch is enabled.",
                evidence_ids=evidence_ids,
                reviewer=reviewer,
                created_at=created_at,
            )
        )

    high_risk = [item for item in blocked_items if item["skip_reason"] == "high_risk_dispatch"]
    if high_risk:
        records.append(
            create_approval_record(
                action_type="venus_high_risk_dispatch_rehearsal_review",
                approval_level=4,
                draft="Review high-risk dispatch candidates before any public reply, ad spend, brand commitment, WeChat contact, model call, or backup write is enabled.",
                evidence_ids=[str(item["execution_id"]) for item in high_risk],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_rehearsal_key(record) for record in records}


def _rehearsal_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("rehearsal_id") or ""),
            str(item.get("execution_id") or ""),
            str(item.get("target_surface") or ""),
        ]
    )


def _storage_path(config: ConnectorDispatchConfig) -> Path:
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
