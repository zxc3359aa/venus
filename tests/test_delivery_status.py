import pytest

from venus.delivery_status import DeliveryStatusConfig, build_delivery_status
from venus.storage import JsonStore


def _status_payload(tmp_workspace, approved=True):
    return {
        "source": "manual_delivery_status",
        "workspace_root": str(tmp_workspace),
        "recorded_at": "2026-06-15T10:20:00+08:00",
        "status_update_requested": True,
        "approved_status_review": approved,
        "api_key": "secret-status-token",
        "draft_records": [
            {
                "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "outbox_id": "outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "artifact_type": "feishu_card_draft",
                "target_surface": "feishu",
                "dispatch_state": "local_review_required",
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-outbox-airtable_sync_review-airtable-sync-001-decision-002",
                "outbox_id": "outbox-airtable_sync_review-airtable-sync-001-decision-002",
                "action_id": "airtable-sync-001",
                "action_type": "airtable_sync_review",
                "artifact_type": "airtable_record_package",
                "target_surface": "airtable",
                "dispatch_state": "local_review_required",
                "external_action_enabled": False,
            },
        ],
        "status_events": [
            {
                "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "delivery_status": "manual_dispatch_completed",
                "reviewer": "owner",
                "event_time": "2026-06-15T10:00:00+08:00",
                "notes": "Copied the private Feishu card manually.",
                "evidence_ids": ["manual-feishu-001"],
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-outbox-airtable_sync_review-airtable-sync-001-decision-002",
                "delivery_status": "returned_for_revision",
                "reviewer": "owner",
                "event_time": "2026-06-15T10:05:00+08:00",
                "notes": "Airtable package needs cleaner field names.",
                "evidence_ids": ["manual-airtable-001"],
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-missing",
                "delivery_status": "manual_dispatch_completed",
                "reviewer": "owner",
                "event_time": "2026-06-15T10:07:00+08:00",
                "notes": "Missing draft should not be recorded.",
                "evidence_ids": [],
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "delivery_status": "platform_sent",
                "reviewer": "owner",
                "event_time": "2026-06-15T10:08:00+08:00",
                "notes": "Unsupported live platform status.",
                "evidence_ids": [],
                "external_action_enabled": False,
            },
            {
                "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "delivery_status": "blocked_after_review",
                "reviewer": "owner",
                "event_time": "2026-06-15T10:09:00+08:00",
                "notes": "Externally enabled event must be blocked.",
                "evidence_ids": [],
                "external_action_enabled": True,
            },
        ],
    }


def test_build_delivery_status_records_manual_statuses_and_blocks_unsafe_events(tmp_workspace):
    report = build_delivery_status(_status_payload(tmp_workspace))

    assert report["workflow"] == "delivery_status"
    assert report["namespace"] == "venus_delivery_status"
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["status_state"] == "recorded"
    assert report["summary"] == {
        "draft_count": 2,
        "status_event_count": 5,
        "recorded_count": 2,
        "duplicate_count": 0,
        "blocked_count": 3,
        "stored_total_count": 2,
    }

    statuses = {item["delivery_status"]: item for item in report["status_records"]}
    assert statuses["manual_dispatch_completed"]["follow_up_state"] == "closed_manual_delivery"
    assert statuses["returned_for_revision"]["follow_up_state"] == "needs_revision"
    assert {item["audit_state"] for item in report["status_records"]} == {
        "local_status_recorded"
    }
    assert {item["skip_reason"] for item in report["blocked_items"]} == {
        "missing_delivery_draft",
        "unsupported_delivery_status",
        "external_delivery_event",
    }
    assert report["rollback_plan"]["status_ids_to_remove"] == [
        item["status_id"] for item in report["status_records"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("delivery_status")
    assert stored == report["status_records"]
    assert "secret-status-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_delivery_status_is_idempotent_for_existing_status_records(tmp_workspace):
    first = build_delivery_status(_status_payload(tmp_workspace))
    second = build_delivery_status(_status_payload(tmp_workspace))

    assert first["summary"]["recorded_count"] == 2
    assert second["summary"]["recorded_count"] == 0
    assert second["summary"]["duplicate_count"] == 2
    assert second["status_state"] == "already_recorded"
    stored = JsonStore(tmp_workspace).read_collection("delivery_status")
    assert len(stored) == 2


def test_build_delivery_status_blocks_without_status_review(tmp_workspace):
    report = build_delivery_status(_status_payload(tmp_workspace, approved=False))

    assert report["status_state"] == "blocked_until_status_review"
    assert report["summary"]["recorded_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_status_review"
    assert not (tmp_workspace / "data" / "venus" / "delivery_status.json").exists()
    assert report["external_actions"] == []


def test_delivery_status_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        DeliveryStatusConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_delivery_status",
        )
