from __future__ import annotations


def requires_manual_approval(approval_level: int) -> bool:
    return int(approval_level) >= 2


def create_approval_record(
    action_type: str,
    approval_level: int,
    draft: str,
    evidence_ids: list[str],
    reviewer: str,
    created_at: str,
) -> dict:
    return {
        "action_type": str(action_type),
        "approval_level": int(approval_level),
        "draft": str(draft),
        "evidence_ids": list(evidence_ids),
        "status": "pending",
        "reviewer": str(reviewer),
        "created_at": str(created_at),
    }
