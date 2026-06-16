import pytest

from venus.connector_dispatch import (
    ConnectorDispatchConfig,
    build_connector_dispatch_rehearsal,
)
from venus.storage import JsonStore


def _dispatch_payload(tmp_workspace, approved=True, live_requested=True):
    return {
        "source": "manual_connector_dispatch_review",
        "workspace_root": str(tmp_workspace),
        "rehearsed_at": "2026-06-15T15:00:00+08:00",
        "dispatch_requested": True,
        "approved_dispatch_review": approved,
        "live_dispatch_requested": live_requested,
        "access_token": "secret-dispatch-token",
        "environment": {
            "VENUS_FEISHU_APP_ID_configured": True,
            "VENUS_AIRTABLE_BASE_ID_configured": True,
            "VENUS_DOUYIN_CLIENT_ID_configured": False,
            "VENUS_QIANCHUAN_APP_ID_configured": True,
            "VENUS_WECHAT_APP_ID_configured": True,
        },
        "execution_records": [
            {
                "execution_id": "exec-draft-feishu-report-001-feishu-bot",
                "draft_id": "draft-feishu-report-001",
                "outbox_id": "outbox-feishu-report-001",
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "artifact_type": "feishu_card_draft",
                "target_surface": "feishu",
                "connector_id": "feishu-bot",
                "connector_type": "feishu_bot",
                "adapter_type": "feishu_card_send_candidate",
                "required_secret_refs": ["VENUS_FEISHU_APP_ID"],
                "manifest_payload": {"card": {"title": "Venus private report"}},
                "execution_state": "local_manifest_ready",
                "dispatch_state": "blocked_until_live_connector_enabled",
                "approval_level": 2,
                "external_action_enabled": False,
            },
            {
                "execution_id": "exec-draft-airtable-sync-001-airtable-ops",
                "draft_id": "draft-airtable-sync-001",
                "outbox_id": "outbox-airtable-sync-001",
                "action_id": "airtable-sync-001",
                "action_type": "airtable_sync_review",
                "artifact_type": "airtable_record_package",
                "target_surface": "airtable",
                "connector_id": "airtable-ops",
                "connector_type": "airtable_api",
                "adapter_type": "airtable_record_write_candidate",
                "required_secret_refs": ["VENUS_AIRTABLE_BASE_ID"],
                "manifest_payload": {"table": "Action Reviews"},
                "execution_state": "local_manifest_ready",
                "dispatch_state": "blocked_until_live_connector_enabled",
                "approval_level": 2,
                "external_action_enabled": False,
            },
            {
                "execution_id": "exec-draft-douyin-reply-001-douyin-open",
                "draft_id": "draft-douyin-reply-001",
                "outbox_id": "outbox-douyin-reply-001",
                "action_id": "douyin-reply-001",
                "action_type": "douyin_reply_queue",
                "artifact_type": "douyin_reply_package",
                "target_surface": "douyin",
                "connector_id": "douyin-open",
                "connector_type": "douyin_open_api",
                "adapter_type": "douyin_reply_or_metric_candidate",
                "required_secret_refs": ["VENUS_DOUYIN_CLIENT_ID"],
                "manifest_payload": {"reply": "先看屏障状态。"},
                "execution_state": "local_manifest_ready",
                "dispatch_state": "blocked_until_live_connector_enabled",
                "approval_level": 3,
                "external_action_enabled": False,
            },
            {
                "execution_id": "exec-draft-qianchuan-budget-001-qianchuan-ads",
                "draft_id": "draft-qianchuan-budget-001",
                "outbox_id": "outbox-qianchuan-budget-001",
                "action_id": "qianchuan-budget-001",
                "action_type": "qianchuan_budget_review",
                "artifact_type": "qianchuan_budget_package",
                "target_surface": "qianchuan",
                "connector_id": "qianchuan-ads",
                "connector_type": "oceanengine_marketing_api",
                "adapter_type": "oceanengine_budget_candidate",
                "required_secret_refs": ["VENUS_QIANCHUAN_APP_ID"],
                "manifest_payload": {"budget_delta": 500},
                "execution_state": "local_manifest_ready",
                "dispatch_state": "blocked_until_live_connector_enabled",
                "approval_level": 4,
                "external_action_enabled": False,
            },
            {
                "execution_id": "exec-draft-wechat-handoff-001-wechat-private-domain",
                "draft_id": "draft-wechat-handoff-001",
                "outbox_id": "outbox-wechat-handoff-001",
                "action_id": "wechat-handoff-001",
                "action_type": "wechat_handoff_queue",
                "artifact_type": "wechat_handoff_package",
                "target_surface": "wechat",
                "connector_id": "wechat-private-domain",
                "connector_type": "wechat_mini_program",
                "adapter_type": "wechat_private_domain_candidate",
                "required_secret_refs": ["VENUS_WECHAT_APP_ID"],
                "manifest_payload": {"handoff": "Invite to Enterprise WeChat."},
                "execution_state": "local_manifest_ready",
                "dispatch_state": "blocked_until_live_connector_enabled",
                "approval_level": 2,
                "external_action_enabled": False,
            },
        ],
        "dispatch_overrides": [
            {
                "execution_id": "exec-draft-wechat-handoff-001-wechat-private-domain",
                "external_action_enabled": True,
            }
        ],
    }


def test_build_connector_dispatch_rehearsal_creates_request_drafts_and_blocks_risks(
    tmp_workspace,
):
    report = build_connector_dispatch_rehearsal(_dispatch_payload(tmp_workspace))

    assert report["workflow"] == "connector_dispatch"
    assert report["namespace"] == "venus_connector_dispatch"
    assert report["approval_mode"] == "manual"
    assert report["external_dry_run"] is True
    assert report["external_actions"] == []
    assert report["dispatch_state"] == "local_rehearsals_written"
    assert report["summary"] == {
        "execution_count": 5,
        "rehearsal_record_count": 2,
        "duplicate_count": 0,
        "blocked_count": 3,
        "approval_record_count": 2,
        "stored_total_count": 2,
    }

    records = {item["target_surface"]: item for item in report["rehearsal_records"]}
    assert records["feishu"]["request_envelope"]["endpoint_label"] == "feishu.private_card"
    assert records["feishu"]["request_envelope"]["method"] == "POST"
    assert records["feishu"]["credential_refs"] == ["VENUS_FEISHU_APP_ID"]
    assert records["airtable"]["request_envelope"]["endpoint_label"] == "airtable.records"
    assert {item["external_action_enabled"] for item in report["rehearsal_records"]} == {
        False
    }
    assert {item["dispatch_state"] for item in report["rehearsal_records"]} == {
        "blocked_until_live_dispatch_enabled"
    }

    blocked = {item["execution_id"]: item["skip_reason"] for item in report["blocked_items"]}
    assert blocked == {
        "exec-draft-douyin-reply-001-douyin-open": "missing_credential_ref",
        "exec-draft-qianchuan-budget-001-qianchuan-ads": "high_risk_dispatch",
        "exec-draft-wechat-handoff-001-wechat-private-domain": "external_override_blocked",
    }
    assert report["credential_readiness"]["VENUS_DOUYIN_CLIENT_ID"]["configured"] is False
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_live_connector_dispatch_rehearsal_review",
        "venus_high_risk_dispatch_rehearsal_review",
    }
    assert report["approval_records"][0]["approval_level"] == 4
    assert report["write_plan"]["external_action_enabled"] is False
    assert report["rollback_plan"]["rehearsal_ids_to_remove"] == [
        item["rehearsal_id"] for item in report["rehearsal_records"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("connector_dispatch_rehearsals")
    assert stored == report["rehearsal_records"]
    assert "secret-dispatch-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_connector_dispatch_rehearsal_is_idempotent_for_existing_records(tmp_workspace):
    first = build_connector_dispatch_rehearsal(_dispatch_payload(tmp_workspace))
    second = build_connector_dispatch_rehearsal(_dispatch_payload(tmp_workspace))

    assert first["summary"]["rehearsal_record_count"] == 2
    assert second["summary"]["rehearsal_record_count"] == 0
    assert second["summary"]["duplicate_count"] == 2
    assert second["dispatch_state"] == "already_rehearsed"
    stored = JsonStore(tmp_workspace).read_collection("connector_dispatch_rehearsals")
    assert len(stored) == 2


def test_build_connector_dispatch_rehearsal_blocks_without_dispatch_review(tmp_workspace):
    report = build_connector_dispatch_rehearsal(_dispatch_payload(tmp_workspace, approved=False))

    assert report["dispatch_state"] == "blocked_until_dispatch_review"
    assert report["summary"]["rehearsal_record_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_dispatch_review"
    assert not (
        tmp_workspace / "data" / "venus" / "connector_dispatch_rehearsals.json"
    ).exists()
    assert report["external_actions"] == []


def test_connector_dispatch_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ConnectorDispatchConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_connector_dispatch",
        )
