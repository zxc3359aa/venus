import pytest

from venus.evals import EvalGateConfig, build_eval_report


def _eval_payload():
    return {
        "source": "manual_agent_run_eval",
        "evaluated_at": "2026-06-14T22:00:00+08:00",
        "api_key": "secret-evals-token",
        "live_autopilot_requested": True,
        "agent_run": {
            "run_id": "venus-run-eval-001",
            "executed_workflows": [
                "trend_scan",
                "hotspot",
                "product_intel",
                "comments",
                "production",
                "content_eval",
                "performance",
                "douyin",
                "ecommerce",
                "wechat",
                "commercial",
                "improvement",
                "memory",
                "scheduler",
                "connectors",
                "connector_execution",
                "connector_dispatch",
                "monitoring",
                "airtable",
            ],
            "workflow_summaries": {
                "content_eval": {
                    "publish_readiness_status": "blocked_by_claim_risk",
                    "blocking_issue_count": 1,
                    "approval_record_count": 2,
                },
                "performance": {
                    "winner_count": 2,
                    "underperformer_count": 1,
                    "calibration_rule_count": 3,
                    "approval_record_count": 2,
                },
                "connectors": {
                    "ready_connector_count": 2,
                    "blocked_connector_count": 3,
                    "high_risk_connector_count": 1,
                    "approval_record_count": 2,
                },
                "connector_execution": {
                    "execution_state": "local_manifests_written",
                    "execution_record_count": 1,
                    "blocked_count": 1,
                    "duplicate_count": 0,
                    "approval_record_count": 1,
                },
                "connector_dispatch": {
                    "dispatch_state": "local_rehearsals_written",
                    "rehearsal_record_count": 1,
                    "blocked_count": 1,
                    "duplicate_count": 0,
                    "approval_record_count": 1,
                },
                "scheduler": {
                    "due_job_count": 3,
                    "blocked_job_count": 2,
                    "approval_gated_job_count": 1,
                    "approval_record_count": 2,
                },
                "memory": {
                    "blocked_sensitive_candidate_count": 1,
                    "approval_gated_action_count": 2,
                },
                "improvement": {
                    "backup_issue_count": 1,
                    "approval_gated_action_count": 4,
                },
            },
            "action_plan": [
                {
                    "action_type": "draft_short_video",
                    "approval_level": 1,
                    "execution_state": "ready_for_internal_review",
                    "external_action_enabled": False,
                },
                {
                    "action_type": "feishu_mobile_report",
                    "approval_level": 2,
                    "execution_state": "blocked_until_approved",
                    "external_action_enabled": False,
                },
                {
                    "action_type": "qianchuan_budget_review",
                    "approval_level": 4,
                    "execution_state": "blocked_until_approved",
                    "external_action_enabled": False,
                },
            ],
            "approval_records": [
                {"action_type": "feishu_mobile_report", "status": "pending"},
                {"action_type": "qianchuan_budget_review", "status": "pending"},
            ],
            "external_actions": [],
        },
    }


def test_build_eval_report_blocks_autopilot_when_connectors_are_not_ready():
    report = build_eval_report(_eval_payload())

    assert report["workflow"] == "evals"
    assert report["namespace"] == "venus_evals"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "case_count": 8,
        "passed_count": 6,
        "failed_count": 2,
        "critical_failed_count": 2,
        "autopilot_ready": False,
        "readiness_status": "blocked_by_connector_readiness",
        "approval_record_count": 1,
    }

    assert report["failed_gates"][0]["gate_id"] == "connector_readiness"
    assert report["failed_gates"][1]["gate_id"] == "connector_dispatch_readiness"
    assert report["gate_results"][0]["gate_id"] == "required_workflows"
    assert report["gate_results"][0]["status"] == "pass"
    assert report["next_actions"][0]["action_type"] == "resolve_blocked_connectors"
    assert report["next_actions"][0]["execution_state"] == "blocked_until_approved"
    assert report["next_actions"][1]["action_type"] == "resolve_connector_dispatch_readiness"
    assert report["gate_definitions"]["external_action_lock"]["decision_use"] == "确认维纳斯没有执行任何平台动作。"
    assert report["approval_records"][0]["action_type"] == "venus_autopilot_enablement_review"
    assert report["approval_records"][0]["approval_level"] == 4
    assert "secret-evals-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_eval_report_passes_when_connector_dispatch_readiness_is_clear():
    payload = _eval_payload()
    payload["live_autopilot_requested"] = False
    summaries = payload["agent_run"]["workflow_summaries"]
    summaries["connectors"] = {
        "ready_connector_count": 5,
        "blocked_connector_count": 0,
        "high_risk_connector_count": 0,
        "approval_record_count": 0,
    }
    summaries["connector_execution"] = {
        "execution_state": "local_manifests_written",
        "execution_record_count": 2,
        "blocked_count": 0,
        "duplicate_count": 0,
        "approval_record_count": 0,
    }
    summaries["connector_dispatch"] = {
        "dispatch_state": "local_rehearsals_written",
        "rehearsal_record_count": 2,
        "blocked_count": 0,
        "duplicate_count": 0,
        "approval_record_count": 0,
    }

    report = build_eval_report(payload)

    assert report["summary"] == {
        "case_count": 8,
        "passed_count": 8,
        "failed_count": 0,
        "critical_failed_count": 0,
        "autopilot_ready": True,
        "readiness_status": "ready_for_manual_autopilot_review",
        "approval_record_count": 0,
    }
    assert report["failed_gates"] == []
    assert report["next_actions"] == []
    assert report["approval_records"] == []


def test_eval_gate_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        EvalGateConfig(namespace="xiaolongxia_evals")
