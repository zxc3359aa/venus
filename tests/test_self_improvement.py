import pytest

from venus.self_improvement import SelfImprovementConfig, build_self_improvement_report


def _improvement_payload():
    return {
        "source": "manual_learning_export",
        "retrieved_at": "2026-06-14T13:00:00+08:00",
        "api_key": "secret-learning-token",
        "feedback_events": [
            {
                "event_id": "fb-001",
                "workflow": "comments",
                "decision": "edited",
                "original": "这个产品一定能修复屏障",
                "final": "这个产品可以作为屏障护理参考，但要看肤质和耐受。",
                "reason": "去掉绝对功效承诺",
                "metric": {"comments": 42, "follows": 12},
            },
            {
                "event_id": "fb-002",
                "workflow": "content",
                "decision": "approved",
                "original": "早C晚A翻车自查",
                "final": "姐妹们，先看屏障状态，再谈早C晚A。",
                "reason": "开头更像我的口语",
                "metric": {"completion_rate": 0.74},
            },
        ],
        "defect_reports": [
            {
                "defect_id": "bug-001",
                "workflow": "douyin",
                "severity": "high",
                "description": "直播弹幕回复没有强调先停刺激组合",
                "expected_guardrail": "高风险直播弹幕必须提醒暂停叠加刺激组合",
            }
        ],
        "backup_checks": [
            {
                "target": "local-json-store",
                "schedule": "daily",
                "last_backup_at": "2026-06-14T08:00:00+08:00",
                "last_verified_at": "",
                "status": "missing_verification",
            }
        ],
    }


def test_build_self_improvement_report_creates_learning_regression_and_backup_tasks():
    report = build_self_improvement_report(_improvement_payload())

    assert report["workflow"] == "improvement"
    assert report["namespace"] == "venus_improvement"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "feedback_event_count": 2,
        "learning_candidate_count": 2,
        "defect_count": 1,
        "high_severity_defect_count": 1,
        "backup_check_count": 1,
        "backup_issue_count": 1,
        "approval_gated_action_count": 4,
    }

    first_candidate = report["learning_candidates"][0]
    assert first_candidate["source_event_id"] == "fb-001"
    assert first_candidate["workflow"] == "comments"
    assert "绝对功效" in first_candidate["proposed_rule"]
    assert first_candidate["execution_state"] == "blocked_until_approved"
    assert first_candidate["external_action_enabled"] is False

    assert report["learning_candidates"][1]["learning_type"] == "persona_style"
    assert report["regression_checks"][0]["check_id"] == "regression-bug-001"
    assert report["regression_checks"][0]["status"] == "pending"
    assert report["backup_tasks"][0]["action_type"] == "backup_verification"
    assert report["backup_tasks"][0]["status"] == "needs_verification"
    assert report["backup_tasks"][0]["execution_state"] == "blocked_until_approved"

    assert len(report["approval_records"]) == 4
    assert {record["status"] for record in report["approval_records"]} == {"pending"}
    assert {
        record["action_type"] for record in report["approval_records"]
    } == {
        "venus_learning_candidate",
        "venus_regression_guardrail",
        "venus_backup_verification",
    }
    assert "secret-learning-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_self_improvement_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        SelfImprovementConfig(namespace="xiaolongxia_improvement")
