from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approval_inbox import build_approval_inbox
from venus.approvals import create_approval_record


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
class ApprovalLedgerConfig:
    namespace: str = "venus_approval_ledger"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus approval ledger config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus approval ledger namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus approval ledger must run in dry-run mode")


def build_approval_ledger(
    payload: dict[str, Any],
    config: ApprovalLedgerConfig | None = None,
) -> dict[str, Any]:
    active_config = config or ApprovalLedgerConfig()
    safe_payload = _redact(payload)
    inbox = build_approval_inbox(safe_payload)
    existing_entries = [dict(item) for item in list(safe_payload.get("existing_ledger_entries") or [])]
    existing_keys = _existing_keys(existing_entries)

    ledger_entries: list[dict[str, Any]] = []
    duplicate_intents: list[dict[str, Any]] = []
    for intent in list(inbox["decision_intents"]):
        if intent["match_status"] != "matched":
            continue
        decision_id = _decision_id(intent)
        if decision_id in existing_keys or _intent_key(intent) in existing_keys:
            duplicate_intents.append(_duplicate_intent(intent, decision_id))
            continue
        ledger_entries.append(_ledger_entry(intent, decision_id, str(safe_payload.get("recorded_at") or "local-time")))

    approval_records = _approval_records(
        safe_payload=safe_payload,
        ledger_entries=ledger_entries,
        reviewer=active_config.reviewer,
    )

    return {
        "workflow": "approval_ledger",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_approval_ledger"),
            "recorded_at": str(safe_payload.get("recorded_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run ledger drafts auditable approval decisions without writing them.",
        },
        "summary": {
            "decision_intent_count": len(inbox["decision_intents"]),
            "new_entry_count": len(ledger_entries),
            "duplicate_intent_count": len(duplicate_intents),
            "second_review_count": sum(
                1 for item in ledger_entries if item["requires_second_review"]
            ),
            "ready_to_record_count": sum(
                1 for item in ledger_entries if item["record_state"] == "ready_for_local_ledger_review"
            ),
            "blocked_intent_count": sum(
                1 for item in ledger_entries if item["record_state"] == "blocked_for_second_review"
            ),
            "approval_record_count": len(approval_records),
        },
        "ledger_entries": ledger_entries,
        "duplicate_intents": duplicate_intents,
        "write_plan": {
            "target_collection": "approval_decision_ledger",
            "write_requested": bool(safe_payload.get("write_requested")),
            "record_count": len(ledger_entries),
            "existing_entry_count": len(existing_entries),
            "execution_state": "blocked_until_approved",
            "external_action_enabled": False,
        },
        "rollback_plan": {
            "strategy": "remove_proposed_decision_ids_if_a_future_local_write_is_reverted",
            "decision_ids_to_remove": [str(item["decision_id"]) for item in ledger_entries],
            "execution_state": "documentation_only",
        },
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "This workflow drafts local ledger entries but does not write storage.",
                "No approval status, Feishu message, Douyin reply, publish action, ad spend, brand task, WeChat contact, memory state, backup state, or platform state is changed.",
            ],
        },
    }


def _ledger_entry(intent: dict[str, Any], decision_id: str, recorded_at: str) -> dict[str, Any]:
    requires_second_review = bool(intent["requires_second_review"])
    return {
        "decision_id": decision_id,
        "action_type": str(intent["action_type"]),
        "decision": str(intent["decision"]),
        "reviewer": str(intent["reviewer"]),
        "reason": str(intent["reason"]),
        "surface": str(intent["surface"]),
        "approval_level": int(intent["approval_level"]),
        "matched_approval_id": str(intent["matched_approval_id"]),
        "requires_second_review": requires_second_review,
        "record_state": "blocked_for_second_review"
        if requires_second_review
        else "ready_for_local_ledger_review",
        "recorded_at": recorded_at,
        "external_action_enabled": False,
    }


def _duplicate_intent(intent: dict[str, Any], decision_id: str) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "action_type": str(intent["action_type"]),
        "decision": str(intent["decision"]),
        "reviewer": str(intent["reviewer"]),
        "matched_approval_id": str(intent["matched_approval_id"]),
        "duplicate_reason": "already_present_in_existing_ledger",
        "execution_state": "skipped_duplicate",
    }


def _approval_records(
    safe_payload: dict[str, Any],
    ledger_entries: list[dict[str, Any]],
    reviewer: str,
) -> list[dict[str, Any]]:
    records = []
    created_at = str(safe_payload.get("recorded_at") or "local-time")
    if bool(safe_payload.get("write_requested")) and ledger_entries:
        records.append(
            create_approval_record(
                action_type="venus_approval_ledger_write_review",
                approval_level=2,
                draft="Review local approval decision ledger write before any file or storage mutation.",
                evidence_ids=[str(item["decision_id"]) for item in ledger_entries],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    second_review_entries = [
        item for item in ledger_entries if item["record_state"] == "blocked_for_second_review"
    ]
    if second_review_entries:
        records.append(
            create_approval_record(
                action_type="venus_high_risk_decision_second_review",
                approval_level=4,
                draft="Second-review high-risk approval decisions before they can be written or executed.",
                evidence_ids=[str(item["decision_id"]) for item in second_review_entries],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _decision_id(intent: dict[str, Any]) -> str:
    return "-".join(
        [
            _slug(str(intent["action_type"])),
            _slug(str(intent["decision"])),
            _slug(str(intent["reviewer"])),
            _slug(str(intent["matched_approval_id"])),
        ]
    )


def _intent_key(intent: dict[str, Any]) -> str:
    return "|".join(
        [
            str(intent["action_type"]),
            str(intent["decision"]),
            str(intent["reviewer"]),
            str(intent["matched_approval_id"]),
        ]
    )


def _existing_keys(existing_entries: list[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for entry in existing_entries:
        keys.add(str(entry.get("decision_id") or ""))
        keys.add(
            "|".join(
                [
                    str(entry.get("action_type") or ""),
                    str(entry.get("decision") or ""),
                    str(entry.get("reviewer") or ""),
                    str(entry.get("matched_approval_id") or ""),
                ]
            )
        )
    return keys


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
