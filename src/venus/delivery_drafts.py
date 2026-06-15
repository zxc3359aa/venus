from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.storage import JsonStore


SUPPORTED_ADAPTERS = {
    "feishu_mobile_report": "feishu_card_draft",
    "airtable_sync_review": "airtable_record_package",
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
class DeliveryDraftConfig:
    workspace_root: Path | str
    namespace: str = "venus_delivery_drafts"
    collection: str = "delivery_drafts"
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
            raise ValueError("Venus delivery draft config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus delivery draft namespace must start with venus_")
        if self.collection != "delivery_drafts":
            raise ValueError("Venus delivery draft collection must be delivery_drafts")
        if not self.external_dry_run:
            raise ValueError("Venus delivery drafts must keep external actions in dry-run mode")


def build_delivery_drafts(
    payload: dict[str, Any],
    config: DeliveryDraftConfig | None = None,
) -> dict[str, Any]:
    safe_payload = _redact(payload)
    workspace_root = safe_payload.get("workspace_root") or "."
    active_config = config or DeliveryDraftConfig(workspace_root=workspace_root)
    outbox_items = _outbox_items(safe_payload, active_config)
    storage_path = _storage_path(active_config)

    if not bool(safe_payload.get("delivery_requested")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            outbox_items=outbox_items,
            draft_records=[],
            duplicate_items=[],
            blocked_items=[],
            existing_count=0,
            delivery_state="blocked_delivery_not_requested",
            execution_state="blocked_delivery_not_requested",
            delivery_requested=False,
            approved_delivery_review=False,
        )
    if not bool(safe_payload.get("approved_delivery_review")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            outbox_items=outbox_items,
            draft_records=[],
            duplicate_items=[],
            blocked_items=[],
            existing_count=0,
            delivery_state="blocked_until_delivery_review",
            execution_state="blocked_until_delivery_review",
            delivery_requested=True,
            approved_delivery_review=False,
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_extra = [dict(item) for item in list(safe_payload.get("existing_delivery_drafts") or [])]
    existing_keys = _existing_keys(existing_records + existing_extra)

    draft_records: list[dict[str, Any]] = []
    duplicate_items: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []

    for item in outbox_items:
        if _should_block(item):
            blocked_items.append(_blocked_item(item, "external_or_unsupported_delivery"))
            continue
        draft = _draft_record(item, str(safe_payload.get("drafted_at") or "local-time"))
        if _draft_key(draft) in existing_keys:
            duplicate_items.append(_duplicate_item(draft))
            continue
        draft_records.append(draft)
        existing_keys.add(_draft_key(draft))

    if draft_records:
        store.write_collection(active_config.collection, existing_records + draft_records)

    if draft_records:
        delivery_state = "drafted"
    elif duplicate_items:
        delivery_state = "already_drafted"
    elif blocked_items:
        delivery_state = "no_supported_delivery_drafts"
    else:
        delivery_state = "empty_outbox"

    return _report(
        config=active_config,
        storage_path=storage_path,
        outbox_items=outbox_items,
        draft_records=draft_records,
        duplicate_items=duplicate_items,
        blocked_items=blocked_items,
        existing_count=len(existing_records),
        delivery_state=delivery_state,
        execution_state="local_delivery_drafts_written" if draft_records else delivery_state,
        delivery_requested=True,
        approved_delivery_review=True,
    )


def _report(
    config: DeliveryDraftConfig,
    storage_path: Path,
    outbox_items: list[dict[str, Any]],
    draft_records: list[dict[str, Any]],
    duplicate_items: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    existing_count: int,
    delivery_state: str,
    execution_state: str,
    delivery_requested: bool,
    approved_delivery_review: bool,
) -> dict[str, Any]:
    return {
        "workflow": "delivery_drafts",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "delivery_state": delivery_state,
        "summary": {
            "outbox_item_count": len(outbox_items),
            "drafted_count": len(draft_records),
            "duplicate_count": len(duplicate_items),
            "blocked_count": len(blocked_items),
            "stored_total_count": existing_count + len(draft_records),
        },
        "draft_records": draft_records,
        "duplicate_items": duplicate_items,
        "blocked_items": blocked_items,
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "delivery_requested": delivery_requested,
            "approved_delivery_review": approved_delivery_review,
            "record_count": len(draft_records),
            "execution_state": execution_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "draft_ids_to_remove": [str(item["draft_id"]) for item in draft_records],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/delivery_drafts.json",
            "notes": [
                "Only local Venus delivery draft records can be written.",
                "Draft dispatch remains local_review_required.",
                "No Feishu message, Airtable write, Douyin reply, publish action, ad spend, brand task, WeChat contact, memory state, backup state, or external platform state is changed.",
            ],
        },
    }


def _outbox_items(payload: dict[str, Any], config: DeliveryDraftConfig) -> list[dict[str, Any]]:
    if payload.get("outbox_items") is not None:
        return [dict(item) for item in list(payload.get("outbox_items") or [])]
    return JsonStore(config.workspace_root).read_collection("action_outbox")


def _should_block(item: dict[str, Any]) -> bool:
    action_type = str(item.get("action_type") or "")
    return (
        action_type not in SUPPORTED_ADAPTERS
        or bool(item.get("external_action_enabled"))
        or str(item.get("delivery_state") or "") != "local_manual_dispatch_required"
        or int(_number(item.get("approval_level"))) > 2
    )


def _draft_record(item: dict[str, Any], drafted_at: str) -> dict[str, Any]:
    action_type = str(item.get("action_type") or "")
    artifact_type = SUPPORTED_ADAPTERS[action_type]
    draft_id = "-".join(["draft", _slug(str(item.get("outbox_id") or action_type))])
    return {
        "draft_id": draft_id,
        "outbox_id": str(item.get("outbox_id") or ""),
        "action_id": str(item.get("action_id") or action_type),
        "action_type": action_type,
        "artifact_type": artifact_type,
        "target_surface": str(item.get("surface") or "local"),
        "draft_payload": _draft_payload(item, artifact_type),
        "drafted_at": drafted_at,
        "dispatch_state": "local_review_required",
        "external_action_enabled": False,
    }


def _draft_payload(item: dict[str, Any], artifact_type: str) -> dict[str, Any]:
    if artifact_type == "feishu_card_draft":
        return {
            "card": {
                "title": "Venus private report",
                "summary": str(item.get("draft") or ""),
                "facts": {
                    "action_type": str(item.get("action_type") or ""),
                    "approval_level": int(_number(item.get("approval_level"))),
                    "reviewer": str(item.get("reviewer") or "owner"),
                },
                "body": str(item.get("draft") or ""),
            },
            "manual_copy_only": True,
        }
    return {
        "table": "Action Reviews",
        "records": [
            {
                "fields": {
                    "Action Type": str(item.get("action_type") or ""),
                    "Action ID": str(item.get("action_id") or ""),
                    "Approval Level": int(_number(item.get("approval_level"))),
                    "Draft": str(item.get("draft") or ""),
                    "Outbox ID": str(item.get("outbox_id") or ""),
                }
            }
        ],
        "manual_import_only": True,
    }


def _blocked_item(item: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "outbox_id": str(item.get("outbox_id") or ""),
        "action_id": str(item.get("action_id") or item.get("action_type") or ""),
        "action_type": str(item.get("action_type") or ""),
        "target_surface": str(item.get("surface") or ""),
        "skip_reason": reason,
    }


def _duplicate_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "draft_id": str(item["draft_id"]),
        "outbox_id": str(item["outbox_id"]),
        "action_type": str(item["action_type"]),
        "skip_reason": "already_drafted",
    }


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_draft_key(record) for record in records}


def _draft_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("draft_id") or ""),
            str(item.get("outbox_id") or ""),
            str(item.get("action_type") or ""),
        ]
    )


def _storage_path(config: DeliveryDraftConfig) -> Path:
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
