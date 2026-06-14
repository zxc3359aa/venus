import pytest

from venus.connector_execution import (
    ConnectorExecutionConfig,
    build_connector_execution_plan,
)
from venus.storage import JsonStore


def _execution_payload(tmp_workspace, approved=True, live_requested=True):
    return {
        "source": "manual_connector_execution_review",
        "workspace_root": str(tmp_workspace),
        "executed_at": "2026-06-15T14:00:00+08:00",
        "execution_requested": True,
        "approved_execution_review": approved,
        "live_dispatch_requested": live_requested,
        "access_token": "secret-execution-token",
        "draft_records": [
            {
                "draft_id": "draft-feishu-report-001",
                "outbox_id": "outbox-feishu-report-001",
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "artifact_type": "feishu_card_draft",
                "target_surface": "feishu",
                "draft_payload": {"card": {"title": "Venus private report"}},
                "dispatch_state": "local_review_required",
                "approval_level": 2,
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-airtable-sync-001",
                "outbox_id": "outbox-airtable-sync-001",
                "action_id": "airtable-sync-001",
                "action_type": "airtable_sync_review",
                "artifact_type": "airtable_record_package",
                "target_surface": "airtable",
                "draft_payload": {"table": "Action Reviews"},
                "dispatch_state": "local_review_required",
                "approval_level": 2,
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-douyin-reply-001",
                "outbox_id": "outbox-douyin-reply-001",
                "action_id": "douyin-reply-001",
                "action_type": "douyin_reply_queue",
                "artifact_type": "douyin_reply_package",
                "target_surface": "douyin",
                "draft_payload": {"reply": "先看屏障状态。"},
                "dispatch_state": "local_review_required",
                "approval_level": 3,
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-qianchuan-budget-001",
                "outbox_id": "outbox-qianchuan-budget-001",
                "action_id": "qianchuan-budget-001",
                "action_type": "qianchuan_budget_review",
                "artifact_type": "qianchuan_budget_package",
                "target_surface": "qianchuan",
                "draft_payload": {"budget_delta": 500},
                "dispatch_state": "local_review_required",
                "approval_level": 4,
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-wechat-handoff-001",
                "outbox_id": "outbox-wechat-handoff-001",
                "action_id": "wechat-handoff-001",
                "action_type": "wechat_handoff_queue",
                "artifact_type": "wechat_handoff_package",
                "target_surface": "wechat",
                "draft_payload": {"handoff": "Invite to Enterprise WeChat."},
                "dispatch_state": "local_review_required",
                "approval_level": 2,
                "external_action_enabled": False,
            },
        ],
        "connector_reviews": [
            {
                "connector_id": "feishu-bot",
                "surface": "feishu",
                "connector_type": "feishu_bot",
                "ready_for_launch": True,
                "missing_permissions": [],
                "permissions_required": ["send_private_card"],
                "permissions_granted": ["send_private_card"],
                "secret_refs": ["VENUS_FEISHU_APP_ID"],
                "audit_ready": True,
                "rollback_ready": True,
                "approval_level": 2,
            },
            {
                "connector_id": "airtable-ops",
                "surface": "airtable",
                "connector_type": "airtable_api",
                "ready_for_launch": True,
                "missing_permissions": [],
                "permissions_required": ["record_write"],
                "permissions_granted": ["record_write"],
                "secret_refs": ["VENUS_AIRTABLE_BASE_ID"],
                "audit_ready": True,
                "rollback_ready": True,
                "approval_level": 2,
            },
            {
                "connector_id": "douyin-open",
                "surface": "douyin",
                "connector_type": "douyin_open_api",
                "ready_for_launch": True,
                "missing_permissions": ["video_comment_reply"],
                "permissions_required": ["video_comment_reply"],
                "permissions_granted": ["video_comment_read"],
                "secret_refs": ["VENUS_DOUYIN_CLIENT_ID"],
                "audit_ready": True,
                "rollback_ready": True,
                "approval_level": 3,
            },
            {
                "connector_id": "qianchuan-ads",
                "surface": "qianchuan",
                "connector_type": "oceanengine_marketing_api",
                "ready_for_launch": True,
                "missing_permissions": [],
                "permissions_required": ["budget_write"],
                "permissions_granted": ["budget_write"],
                "secret_refs": ["VENUS_QIANCHUAN_APP_ID"],
                "audit_ready": True,
                "rollback_ready": True,
                "approval_level": 4,
            },
            {
                "connector_id": "wechat-private-domain",
                "surface": "wechat",
                "connector_type": "wechat_mini_program",
                "ready_for_launch": True,
                "missing_permissions": [],
                "permissions_required": ["customer_message_send"],
                "permissions_granted": ["customer_message_send"],
                "secret_refs": ["VENUS_WECHAT_APP_ID"],
                "audit_ready": True,
                "rollback_ready": True,
                "approval_level": 2,
            },
        ],
        "execution_overrides": [
            {
                "draft_id": "draft-wechat-handoff-001",
                "external_action_enabled": True,
            }
        ],
    }


def test_build_connector_execution_plan_creates_local_manifests_and_blocks_risky_items(
    tmp_workspace,
):
    report = build_connector_execution_plan(_execution_payload(tmp_workspace))

    assert report["workflow"] == "connector_execution"
    assert report["namespace"] == "venus_connector_execution"
    assert report["approval_mode"] == "manual"
    assert report["external_dry_run"] is True
    assert report["external_actions"] == []
    assert report["execution_state"] == "local_manifests_written"
    assert report["summary"] == {
        "draft_count": 5,
        "execution_record_count": 2,
        "duplicate_count": 0,
        "blocked_count": 3,
        "approval_record_count": 2,
        "stored_total_count": 2,
    }

    records = {item["target_surface"]: item for item in report["execution_records"]}
    assert records["feishu"]["adapter_type"] == "feishu_card_send_candidate"
    assert records["feishu"]["required_secret_refs"] == ["VENUS_FEISHU_APP_ID"]
    assert records["airtable"]["adapter_type"] == "airtable_record_write_candidate"
    assert {item["external_action_enabled"] for item in report["execution_records"]} == {
        False
    }
    assert {item["dispatch_state"] for item in report["execution_records"]} == {
        "blocked_until_live_connector_enabled"
    }

    blocked = {item["draft_id"]: item["skip_reason"] for item in report["blocked_items"]}
    assert blocked == {
        "draft-douyin-reply-001": "missing_connector_permission",
        "draft-qianchuan-budget-001": "high_risk_live_action",
        "draft-wechat-handoff-001": "external_override_blocked",
    }
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_live_connector_dispatch_review",
        "venus_high_risk_connector_execution_review",
    }
    assert report["approval_records"][0]["approval_level"] == 4
    assert report["write_plan"]["external_action_enabled"] is False
    assert report["rollback_plan"]["execution_ids_to_remove"] == [
        item["execution_id"] for item in report["execution_records"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("connector_execution_manifests")
    assert stored == report["execution_records"]
    assert "secret-execution-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_connector_execution_plan_is_idempotent_for_existing_manifests(tmp_workspace):
    first = build_connector_execution_plan(_execution_payload(tmp_workspace))
    second = build_connector_execution_plan(_execution_payload(tmp_workspace))

    assert first["summary"]["execution_record_count"] == 2
    assert second["summary"]["execution_record_count"] == 0
    assert second["summary"]["duplicate_count"] == 2
    assert second["execution_state"] == "already_manifested"
    stored = JsonStore(tmp_workspace).read_collection("connector_execution_manifests")
    assert len(stored) == 2


def test_build_connector_execution_plan_blocks_without_execution_review(tmp_workspace):
    report = build_connector_execution_plan(_execution_payload(tmp_workspace, approved=False))

    assert report["execution_state"] == "blocked_until_execution_review"
    assert report["summary"]["execution_record_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_execution_review"
    assert not (
        tmp_workspace / "data" / "venus" / "connector_execution_manifests.json"
    ).exists()
    assert report["external_actions"] == []


def test_connector_execution_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ConnectorExecutionConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_connector_execution",
        )
