from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.airtable_export import build_airtable_sync_package
from venus.storage import JsonStore


REQUIRED_AIRTABLE_PERMISSIONS = {"base_read", "record_write"}
READY_VALUES = {"ready", "configured", "enabled", "true"}
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
class AirtableSyncPlanConfig:
    workspace_root: Path | str
    namespace: str = "venus_airtable_sync"
    collection: str = "airtable_sync_plans"
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
            raise ValueError("Venus Airtable sync config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus Airtable sync namespace must start with venus_")
        if self.collection != "airtable_sync_plans":
            raise ValueError("Venus Airtable sync collection must be airtable_sync_plans")
        if not self.external_dry_run:
            raise ValueError("Venus Airtable sync must keep external actions in dry-run mode")


def build_airtable_sync_plan(
    payload: dict[str, Any],
    config: AirtableSyncPlanConfig | None = None,
) -> dict[str, Any]:
    safe_payload = _redact(payload)
    workspace_root = safe_payload.get("workspace_root") or "."
    active_config = config or AirtableSyncPlanConfig(workspace_root=workspace_root)
    package = _airtable_package(safe_payload)
    tables = [dict(item) for item in list(package.get("tables") or [])]
    storage_path = _storage_path(active_config)

    if not bool(safe_payload.get("sync_requested")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            package=package,
            tables=tables,
            sync_plan_records=[],
            duplicate_items=[],
            blocked_tables=[],
            existing_count=0,
            sync_state="blocked_sync_not_requested",
            execution_state="blocked_sync_not_requested",
            sync_requested=False,
            approved_sync_review=False,
        )
    if not bool(safe_payload.get("approved_sync_review")):
        return _report(
            config=active_config,
            storage_path=storage_path,
            package=package,
            tables=tables,
            sync_plan_records=[],
            duplicate_items=[],
            blocked_tables=[],
            existing_count=0,
            sync_state="blocked_until_sync_review",
            execution_state="blocked_until_sync_review",
            sync_requested=True,
            approved_sync_review=False,
        )

    connector = _ready_airtable_connector(safe_payload)
    if connector is None:
        blocked = [_blocked_table(table, "connector_not_ready") for table in tables]
        return _report(
            config=active_config,
            storage_path=storage_path,
            package=package,
            tables=tables,
            sync_plan_records=[],
            duplicate_items=[],
            blocked_tables=blocked,
            existing_count=0,
            sync_state="blocked_connector_not_ready",
            execution_state="blocked_connector_not_ready",
            sync_requested=True,
            approved_sync_review=True,
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_extra = [dict(item) for item in list(safe_payload.get("existing_sync_plans") or [])]
    existing_keys = _existing_keys(existing_records + existing_extra)

    sync_plan_records: list[dict[str, Any]] = []
    duplicate_items: list[dict[str, Any]] = []
    blocked_tables: list[dict[str, Any]] = []
    planned_at = str(safe_payload.get("planned_at") or "local-time")

    for table in tables:
        reason = _table_block_reason(table, package)
        if reason:
            blocked_tables.append(_blocked_table(table, reason))
            continue
        record = _sync_plan_record(table, package, connector, planned_at)
        if _sync_key(record) in existing_keys:
            duplicate_items.append(_duplicate_item(record))
            continue
        sync_plan_records.append(record)
        existing_keys.add(_sync_key(record))

    if sync_plan_records:
        store.write_collection(active_config.collection, existing_records + sync_plan_records)

    if sync_plan_records:
        sync_state = "planned"
    elif duplicate_items:
        sync_state = "already_planned"
    elif blocked_tables:
        sync_state = "no_plannable_tables"
    else:
        sync_state = "empty_airtable_package"

    return _report(
        config=active_config,
        storage_path=storage_path,
        package=package,
        tables=tables,
        sync_plan_records=sync_plan_records,
        duplicate_items=duplicate_items,
        blocked_tables=blocked_tables,
        existing_count=len(existing_records),
        sync_state=sync_state,
        execution_state="local_airtable_sync_plan_written" if sync_plan_records else sync_state,
        sync_requested=True,
        approved_sync_review=True,
    )


def _report(
    config: AirtableSyncPlanConfig,
    storage_path: Path,
    package: dict[str, Any],
    tables: list[dict[str, Any]],
    sync_plan_records: list[dict[str, Any]],
    duplicate_items: list[dict[str, Any]],
    blocked_tables: list[dict[str, Any]],
    existing_count: int,
    sync_state: str,
    execution_state: str,
    sync_requested: bool,
    approved_sync_review: bool,
) -> dict[str, Any]:
    return {
        "workflow": "airtable_sync_plan",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "sync_state": sync_state,
        "summary": {
            "table_count": len(tables),
            "planned_count": len(sync_plan_records),
            "duplicate_count": len(duplicate_items),
            "blocked_count": len(blocked_tables),
            "record_count": sum(len(list(table.get("records") or [])) for table in tables),
            "stored_total_count": existing_count + len(sync_plan_records),
        },
        "base": dict(package.get("base") or {}),
        "sync_plan_records": sync_plan_records,
        "duplicate_items": duplicate_items,
        "blocked_tables": blocked_tables,
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "sync_requested": sync_requested,
            "approved_sync_review": approved_sync_review,
            "record_count": len(sync_plan_records),
            "execution_state": execution_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "sync_plan_ids_to_remove": [str(item["sync_plan_id"]) for item in sync_plan_records],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/airtable_sync_plans.json",
            "notes": [
                "Only local Venus Airtable sync plan records can be written.",
                "No Airtable base, table, field, view, automation, interface, or record is created or updated.",
                "A future live adapter must re-check connector permissions, approval status, audit logging, and rollback readiness before writing to Airtable.",
            ],
        },
    }


def _airtable_package(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("airtable_package") is not None:
        return dict(payload.get("airtable_package") or {})
    return build_airtable_sync_package(payload)


def _ready_airtable_connector(payload: dict[str, Any]) -> dict[str, Any] | None:
    connectors = [dict(item) for item in list(payload.get("connector_reviews") or [])]
    for connector in connectors:
        if str(connector.get("surface") or "").lower() != "airtable":
            continue
        if bool(connector.get("external_action_enabled")):
            continue
        if str(connector.get("status") or "").lower() != "ready":
            continue
        granted = {str(item) for item in list(connector.get("permissions_granted") or [])}
        if not REQUIRED_AIRTABLE_PERMISSIONS.issubset(granted):
            continue
        if not _ready_flag(connector.get("audit_ready", connector.get("audit_log"))):
            continue
        if not _ready_flag(connector.get("rollback_ready", connector.get("rollback"))):
            continue
        return connector
    return None


def _ready_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in READY_VALUES


def _table_block_reason(table: dict[str, Any], package: dict[str, Any]) -> str:
    base = dict(package.get("base") or {})
    namespace = str(base.get("namespace") or "")
    if not namespace.startswith("venus_"):
        return "unsupported_base_namespace"
    if bool(table.get("external_action_enabled")):
        return "external_table_action_enabled"
    if not str(table.get("name") or ""):
        return "missing_table_name"
    field_names = {str(field.get("name") or "") for field in list(table.get("fields") or [])}
    if not field_names:
        return "missing_field_definitions"
    for record in list(table.get("records") or []):
        record_fields = set(dict(record.get("fields") or {}).keys())
        if not record_fields.issubset(field_names):
            return "schema_field_mismatch"
    return ""


def _sync_plan_record(
    table: dict[str, Any],
    package: dict[str, Any],
    connector: dict[str, Any],
    planned_at: str,
) -> dict[str, Any]:
    base = dict(package.get("base") or {})
    table_name = str(table.get("name") or "")
    records = [dict(item) for item in list(table.get("records") or [])]
    fields = [dict(item) for item in list(table.get("fields") or [])]
    return {
        "sync_plan_id": "-".join(["airtable-sync", _slug(table_name), _slug(planned_at)]),
        "base_name": str(base.get("name") or ""),
        "base_namespace": str(base.get("namespace") or ""),
        "connector_id": str(connector.get("connector_id") or "airtable"),
        "table_name": table_name,
        "planned_operation": "create_or_update_records",
        "record_count": len(records),
        "field_count": len(fields),
        "record_preview_names": _record_preview_names(records),
        "rollback_strategy": "manual_restore_from_airtable_snapshot",
        "planned_at": planned_at,
        "execution_state": "local_sync_plan_ready",
        "external_action_enabled": False,
    }


def _record_preview_names(records: list[dict[str, Any]]) -> list[str]:
    names = []
    for record in records[:5]:
        fields = dict(record.get("fields") or {})
        names.append(str(fields.get("Name") or fields.get("Topic") or fields.get("Product") or "record"))
    return names


def _blocked_table(table: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "table_name": str(table.get("name") or ""),
        "record_count": len(list(table.get("records") or [])),
        "skip_reason": reason,
    }


def _duplicate_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "sync_plan_id": str(item["sync_plan_id"]),
        "table_name": str(item["table_name"]),
        "planned_operation": str(item["planned_operation"]),
        "skip_reason": "already_planned",
    }


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_sync_key(record) for record in records}


def _sync_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("sync_plan_id") or ""),
            str(item.get("base_namespace") or ""),
            str(item.get("table_name") or ""),
            str(item.get("planned_operation") or ""),
        ]
    )


def _storage_path(config: AirtableSyncPlanConfig) -> Path:
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
