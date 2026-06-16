import pytest

from venus.connector_audit import ConnectorAuditConfig, build_connector_audit_report


def _connector_payload():
    return {
        "source": "manual_connector_review",
        "reviewed_at": "2026-06-14T19:00:00+08:00",
        "live_connector_requested": True,
        "access_token": "secret-connector-token",
        "connectors": [
            {
                "connector_id": "douyin-open",
                "surface": "douyin",
                "connector_type": "douyin_open_api",
                "desired_workflows": ["trend_scan", "douyin"],
                "status": "missing_permission",
                "permissions_required": ["video_comment_read", "live_message_read"],
                "permissions_granted": ["basic_profile"],
                "secret_refs": ["VENUS_DOUYIN_CLIENT_ID"],
                "audit_log": "missing",
                "rollback": "not_configured",
                "data_classes": ["public_comments", "creator_metrics"],
                "approval_level": 3,
                "evidence": ["douyin-app-001"],
            },
            {
                "connector_id": "feishu-bot",
                "surface": "feishu",
                "connector_type": "feishu_bot",
                "desired_workflows": ["feishu"],
                "status": "ready",
                "permissions_required": ["receive_message", "send_private_card"],
                "permissions_granted": ["receive_message", "send_private_card"],
                "secret_refs": ["VENUS_FEISHU_APP_ID"],
                "audit_log": "ready",
                "rollback": "configured",
                "data_classes": ["private_operator_reports"],
                "approval_level": 2,
                "evidence": ["feishu-app-001"],
            },
            {
                "connector_id": "qianchuan-ads",
                "surface": "qianchuan",
                "connector_type": "oceanengine_marketing_api",
                "desired_workflows": ["commercial"],
                "status": "missing_permission",
                "permissions_required": ["ad_account_read", "budget_write"],
                "permissions_granted": ["ad_account_read"],
                "secret_refs": ["VENUS_QIANCHUAN_APP_ID"],
                "audit_log": "ready",
                "rollback": "not_configured",
                "data_classes": ["ad_budget", "audience_segments"],
                "approval_level": 4,
                "evidence": ["qianchuan-app-001"],
            },
            {
                "connector_id": "airtable-ops",
                "surface": "airtable",
                "connector_type": "airtable_api",
                "desired_workflows": ["airtable"],
                "status": "ready",
                "permissions_required": ["base_read", "record_write"],
                "permissions_granted": ["base_read", "record_write"],
                "secret_refs": ["VENUS_AIRTABLE_BASE_ID"],
                "audit_log": "ready",
                "rollback": "configured",
                "data_classes": ["operations_records"],
                "approval_level": 2,
                "evidence": ["airtable-base-001"],
            },
            {
                "connector_id": "backup-store",
                "surface": "backup",
                "connector_type": "local_backup",
                "desired_workflows": ["improvement", "memory"],
                "status": "missing_verification",
                "permissions_required": ["local_write", "restore_read"],
                "permissions_granted": ["local_write", "restore_read"],
                "secret_refs": [],
                "audit_log": "ready",
                "rollback": "configured",
                "data_classes": ["local_memory_snapshots"],
                "approval_level": 2,
                "evidence": ["backup-store-001"],
            },
        ],
    }


def test_build_connector_audit_report_reviews_permissions_and_launch_sequence():
    report = build_connector_audit_report(_connector_payload())

    assert report["workflow"] == "connectors"
    assert report["namespace"] == "venus_connectors"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "connector_count": 5,
        "ready_connector_count": 2,
        "blocked_connector_count": 3,
        "missing_permission_count": 2,
        "missing_audit_log_count": 1,
        "missing_rollback_count": 2,
        "high_risk_connector_count": 1,
        "approval_gated_connector_count": 5,
        "approval_record_count": 2,
    }

    douyin = report["connector_reviews"][0]
    assert douyin["connector_id"] == "douyin-open"
    assert douyin["missing_permissions"] == ["video_comment_read", "live_message_read"]
    assert douyin["audit_ready"] is False
    assert douyin["rollback_ready"] is False
    assert douyin["execution_state"] == "blocked_by_readiness_gap"
    assert report["connector_reviews"][1]["execution_state"] == "blocked_until_approved"
    assert report["permission_matrix"]["qianchuan-ads"]["missing"] == ["budget_write"]
    assert report["readiness_gaps"][0]["severity"] == "high"
    assert {item["connector_id"] for item in report["launch_sequence"]} == {
        "feishu-bot",
        "airtable-ops",
    }
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_connector_live_enablement",
        "venus_high_risk_connector_review",
    }
    assert "secret-connector-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_connector_audit_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ConnectorAuditConfig(namespace="xiaolongxia_connectors")
