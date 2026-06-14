from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from venus.approval_ledger import build_approval_ledger
from venus.storage import JsonStore


@dataclass(frozen=True)
class ApprovalArchiveConfig:
    workspace_root: Path | str
    namespace: str = "venus_approval_archive"
    collection: str = "approval_decision_ledger"
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
            raise ValueError("Venus approval archive config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus approval archive namespace must start with venus_")
        if self.collection != "approval_decision_ledger":
            raise ValueError("Venus approval archive collection must be approval_decision_ledger")
        if not self.external_dry_run:
            raise ValueError("Venus approval archive must keep external actions in dry-run mode")


def build_approval_archive(
    payload: dict[str, Any],
    config: ApprovalArchiveConfig | None = None,
) -> dict[str, Any]:
    workspace_root = payload.get("workspace_root") or "."
    active_config = config or ApprovalArchiveConfig(workspace_root=workspace_root)
    ledger = build_approval_ledger(payload)
    storage_path = _storage_path(active_config)
    ready_entries = [
        dict(entry)
        for entry in ledger["ledger_entries"]
        if entry["record_state"] == "ready_for_local_ledger_review"
    ]
    skipped_entries = [
        _skipped_entry(entry, "requires_second_review")
        for entry in ledger["ledger_entries"]
        if entry["record_state"] == "blocked_for_second_review"
    ]

    archive_requested = bool(payload.get("archive_requested"))
    approved_write = bool(payload.get("approved_ledger_write_review"))
    if not archive_requested:
        return _report(
            config=active_config,
            ledger=ledger,
            storage_path=storage_path,
            archive_state="blocked_archive_not_requested",
            archived_entries=[],
            duplicate_entries=[],
            skipped_entries=skipped_entries,
            existing_count=0,
            execution_state="blocked_archive_not_requested",
        )
    if not approved_write:
        return _report(
            config=active_config,
            ledger=ledger,
            storage_path=storage_path,
            archive_state="blocked_until_ledger_write_review",
            archived_entries=[],
            duplicate_entries=[],
            skipped_entries=skipped_entries,
            existing_count=0,
            execution_state="blocked_until_ledger_write_review",
        )

    store = JsonStore(active_config.workspace_root)
    existing_records = store.read_collection(active_config.collection)
    existing_keys = _existing_keys(existing_records)
    archived_entries: list[dict[str, Any]] = []
    duplicate_entries: list[dict[str, Any]] = []

    for entry in ready_entries:
        if _entry_key(entry) in existing_keys:
            duplicate_entries.append(_skipped_entry(entry, "already_archived"))
            continue
        archived_entry = dict(entry)
        archived_entry["archive_state"] = "archived"
        archived_entries.append(archived_entry)
        existing_keys.add(_entry_key(archived_entry))

    if archived_entries:
        store.write_collection(active_config.collection, existing_records + archived_entries)

    if archived_entries:
        archive_state = "archived"
    elif duplicate_entries:
        archive_state = "already_archived"
    else:
        archive_state = "no_ready_entries_to_archive"

    return _report(
        config=active_config,
        ledger=ledger,
        storage_path=storage_path,
        archive_state=archive_state,
        archived_entries=archived_entries,
        duplicate_entries=duplicate_entries,
        skipped_entries=skipped_entries,
        existing_count=len(existing_records),
        execution_state="local_archive_written" if archived_entries else archive_state,
    )


def _report(
    config: ApprovalArchiveConfig,
    ledger: dict[str, Any],
    storage_path: Path,
    archive_state: str,
    archived_entries: list[dict[str, Any]],
    duplicate_entries: list[dict[str, Any]],
    skipped_entries: list[dict[str, Any]],
    existing_count: int,
    execution_state: str,
) -> dict[str, Any]:
    stored_total_count = existing_count + len(archived_entries)
    return {
        "workflow": "approval_archive",
        "namespace": config.namespace,
        "approval_mode": config.approval_mode,
        "external_dry_run": config.external_dry_run,
        "archive_state": archive_state,
        "summary": {
            "ledger_entry_count": len(ledger["ledger_entries"]),
            "archived_count": len(archived_entries),
            "duplicate_count": len(duplicate_entries),
            "skipped_second_review_count": sum(
                1 for item in skipped_entries if item["skip_reason"] == "requires_second_review"
            ),
            "stored_total_count": stored_total_count,
        },
        "archived_entries": archived_entries,
        "duplicate_entries": duplicate_entries,
        "skipped_entries": skipped_entries,
        "write_plan": {
            "target_collection": config.collection,
            "storage_path": str(storage_path),
            "archive_requested": execution_state != "blocked_archive_not_requested",
            "approved_ledger_write_review": execution_state
            not in {"blocked_archive_not_requested", "blocked_until_ledger_write_review"},
            "execution_state": execution_state,
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "collection": config.collection,
            "storage_path": str(storage_path),
            "decision_ids_to_remove": [str(item["decision_id"]) for item in archived_entries],
            "restore_snapshot_record_count": existing_count,
            "execution_state": "documentation_only",
        },
        "ledger_summary": ledger["summary"],
        "external_actions": [],
        "safety_boundary": {
            "local_write_scope": "data/venus/approval_decision_ledger.json",
            "notes": [
                "Only local Venus JSON storage can be changed by this workflow.",
                "High-risk decisions requiring second review are not archived.",
                "No source approval record, Feishu message, Douyin reply, publish action, ad spend, brand task, WeChat contact, memory state, backup state, or external platform state is changed.",
            ],
        },
    }


def _skipped_entry(entry: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "decision_id": str(entry["decision_id"]),
        "action_type": str(entry["action_type"]),
        "decision": str(entry["decision"]),
        "reviewer": str(entry["reviewer"]),
        "matched_approval_id": str(entry["matched_approval_id"]),
        "skip_reason": reason,
    }


def _existing_keys(records: list[dict[str, Any]]) -> set[str]:
    return {_entry_key(record) for record in records}


def _entry_key(entry: dict[str, Any]) -> str:
    return "|".join(
        [
            str(entry.get("decision_id") or ""),
            str(entry.get("action_type") or ""),
            str(entry.get("decision") or ""),
            str(entry.get("reviewer") or ""),
            str(entry.get("matched_approval_id") or ""),
        ]
    )


def _storage_path(config: ApprovalArchiveConfig) -> Path:
    return Path(config.workspace_root) / "data" / "venus" / f"{config.collection}.json"
