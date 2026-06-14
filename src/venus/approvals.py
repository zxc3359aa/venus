from __future__ import annotations

from venus.models import ApprovalRecord


def requires_manual_approval(approval_level: int) -> bool:
    return approval_level >= 2


def create_approval_record(
    action_type: str,
    approval_level: int,
    draft: str,
    evidence_ids: list[str],
    reviewer: str,
    created_at: str,
) -> dict:
    record = ApprovalRecord(
        action_type=action_type,
        approval_level=approval_level,  # type: ignore[arg-type]
        draft=draft,
        evidence_ids=evidence_ids,
        status="pending",
        reviewer=reviewer,
        created_at=created_at,
    )
    return record.to_dict()
