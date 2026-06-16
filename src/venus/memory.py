from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record
from venus.backups import backup_status_record


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

MEMORY_SECTIONS = [
    "principles",
    "style_phrases",
    "product_beliefs",
    "content_rules",
    "banned_claims",
    "privacy_boundaries",
]

SENSITIVE_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"\d{15}|\d{17}[\dXx]"),
]


@dataclass(frozen=True)
class MemoryConfig:
    namespace: str = "venus_memory"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus memory config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus memory namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus memory workflow must run in dry-run mode")


def build_memory_report(
    payload: dict[str, Any],
    config: MemoryConfig | None = None,
) -> dict[str, Any]:
    active_config = config or MemoryConfig()
    safe_payload = _redact(payload)
    current_memory = _normalize_current_memory(safe_payload.get("current_memory"))
    learning_candidates = [dict(item) for item in list(safe_payload.get("learning_candidates") or [])]
    decisions = _decision_map(safe_payload.get("approval_decisions"))
    backup = dict(safe_payload.get("backup") or {})

    proposed_version = _next_version(str(current_memory["version"]))
    candidate_reviews = _build_candidate_reviews(learning_candidates, decisions)
    memory_diff = _build_memory_diff(current_memory, candidate_reviews)
    proposed_memory = _build_proposed_memory(current_memory, proposed_version, memory_diff)
    rollback_plan = _build_rollback_plan(
        previous_version=str(current_memory["version"]),
        proposed_version=proposed_version,
        backup_target=str(backup.get("target") or "local-memory-ledger"),
    )
    backup_tasks = _build_backup_tasks(backup)
    approval_records = _build_approval_records(
        memory_diff=memory_diff,
        backup_tasks=backup_tasks,
        candidate_reviews=candidate_reviews,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    approved_count = sum(1 for item in candidate_reviews if item["decision"] == "approved")
    rejected_count = sum(1 for item in candidate_reviews if item["decision"] == "rejected")
    pending_count = sum(1 for item in candidate_reviews if item["decision"] == "pending")
    blocked_sensitive_count = sum(1 for item in candidate_reviews if item["privacy_flag"])
    proposed_change_count = sum(
        len(values) for values in memory_diff["additions"].values()
    )

    return {
        "workflow": "memory",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_memory_review"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run report stages approved memory changes without writing long-term memory or external systems.",
        },
        "summary": {
            "current_version": str(current_memory["version"]),
            "candidate_count": len(candidate_reviews),
            "approved_candidate_count": approved_count,
            "rejected_candidate_count": rejected_count,
            "pending_candidate_count": pending_count,
            "blocked_sensitive_candidate_count": blocked_sensitive_count,
            "proposed_version": proposed_version,
            "proposed_change_count": proposed_change_count,
            "backup_issue_count": len(backup_tasks),
            "approval_gated_action_count": len(approval_records),
        },
        "candidate_reviews": candidate_reviews,
        "memory_diff": memory_diff,
        "proposed_memory": proposed_memory,
        "rollback_plan": rollback_plan,
        "backup_tasks": backup_tasks,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No long-term memory, system prompt, persona file, backup target, or external platform state is changed.",
                "Approved learning is staged for manual review only.",
                "Sensitive personal data is blocked from the proposed memory merge.",
            ],
        },
    }


def _normalize_current_memory(value: Any) -> dict[str, Any]:
    raw = dict(value or {})
    normalized: dict[str, Any] = {"version": str(raw.get("version") or "v0")}
    for section in MEMORY_SECTIONS:
        normalized[section] = _string_list(raw.get(section))
    return normalized


def _decision_map(value: Any) -> dict[str, str]:
    decisions = {}
    for item in list(value or []):
        candidate_id = str(dict(item).get("candidate_id") or "")
        decision = str(dict(item).get("decision") or "pending").lower()
        decisions[candidate_id] = decision if decision in {"approved", "rejected"} else "pending"
    return decisions


def _build_candidate_reviews(
    candidates: list[dict[str, Any]],
    decisions: dict[str, str],
) -> list[dict[str, Any]]:
    reviews = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = str(candidate.get("candidate_id") or f"memory-{index:03d}")
        category = _memory_section(str(candidate.get("category") or "content_rules"))
        raw_rule = str(candidate.get("proposed_rule") or "")
        privacy_flag = bool(candidate.get("contains_personal_data")) or _contains_sensitive(raw_rule)
        decision = decisions.get(candidate_id, "pending")
        execution_state = _execution_state(decision, privacy_flag)
        reviews.append(
            {
                "candidate_id": candidate_id,
                "category": category,
                "source": str(candidate.get("source") or "manual_review"),
                "proposed_rule": "[REDACTED_SENSITIVE_MEMORY]" if privacy_flag else raw_rule,
                "decision": decision,
                "risk_level": "high" if privacy_flag else ("low" if decision == "approved" else "medium"),
                "privacy_flag": privacy_flag,
                "execution_state": execution_state,
                "approval_level": 3,
                "requires_manual_approval": True,
                "evidence_ids": [str(item) for item in list(candidate.get("evidence") or [])],
                "external_action_enabled": False,
            }
        )
    return reviews


def _build_memory_diff(
    current_memory: dict[str, Any],
    candidate_reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    additions = {section: [] for section in MEMORY_SECTIONS}
    excluded_candidate_ids = []
    for review in candidate_reviews:
        if (
            review["decision"] == "approved"
            and not review["privacy_flag"]
            and review["proposed_rule"]
        ):
            section = str(review["category"])
            rule = str(review["proposed_rule"])
            if rule not in list(current_memory.get(section) or []):
                additions[section].append(rule)
        else:
            excluded_candidate_ids.append(str(review["candidate_id"]))
    return {
        "additions": additions,
        "excluded_candidate_ids": excluded_candidate_ids,
    }


def _build_proposed_memory(
    current_memory: dict[str, Any],
    proposed_version: str,
    memory_diff: dict[str, Any],
) -> dict[str, Any]:
    proposed: dict[str, Any] = {
        "version": proposed_version,
        "previous_version": str(current_memory["version"]),
    }
    additions = dict(memory_diff.get("additions") or {})
    for section in MEMORY_SECTIONS:
        merged = list(current_memory.get(section) or [])
        for item in list(additions.get(section) or []):
            if item not in merged:
                merged.append(str(item))
        proposed[section] = merged
    return proposed


def _build_rollback_plan(
    previous_version: str,
    proposed_version: str,
    backup_target: str,
) -> dict[str, Any]:
    return {
        "from_version": proposed_version,
        "to_version": previous_version,
        "required_snapshot": f"{backup_target}@{previous_version}",
        "approval_level": 3,
        "requires_manual_approval": True,
        "execution_state": "blocked_until_approved",
        "external_action_enabled": False,
    }


def _build_backup_tasks(backup: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(backup.get("status") or "").lower()
    last_verified_at = str(backup.get("last_verified_at") or "")
    if status in {"ok", "verified"} and last_verified_at:
        return []

    target = str(backup.get("target") or "local-memory-ledger")
    record = backup_status_record(
        target=target,
        schedule=str(backup.get("schedule") or "before-memory-merge"),
        last_backup_at=str(backup.get("last_backup_at") or ""),
        last_verified_at=last_verified_at,
        status=status or "missing_verification",
    )
    return [
        {
            "action_type": "memory_backup_verification",
            "task_id": f"memory-backup-{target}",
            "target": target,
            "last_snapshot_version": str(backup.get("last_snapshot_version") or ""),
            "status": "needs_verification",
            "backup_status": record,
            "approval_level": 2,
            "requires_manual_approval": True,
            "execution_state": "blocked_until_approved",
            "external_action_enabled": False,
        }
    ]


def _build_approval_records(
    memory_diff: dict[str, Any],
    backup_tasks: list[dict[str, Any]],
    candidate_reviews: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    changed_sections = [
        section
        for section, values in dict(memory_diff.get("additions") or {}).items()
        if list(values)
    ]
    if changed_sections:
        evidence_ids = []
        for review in candidate_reviews:
            if review["decision"] == "approved" and not review["privacy_flag"]:
                evidence_ids.extend(str(item) for item in list(review.get("evidence_ids") or []))
        records.append(
            create_approval_record(
                action_type="venus_memory_merge",
                approval_level=3,
                draft=f"Review staged Venus memory merge for sections: {', '.join(changed_sections)}.",
                evidence_ids=sorted(set(evidence_ids)),
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    for task in backup_tasks:
        records.append(
            create_approval_record(
                action_type="venus_memory_backup_verification",
                approval_level=int(task["approval_level"]),
                draft=f"Verify memory backup target {task['target']} before any memory merge or rollback.",
                evidence_ids=[str(task["task_id"])],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _execution_state(decision: str, privacy_flag: bool) -> str:
    if privacy_flag:
        return "blocked_sensitive_data"
    if decision == "approved":
        return "staged_for_manual_merge"
    if decision == "rejected":
        return "rejected"
    return "blocked_until_approved"


def _memory_section(value: str) -> str:
    return value if value in MEMORY_SECTIONS else "content_rules"


def _contains_sensitive(value: str) -> bool:
    return any(pattern.search(value) for pattern in SENSITIVE_PATTERNS)


def _next_version(value: str) -> str:
    match = re.search(r"(\d+)$", value)
    if not match:
        return f"{value}-next"
    number = int(match.group(1)) + 1
    return f"{value[:match.start(1)]}{number}"


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in list(value or [])]


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
