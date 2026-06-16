from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.storage import JsonStore


QUEUEABLE_LOCAL_ACTIONS = {"feishu_mobile_report", "airtable_sync_review"}
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
class ActionOutboxConfig:
    workspace_root: Path | str
    namespace: str = "venus_action_outbox"
    collection: str = "action_outbox"
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
            raise ValueError("Venus action outbox config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus action outbox namespace must start with venus_")
        if self.collection != "action_outbox":
            raise ValueError("Venus action outbox collection must be action_outbox")
        if not self.external_dry_run:
            raise ValueError("Venus action outbox must keep external actions in dry-run mode")


def build_action_outbox(
    payload: dict[str, Any],
    config: ActionOutboxConfig | None = None,
) -> dict[str, Any]:
    safe_payload = _redact(payload)
    workspace_root = safe_payload.get("workspace_root") or "."
    active_config = config or ActionOutboxConfig(workspace_root=workspace_root)
    storage_path = _storage_path(active_config)
    action_plan = [dict(item) for item in list(safe_payload.get("action_plan") or [])]
    archived_decisions = _archived_decisions(safe_payload, active_config)
    decision_by_action = _decision_by_action(archived_decisions)

    if not bool(safe_payload.get("execution_requested")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            action_plan=action_plan,
            queued_items=[],
            duplicate_items=[],
            blocked_items=[],
            rejected_items=[],
            missing_decision_items=[],
            existing_count=0,
            outbox_state="blocked_execution_not_requested",
            execution_state="blocked_execution_not_requested",
            execution_requested=False,
            approved_execution_review=False,
        )
    if not bool(safe_payload.get("approved_execution_review")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            action_plan=action_plan,
            queued_items=[],
            duplicate_items=[],
            blocked_items=[],
            rejected_items=[],
            missing_decision_items=[],
            existing_count=0,
            outbox_state="blocked_until_execution_review",
            execution_state="blocked_until_execution_review",
            execution_requested=True,
            approved_execution_review=False,
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_outbox_items = [
        dict(item) for item in list(safe_payload.get("existing_outbox_items") or [])
    ]
    existing_keys = _existing_keys(existing_records + existing_outbox_items)

    queued_items: list[dict[str, Any]] = []
    duplicate_items: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []
    rejected_items: list[dict[str, Any]] = []
    missing_decision_items: list[dict[str, Any]] = []

    for action in action_plan:
        action_type = str(action.get("action_type") or "")
        decision = decision_by_action.get(action_type)
        if not decision:
            missing_decision_items.append(_skipped_action(action, "missing_archived_approval"))
            continue
        if str(decision.get("decision") or "").lower() != "approve":
            rejected_items.append(_skipped_action(action, "decision_not_approved", decision))
            continue
        if _is_external_or_high_risk(action, decision):
            blocked_items.append(_skipped_action(action, "external_or_high_risk_action", decision))
            continue

        outbox_item = _outbox_item(action, decision, str(safe_payload.get("queued_at") or "local-time"))
        if _outbox_key(outbox_item) in existing_keys:
            duplicate_items.append(_duplicate_item(outbox_item))
            continue
        queued_items.append(outbox_item)
        existing_keys.add(_outbox_key(outbox_item))

    if queued_items:
        store.write_collection(active_config.collection, existing_records + queued_items)

    if queued_items:
        outbox_state = "queued"
    elif duplicate_items:
        outbox_state = "already_queued"
    elif blocked_items or rejected_items or missing_decision_items:
        outbox_state = "no_queueable_actions"
    else:
        outbox_state = "empty_action_plan"

    return _report(
        config=active_config,
        storage_path=storage_path,
        action_plan=action_plan,
        queued_items=queued_items,
        duplicate_items=duplicate_items,
        blocked_items=blocked_items,
        rejected_items=rejected_items,
        missing_decision_items=missing_decision_items,
        existing_count=len(existing_records),
        outbox_state=outbox_state,
        execution_state="local_outbox_written" if queued_items else outbox_state,
        execution_requested=True,
        approved_execution_review=True,
    )


def _report(
    config: ActionOutboxConfig,
    storage_path: Path,
    action_plan: list[dict[str, Any]],
    queued_items: list[dict[str, Any]],
    duplicate_items: list[dict[str, Any]],
    blocked_items: list[dict[str, Any]],
    rejected_items: list[dict[str, Any]],
    missing_decision_items: list[dict[str, Any]],
    existing_count: int,
    outbox_state: str,
    execution_state: str,
    execution_requested: bool,
    approved_execution_review: bool,
) -> dict[str, Any]:
    stored_total_count = existing_count + len(queued_items)
    return {
        "workflow": "action_outbox",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "outbox_state": outbox_state,
        "summary": {
            "action_count": len(action_plan),
            "queued_count": len(queued_items),
            "duplicate_count": len(duplicate_items),
            "blocked_count": len(blocked_items),
            "rejected_count": len(rejected_items),
            "missing_decision_count": len(missing_decision_items),
            "stored_total_count": stored_total_count,
        },
        "queued_items": queued_items,
        "duplicate_items": duplicate_items,
        "blocked_items": blocked_items,
        "rejected_items": rejected_items,
        "missing_decision_items": missing_decision_items,
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "execution_requested": execution_requested,
            "approved_execution_review": approved_execution_review,
            "record_count": len(queued_items),
            "execution_state": execution_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "outbox_ids_to_remove": [str(item["outbox_id"]) for item in queued_items],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/action_outbox.json",
            "notes": [
                "Only local Venus JSON outbox records can be written.",
                "Outbox delivery remains local_manual_dispatch_required.",
                "No Feishu message, Airtable write, Douyin reply, publish action, ad spend, brand task, WeChat contact, memory state, backup state, or external platform state is changed.",
            ],
        },
    }


def _archived_decisions(payload: dict[str, Any], config: ActionOutboxConfig) -> list[dict[str, Any]]:
    if payload.get("archived_decisions") is not None:
        return [dict(item) for item in list(payload.get("archived_decisions") or [])]
    store = JsonStore(config.workspace_root)
    return store.read_collection("approval_decision_ledger")


def _decision_by_action(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if str(decision.get("archive_state") or "") != "archived":
            continue
        action_type = str(decision.get("action_type") or "")
        if action_type not in indexed:
            indexed[action_type] = decision
    return indexed


def _is_external_or_high_risk(action: dict[str, Any], decision: dict[str, Any]) -> bool:
    action_type = str(action.get("action_type") or "")
    action_level = int(_number(action.get("approval_level")))
    decision_level = int(_number(decision.get("approval_level")))
    return (
        bool(action.get("external_action_enabled"))
        or action_type not in QUEUEABLE_LOCAL_ACTIONS
        or max(action_level, decision_level) > 2
    )


def _outbox_item(action: dict[str, Any], decision: dict[str, Any], queued_at: str) -> dict[str, Any]:
    action_type = str(action.get("action_type") or "")
    action_id = str(action.get("action_id") or action_type)
    decision_id = str(decision.get("decision_id") or "")
    return {
        "outbox_id": "-".join(["outbox", _slug(action_type), _slug(action_id), _slug(decision_id)]),
        "action_id": action_id,
        "action_type": action_type,
        "surface": str(action.get("surface") or "local"),
        "approval_level": int(_number(action.get("approval_level"))),
        "decision_id": decision_id,
        "matched_approval_id": str(decision.get("matched_approval_id") or ""),
        "reviewer": str(decision.get("reviewer") or "owner"),
        "draft": str(action.get("draft") or ""),
        "queued_at": queued_at,
        "execution_state": "queued_local_outbox",
        "delivery_state": "local_manual_dispatch_required",
        "external_action_enabled": False,
    }


def _skipped_action(
    action: dict[str, Any],
    reason: str,
    decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = {
        "action_id": str(action.get("action_id") or action.get("action_type") or ""),
        "action_type": str(action.get("action_type") or ""),
        "surface": str(action.get("surface") or ""),
        "approval_level": int(_number(action.get("approval_level"))),
        "skip_reason": reason,
    }
    if decision is not None:
        data["decision_id"] = str(decision.get("decision_id") or "")
        data["decision"] = str(decision.get("decision") or "")
    return data


def _duplicate_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "outbox_id": str(item["outbox_id"]),
        "action_id": str(item["action_id"]),
        "action_type": str(item["action_type"]),
        "skip_reason": "already_queued",
    }


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_outbox_key(record) for record in records}


def _outbox_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("outbox_id") or ""),
            str(item.get("action_type") or ""),
            str(item.get("action_id") or ""),
            str(item.get("decision_id") or ""),
        ]
    )


def _storage_path(config: ActionOutboxConfig) -> Path:
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
