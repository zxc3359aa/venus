from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Confidence = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high", "critical"]
ApprovalLevel = Literal[0, 1, 2, 3, 4]


@dataclass(frozen=True)
class Evidence:
    source_id: str
    source_type: str
    title: str
    url: str
    retrieved_at: str
    confidence: Confidence
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskTag:
    label: str
    level: RiskLevel
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalRecord:
    action_type: str
    approval_level: ApprovalLevel
    draft: str
    evidence_ids: list[str]
    status: str
    reviewer: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
