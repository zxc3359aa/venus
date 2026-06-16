from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval
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


@dataclass(frozen=True)
class SelfImprovementConfig:
    namespace: str = "venus_improvement"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus self-improvement config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus self-improvement namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus self-improvement must run in dry-run mode")


def build_self_improvement_report(
    payload: dict[str, Any],
    config: SelfImprovementConfig | None = None,
) -> dict[str, Any]:
    active_config = config or SelfImprovementConfig()
    safe_payload = _redact(payload)
    feedback_events = list(safe_payload.get("feedback_events") or [])
    defect_reports = list(safe_payload.get("defect_reports") or [])
    backup_checks = list(safe_payload.get("backup_checks") or [])

    learning_candidates = _build_learning_candidates(feedback_events)
    regression_checks = _build_regression_checks(defect_reports)
    backup_tasks = _build_backup_tasks(backup_checks)
    approval_records = _build_approval_records(
        learning_candidates=learning_candidates,
        regression_checks=regression_checks,
        backup_tasks=backup_tasks,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "improvement",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_learning_export"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run report proposes learning, guardrail, and backup tasks without changing memory or external systems.",
        },
        "summary": {
            "feedback_event_count": len(feedback_events),
            "learning_candidate_count": len(learning_candidates),
            "defect_count": len(defect_reports),
            "high_severity_defect_count": sum(
                1 for defect in defect_reports if str(defect.get("severity", "")).lower() == "high"
            ),
            "backup_check_count": len(backup_checks),
            "backup_issue_count": len(backup_tasks),
            "approval_gated_action_count": len(approval_records),
        },
        "learning_candidates": learning_candidates,
        "regression_checks": regression_checks,
        "backup_tasks": backup_tasks,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No persona memory, system prompt, code, backup target, or platform configuration is changed automatically.",
                "Learning candidates and high-risk guardrail updates require manual approval before becoming operating rules.",
                "Backup verification only creates a local review task in this slice.",
            ],
        },
    }


def _build_learning_candidates(feedback_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for index, event in enumerate(feedback_events, start=1):
        event_id = str(event.get("event_id") or f"feedback-{index:03d}")
        rule = _learning_rule(event)
        evidence_ids = [event_id]
        candidates.append(
            {
                "candidate_id": f"learning-{event_id}",
                "source_event_id": event_id,
                "workflow": str(event.get("workflow") or "unknown"),
                "decision": str(event.get("decision") or "unknown"),
                "learning_type": _learning_type(event),
                "proposed_rule": rule,
                "approval_level": 2,
                "requires_manual_approval": True,
                "execution_state": "blocked_until_approved",
                "evidence_ids": evidence_ids,
                "external_action_enabled": False,
            }
        )
    return candidates


def _build_regression_checks(defect_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = []
    for index, defect in enumerate(defect_reports, start=1):
        defect_id = str(defect.get("defect_id") or f"defect-{index:03d}")
        severity = str(defect.get("severity") or "medium").lower()
        approval_level = 3 if severity == "high" else 2
        checks.append(
            {
                "check_id": f"regression-{defect_id}",
                "source_defect_id": defect_id,
                "workflow": str(defect.get("workflow") or "unknown"),
                "severity": severity,
                "description": str(defect.get("description") or ""),
                "expected_guardrail": str(
                    defect.get("expected_guardrail")
                    or "生成前必须检查功效、风险、人群和审批边界。"
                ),
                "status": "pending",
                "approval_level": approval_level,
                "requires_manual_approval": requires_manual_approval(approval_level),
                "execution_state": "blocked_until_approved",
                "external_action_enabled": False,
            }
        )
    return checks


def _build_backup_tasks(backup_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = []
    for index, check in enumerate(backup_checks, start=1):
        status = str(check.get("status") or "").lower()
        last_verified_at = str(check.get("last_verified_at") or "")
        if status in {"ok", "verified"} and last_verified_at:
            continue

        target = str(check.get("target") or f"backup-target-{index:03d}")
        record = backup_status_record(
            target=target,
            schedule=str(check.get("schedule") or "manual"),
            last_backup_at=str(check.get("last_backup_at") or ""),
            last_verified_at=last_verified_at,
            status=status or "missing_verification",
        )
        tasks.append(
            {
                "action_type": "backup_verification",
                "task_id": f"backup-{target}",
                "target": target,
                "status": "needs_verification",
                "backup_status": record,
                "approval_level": 2,
                "requires_manual_approval": True,
                "execution_state": "blocked_until_approved",
                "external_action_enabled": False,
            }
        )
    return tasks


def _build_approval_records(
    learning_candidates: list[dict[str, Any]],
    regression_checks: list[dict[str, Any]],
    backup_tasks: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    for candidate in learning_candidates:
        records.append(
            create_approval_record(
                action_type="venus_learning_candidate",
                approval_level=int(candidate["approval_level"]),
                draft=str(candidate["proposed_rule"]),
                evidence_ids=list(candidate["evidence_ids"]),
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    for check in regression_checks:
        if not check["requires_manual_approval"]:
            continue
        records.append(
            create_approval_record(
                action_type="venus_regression_guardrail",
                approval_level=int(check["approval_level"]),
                draft=str(check["expected_guardrail"]),
                evidence_ids=[str(check["source_defect_id"])],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    for task in backup_tasks:
        records.append(
            create_approval_record(
                action_type="venus_backup_verification",
                approval_level=int(task["approval_level"]),
                draft=f"Verify latest backup for {task['target']} before any restore or schema change.",
                evidence_ids=[str(task["task_id"])],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _learning_type(event: dict[str, Any]) -> str:
    text = " ".join(
        str(event.get(key) or "")
        for key in ("reason", "original", "final", "workflow", "decision")
    )
    if "口语" in text or "姐妹们" in text or "风格" in text:
        return "persona_style"
    if "绝对" in text or "100%" in text or "一定" in text or "承诺" in text:
        return "safety_claim_boundary"
    return "operating_preference"


def _learning_rule(event: dict[str, Any]) -> str:
    text = " ".join(
        str(event.get(key) or "")
        for key in ("reason", "original", "final")
    )
    metric = dict(event.get("metric") or {})
    completion_rate = _number(metric.get("completion_rate"))
    if "绝对" in text or "100%" in text or "一定" in text or "修复屏障" in text:
        return "不要把护肤功效写成绝对功效承诺；改成证据、肤质、耐受和使用边界。"
    if "口语" in text or "姐妹们" in text or completion_rate >= 0.7:
        return "优先保留“姐妹们/先看屏障状态/证据和耐受”这类口语节奏，再给专业判断。"
    return "保留用户最终采用的表达方向，但进入长期记忆前必须人工确认适用场景。"


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


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
