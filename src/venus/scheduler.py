from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval


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

READY_STATES = {"ready", "ok", "healthy"}


@dataclass(frozen=True)
class SchedulerConfig:
    namespace: str = "venus_scheduler"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus scheduler config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus scheduler namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus scheduler workflow must run in dry-run mode")


def build_scheduler_plan(
    payload: dict[str, Any],
    config: SchedulerConfig | None = None,
) -> dict[str, Any]:
    active_config = config or SchedulerConfig()
    safe_payload = _redact(payload)
    generated_at = str(safe_payload.get("generated_at") or "local-time")
    generated_dt = _parse_datetime(generated_at)
    jobs = [dict(item) for item in list(safe_payload.get("jobs") or [])]
    blackout_windows = [dict(item) for item in list(safe_payload.get("blackout_windows") or [])]
    operator_channels = [str(item) for item in list(safe_payload.get("operator_channels") or [])]

    run_queue: list[dict[str, Any]] = []
    blocked_jobs: list[dict[str, Any]] = []
    next_runs: list[dict[str, Any]] = []

    for job in jobs:
        normalized = _normalize_job(job, generated_dt)
        connector_state = normalized["connector_state"]
        if connector_state not in READY_STATES:
            blocked_jobs.append(_blocked_job(normalized, connector_state))
        elif normalized["is_due"]:
            run_queue.append(_run_queue_item(normalized))
        else:
            next_runs.append(_next_run_item(normalized))

    approval_gated_jobs = [
        item for item in run_queue if item["requires_manual_approval"]
    ]
    approval_records = _build_approval_records(
        live_scheduler_requested=bool(safe_payload.get("live_scheduler_requested")),
        approval_gated_jobs=approval_gated_jobs,
        reviewer=active_config.reviewer,
        created_at=generated_at,
    )
    operator_digest = _build_operator_digest(
        operator_channels=operator_channels,
        run_queue=run_queue,
        blocked_jobs=blocked_jobs,
        approval_gated_jobs=approval_gated_jobs,
    )

    return {
        "workflow": "scheduler",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_scheduler_plan"),
            "generated_at": generated_at,
            "timezone": str(safe_payload.get("timezone") or "Asia/Shanghai"),
            "freshness": "manual-import",
            "notes": "This dry-run scheduler creates a local run plan without starting timers, jobs, connectors, or external actions.",
        },
        "summary": {
            "job_count": len(jobs),
            "due_job_count": len(run_queue),
            "blocked_job_count": len(blocked_jobs),
            "paused_job_count": sum(1 for item in blocked_jobs if item["block_reason"] == "paused"),
            "next_run_count": len(next_runs),
            "approval_gated_job_count": len(approval_gated_jobs),
            "high_priority_due_count": sum(
                1 for item in run_queue if item["priority"] == "high"
            ),
            "backup_job_count": sum(
                1 for item in run_queue if "backup" in item["workflow"]
            ),
            "approval_record_count": len(approval_records),
        },
        "run_queue": run_queue,
        "blocked_jobs": blocked_jobs,
        "next_runs": next_runs,
        "blackout_windows": blackout_windows,
        "operator_digest": operator_digest,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No cron timer, Feishu message, platform read, platform write, reply, ad spend, memory write, or backup write is executed.",
                "Due jobs with approval level 2 or higher remain blocked until manual approval.",
                "Connector and permission blocked jobs are excluded from the run queue.",
            ],
        },
    }


def _normalize_job(job: dict[str, Any], generated_at: datetime | None) -> dict[str, Any]:
    last_run_at = str(job.get("last_run_at") or "")
    cadence_minutes = int(_number(job.get("cadence_minutes")))
    next_dt = _next_run_datetime(last_run_at, cadence_minutes)
    next_run_at = _format_datetime(next_dt)
    is_due = bool(generated_at and next_dt and next_dt <= generated_at)
    approval_level = int(_number(job.get("approval_level")))
    return {
        "job_id": str(job.get("job_id") or "local-job"),
        "workflow": str(job.get("workflow") or "unknown"),
        "cadence_minutes": cadence_minutes,
        "last_run_at": last_run_at,
        "next_run_at": next_run_at,
        "priority": str(job.get("priority") or "medium").lower(),
        "connector_state": str(job.get("connector_state") or "ready").lower(),
        "approval_level": approval_level,
        "requires_manual_approval": requires_manual_approval(approval_level),
        "is_due": is_due,
        "evidence_ids": [str(item) for item in list(job.get("evidence") or [])],
    }


def _run_queue_item(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "workflow": job["workflow"],
        "priority": job["priority"],
        "cadence_minutes": job["cadence_minutes"],
        "last_run_at": job["last_run_at"],
        "next_run_at": job["next_run_at"],
        "approval_level": job["approval_level"],
        "requires_manual_approval": job["requires_manual_approval"],
        "execution_state": (
            "blocked_until_approved"
            if job["requires_manual_approval"]
            else "ready_for_local_run"
        ),
        "evidence_ids": job["evidence_ids"],
        "external_action_enabled": False,
    }


def _blocked_job(job: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "workflow": job["workflow"],
        "priority": job["priority"],
        "next_run_at": job["next_run_at"],
        "block_reason": reason,
        "execution_state": "paused" if reason == "paused" else "blocked_by_connector",
        "evidence_ids": job["evidence_ids"],
        "external_action_enabled": False,
    }


def _next_run_item(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "workflow": job["workflow"],
        "priority": job["priority"],
        "next_run_at": job["next_run_at"],
        "execution_state": "waiting_for_cadence",
        "external_action_enabled": False,
    }


def _build_operator_digest(
    operator_channels: list[str],
    run_queue: list[dict[str, Any]],
    blocked_jobs: list[dict[str, Any]],
    approval_gated_jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    channel = operator_channels[0] if operator_channels else "local_review"
    return {
        "channel": channel,
        "summary": (
            f"{len(run_queue)} due jobs, {len(blocked_jobs)} blocked jobs, "
            f"{len(approval_gated_jobs)} approval-gated jobs."
        ),
        "due_workflows": [str(item["workflow"]) for item in run_queue],
        "blocked_workflows": [str(item["workflow"]) for item in blocked_jobs],
        "execution_state": "draft_only",
        "external_action_enabled": False,
    }


def _build_approval_records(
    live_scheduler_requested: bool,
    approval_gated_jobs: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    if live_scheduler_requested:
        records.append(
            create_approval_record(
                action_type="venus_scheduler_live_enablement",
                approval_level=2,
                draft="Review live 24-hour scheduler enablement, run locks, connector permissions, rate limits, and rollback controls.",
                evidence_ids=["venus-scheduler"],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    if approval_gated_jobs:
        evidence_ids = []
        for job in approval_gated_jobs:
            evidence_ids.extend(str(item) for item in list(job.get("evidence_ids") or []))
        records.append(
            create_approval_record(
                action_type="venus_scheduler_job_approval",
                approval_level=max(int(job["approval_level"]) for job in approval_gated_jobs),
                draft="Review approval-gated due scheduler jobs before any local or external execution.",
                evidence_ids=sorted(set(evidence_ids)),
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _next_run_datetime(last_run_at: str, cadence_minutes: int) -> datetime | None:
    last_dt = _parse_datetime(last_run_at)
    if not last_dt:
        return None
    return last_dt + timedelta(minutes=cadence_minutes)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_datetime(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _number(value: Any) -> float:
    try:
        return float(value or 0)
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
