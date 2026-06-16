from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.storage import JsonStore


ALLOWED_STATUSES = {
    "manual_dispatch_completed": "closed_manual_delivery",
    "returned_for_revision": "needs_revision",
    "blocked_after_review": "blocked_manual_review",
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
class DeliveryStatusConfig:
    workspace_root: Path | str
    namespace: str = "venus_delivery_status"
    collection: str = "delivery_status"
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
            raise ValueError("Venus delivery status config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus delivery status namespace must start with venus_")
        if self.collection != "delivery_status":
            raise ValueError("Venus delivery status collection must be delivery_status")
        if not self.external_dry_run:
            raise ValueError("Venus delivery status must keep external actions in dry-run mode")


def build_delivery_status(
    payload: dict[str, Any],
    config: DeliveryStatusConfig | None = None,
) -> dict[str, Any]:
    safe_payload = _redact(payload)
    workspace_root = safe_payload.get("workspace_root") or "."
    active_config = config or DeliveryStatusConfig(workspace_root=workspace_root)
    storage_path = _storage_path(active_config)
    draft_records = _draft_records(safe_payload, active_config)
    status_events = [dict(item) for item in list(safe_payload.get("status_events") or [])]

    if not bool(safe_payload.get("status_update_requested")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            draft_records=draft_records,
            status_events=status_events,
            status_records=[],
            duplicate_items=[],
            blocked_items=[],
            existing_count=0,
            status_state="blocked_status_not_requested",
            execution_state="blocked_status_not_requested",
            status_update_requested=False,
            approved_status_review=False,
        )
    if not bool(safe_payload.get("approved_status_review")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            draft_records=draft_records,
            status_events=status_events,
            status_records=[],
            duplicate_items=[],
            blocked_items=[],
            existing_count=0,
            status_state="blocked_until_status_review",
            execution_state="blocked_until_status_review",
            status_update_requested=True,
            approved_status_review=False,
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_extra = [dict(item) for item in list(safe_payload.get("existing_delivery_statuses") or [])]
    existing_keys = _existing_keys(existing_records + existing_extra)
    drafts_by_key = _drafts_by_key(draft_records)

    status_records: list[dict[str, Any]] = []
    duplicate_items: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []
    recorded_at = str(safe_payload.get("recorded_at") or "local-time")

    for event in status_events:
        draft = _matching_draft(event, drafts_by_key)
        block_reason = _block_reason(event, draft)
        if block_reason:
            blocked_items.append(_blocked_event(event, block_reason))
            continue
        assert draft is not None
        record = _status_record(event, draft, recorded_at)
        if _status_key(record) in existing_keys:
            duplicate_items.append(_duplicate_item(record))
            continue
        status_records.append(record)
        existing_keys.add(_status_key(record))

    if status_records:
        store.write_collection(active_config.collection, existing_records + status_records)

    if status_records:
        status_state = "recorded"
    elif duplicate_items:
        status_state = "already_recorded"
    elif blocked_items:
        status_state = "no_recordable_statuses"
    else:
        status_state = "empty_status_events"

    return _report(
        config=active_config,
        storage_path=storage_path,
        draft_records=draft_records,
        status_events=status_events,
        status_records=status_records,
        duplicate_items=duplicate_items,
        blocked_items=blocked_items,
        existing_count=len(existing_records),
        status_state=status_state,
        execution_state="local_delivery_status_written" if status_records else status_state,
        status_update_requested=True,
        approved_status_review=True,
    )


def _report(
    config: DeliveryStatusConfig,
    storage_path: Path,
    draft_records: list[dict[str, Any]],
    status_events: list[dict[str, Any]],
    status_records: list[dict[str, Any]],
    duplicate_items: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    existing_count: int,
    status_state: str,
    execution_state: str,
    status_update_requested: bool,
    approved_status_review: bool,
) -> dict[str, Any]:
    return {
        "workflow": "delivery_status",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "status_state": status_state,
        "summary": {
            "draft_count": len(draft_records),
            "status_event_count": len(status_events),
            "recorded_count": len(status_records),
            "duplicate_count": len(duplicate_items),
            "blocked_count": len(blocked_items),
            "stored_total_count": existing_count + len(status_records),
        },
        "status_records": status_records,
        "duplicate_items": duplicate_items,
        "blocked_items": blocked_items,
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "status_update_requested": status_update_requested,
            "approved_status_review": approved_status_review,
            "record_count": len(status_records),
            "execution_state": execution_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "status_ids_to_remove": [str(item["status_id"]) for item in status_records],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/delivery_status.json",
            "notes": [
                "Only local Venus delivery status records can be written.",
                "Status records describe manual operator review outcomes only.",
                "No Feishu message, Airtable write, Douyin reply, publish action, ad spend, brand task, WeChat contact, memory state, backup state, or external platform state is changed.",
            ],
        },
    }


def _draft_records(payload: dict[str, Any], config: DeliveryStatusConfig) -> list[dict[str, Any]]:
    if payload.get("draft_records") is not None:
        return [dict(item) for item in list(payload.get("draft_records") or [])]
    return JsonStore(config.workspace_root).read_collection("delivery_drafts")


def _drafts_by_key(drafts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for draft in drafts:
        for key in (str(draft.get("draft_id") or ""), str(draft.get("outbox_id") or "")):
            if key and key not in indexed:
                indexed[key] = draft
    return indexed


def _matching_draft(
    event: dict[str, Any],
    drafts_by_key: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for key in (str(event.get("draft_id") or ""), str(event.get("outbox_id") or "")):
        if key in drafts_by_key:
            return drafts_by_key[key]
    return None


def _block_reason(event: dict[str, Any], draft: dict[str, Any] | None) -> str:
    if draft is None:
        return "missing_delivery_draft"
    if bool(event.get("external_action_enabled")):
        return "external_delivery_event"
    if str(event.get("delivery_status") or "") not in ALLOWED_STATUSES:
        return "unsupported_delivery_status"
    if bool(draft.get("external_action_enabled")):
        return "draft_not_local_review"
    if str(draft.get("dispatch_state") or "") != "local_review_required":
        return "draft_not_local_review"
    return ""


def _status_record(event: dict[str, Any], draft: dict[str, Any], recorded_at: str) -> dict[str, Any]:
    delivery_status = str(event.get("delivery_status") or "")
    event_time = str(event.get("event_time") or recorded_at)
    draft_id = str(draft.get("draft_id") or event.get("draft_id") or "")
    return {
        "status_id": "-".join(
            ["status", _slug(draft_id), _slug(delivery_status), _slug(event_time)]
        ),
        "draft_id": draft_id,
        "outbox_id": str(draft.get("outbox_id") or event.get("outbox_id") or ""),
        "action_id": str(draft.get("action_id") or ""),
        "action_type": str(draft.get("action_type") or ""),
        "artifact_type": str(draft.get("artifact_type") or ""),
        "target_surface": str(draft.get("target_surface") or ""),
        "delivery_status": delivery_status,
        "follow_up_state": ALLOWED_STATUSES[delivery_status],
        "reviewer": str(event.get("reviewer") or "owner"),
        "event_time": event_time,
        "recorded_at": recorded_at,
        "notes": str(event.get("notes") or ""),
        "evidence_ids": [str(item) for item in list(event.get("evidence_ids") or [])],
        "audit_state": "local_status_recorded",
        "external_action_enabled": False,
    }


def _blocked_event(event: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "draft_id": str(event.get("draft_id") or ""),
        "outbox_id": str(event.get("outbox_id") or ""),
        "delivery_status": str(event.get("delivery_status") or ""),
        "skip_reason": reason,
    }


def _duplicate_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "status_id": str(item["status_id"]),
        "draft_id": str(item["draft_id"]),
        "delivery_status": str(item["delivery_status"]),
        "event_time": str(item["event_time"]),
        "skip_reason": "already_recorded",
    }


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_status_key(record) for record in records}


def _status_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("status_id") or ""),
            str(item.get("draft_id") or ""),
            str(item.get("delivery_status") or ""),
            str(item.get("event_time") or ""),
        ]
    )


def _storage_path(config: DeliveryStatusConfig) -> Path:
    return Path(config.workspace_root) / "data" / "venus" / f"{config.collection}.json"


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "-" for ch in value).strip("-")


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
