import pytest

from venus.scheduler import SchedulerConfig, build_scheduler_plan


def _scheduler_payload():
    return {
        "source": "manual_scheduler_plan",
        "generated_at": "2026-06-14T18:30:00+08:00",
        "timezone": "Asia/Shanghai",
        "live_scheduler_requested": True,
        "access_token": "secret-scheduler-token",
        "jobs": [
            {
                "job_id": "job-trend",
                "workflow": "trend_scan",
                "cadence_minutes": 15,
                "last_run_at": "2026-06-14T18:00:00+08:00",
                "priority": "high",
                "connector_state": "ready",
                "approval_level": 1,
                "evidence": ["trend-schedule-001"],
            },
            {
                "job_id": "job-monitoring",
                "workflow": "monitoring",
                "cadence_minutes": 60,
                "last_run_at": "2026-06-14T17:00:00+08:00",
                "priority": "medium",
                "connector_state": "ready",
                "approval_level": 1,
                "evidence": ["monitoring-schedule-001"],
            },
            {
                "job_id": "job-douyin",
                "workflow": "douyin",
                "cadence_minutes": 10,
                "last_run_at": "2026-06-14T18:25:00+08:00",
                "priority": "high",
                "connector_state": "ready",
                "approval_level": 3,
                "evidence": ["douyin-schedule-001"],
            },
            {
                "job_id": "job-ecommerce",
                "workflow": "ecommerce",
                "cadence_minutes": 30,
                "last_run_at": "2026-06-14T17:40:00+08:00",
                "priority": "high",
                "connector_state": "missing_permission",
                "approval_level": 3,
                "evidence": ["shop-schedule-001"],
            },
            {
                "job_id": "job-backup",
                "workflow": "backup_verification",
                "cadence_minutes": 1440,
                "last_run_at": "2026-06-13T08:00:00+08:00",
                "priority": "high",
                "connector_state": "ready",
                "approval_level": 2,
                "evidence": ["backup-schedule-001"],
            },
            {
                "job_id": "job-memory",
                "workflow": "memory",
                "cadence_minutes": 1440,
                "last_run_at": "2026-06-14T08:00:00+08:00",
                "priority": "medium",
                "connector_state": "paused",
                "approval_level": 3,
                "evidence": ["memory-schedule-001"],
            },
        ],
        "blackout_windows": [
            {
                "name": "ad_spend_freeze",
                "surface": "qianchuan",
                "start": "2026-06-14T18:00:00+08:00",
                "end": "2026-06-14T20:00:00+08:00",
                "reason": "预算复盘前不自动调整投流",
            }
        ],
        "operator_channels": ["feishu_private"],
    }


def test_build_scheduler_plan_creates_due_queue_and_blocks_unsafe_jobs():
    plan = build_scheduler_plan(_scheduler_payload())

    assert plan["workflow"] == "scheduler"
    assert plan["namespace"] == "venus_scheduler"
    assert plan["dry_run"] is True
    assert plan["approval_mode"] == "manual"
    assert plan["external_actions"] == []
    assert plan["summary"] == {
        "job_count": 6,
        "due_job_count": 3,
        "blocked_job_count": 2,
        "paused_job_count": 1,
        "next_run_count": 1,
        "approval_gated_job_count": 1,
        "high_priority_due_count": 2,
        "backup_job_count": 1,
        "approval_record_count": 2,
    }

    assert [item["job_id"] for item in plan["run_queue"]] == [
        "job-trend",
        "job-monitoring",
        "job-backup",
    ]
    assert plan["run_queue"][0]["next_run_at"] == "2026-06-14T18:15:00+08:00"
    assert plan["run_queue"][0]["execution_state"] == "ready_for_local_run"
    assert plan["run_queue"][2]["execution_state"] == "blocked_until_approved"
    assert [item["job_id"] for item in plan["next_runs"]] == ["job-douyin"]
    assert {item["job_id"] for item in plan["blocked_jobs"]} == {"job-ecommerce", "job-memory"}
    assert plan["blocked_jobs"][0]["block_reason"] == "missing_permission"
    assert plan["operator_digest"]["channel"] == "feishu_private"
    assert "3 due jobs" in plan["operator_digest"]["summary"]
    assert plan["blackout_windows"][0]["name"] == "ad_spend_freeze"
    assert {record["action_type"] for record in plan["approval_records"]} == {
        "venus_scheduler_live_enablement",
        "venus_scheduler_job_approval",
    }
    assert "secret-scheduler-token" not in str(plan)
    assert "Xiaolongxia" not in str(plan)
    assert "小龙虾" not in str(plan)


def test_scheduler_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        SchedulerConfig(namespace="xiaolongxia_scheduler")
