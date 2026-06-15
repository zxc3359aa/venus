import pytest

from venus.delivery_drafts import DeliveryDraftConfig, build_delivery_drafts
from venus.storage import JsonStore


def _delivery_payload(tmp_workspace, approved=True):
    return {
        "source": "manual_delivery_drafts",
        "workspace_root": str(tmp_workspace),
        "drafted_at": "2026-06-15T09:10:00+08:00",
        "delivery_requested": True,
        "approved_delivery_review": approved,
        "access_token": "secret-delivery-token",
        "outbox_items": [
            {
                "outbox_id": "outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "surface": "feishu",
                "approval_level": 2,
                "decision_id": "decision-001",
                "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                "reviewer": "owner",
                "draft": "Prepare a private Feishu card summary.",
                "queued_at": "2026-06-14T23:40:00+08:00",
                "execution_state": "queued_local_outbox",
                "delivery_state": "local_manual_dispatch_required",
                "external_action_enabled": False,
            },
            {
                "outbox_id": "outbox-airtable_sync_review-airtable-sync-001-decision-002",
                "action_id": "airtable-sync-001",
                "action_type": "airtable_sync_review",
                "surface": "airtable",
                "approval_level": 2,
                "decision_id": "decision-002",
                "matched_approval_id": "airtable_sync_review-20260614-2020000800",
                "reviewer": "owner",
                "draft": "Review Airtable sync package.",
                "queued_at": "2026-06-14T23:41:00+08:00",
                "execution_state": "queued_local_outbox",
                "delivery_state": "local_manual_dispatch_required",
                "external_action_enabled": False,
            },
            {
                "outbox_id": "outbox-qianchuan_budget_review-qianchuan-budget-001-decision-003",
                "action_id": "qianchuan-budget-001",
                "action_type": "qianchuan_budget_review",
                "surface": "qianchuan",
                "approval_level": 4,
                "decision_id": "decision-003",
                "matched_approval_id": "qianchuan_budget_review-20260614-2130000800",
                "reviewer": "owner",
                "draft": "Review budget before spend changes.",
                "queued_at": "2026-06-14T23:42:00+08:00",
                "execution_state": "queued_local_outbox",
                "delivery_state": "local_manual_dispatch_required",
                "external_action_enabled": False,
            },
        ],
    }


def test_build_delivery_drafts_creates_feishu_and_airtable_local_drafts(tmp_workspace):
    report = build_delivery_drafts(_delivery_payload(tmp_workspace))

    assert report["workflow"] == "delivery_drafts"
    assert report["namespace"] == "venus_delivery_drafts"
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["delivery_state"] == "drafted"
    assert report["summary"] == {
        "outbox_item_count": 3,
        "drafted_count": 2,
        "duplicate_count": 0,
        "blocked_count": 1,
        "stored_total_count": 2,
    }

    drafts = {item["action_type"]: item for item in report["draft_records"]}
    assert drafts["feishu_mobile_report"]["artifact_type"] == "feishu_card_draft"
    assert drafts["feishu_mobile_report"]["draft_payload"]["card"]["title"] == "Venus private report"
    assert drafts["airtable_sync_review"]["artifact_type"] == "airtable_record_package"
    assert drafts["airtable_sync_review"]["draft_payload"]["table"] == "Action Reviews"
    assert {item["dispatch_state"] for item in report["draft_records"]} == {
        "local_review_required"
    }
    assert report["blocked_items"][0]["action_type"] == "qianchuan_budget_review"
    assert report["blocked_items"][0]["skip_reason"] == "external_or_unsupported_delivery"
    assert report["rollback_plan"]["draft_ids_to_remove"] == [
        item["draft_id"] for item in report["draft_records"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("delivery_drafts")
    assert stored == report["draft_records"]
    assert "secret-delivery-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_delivery_drafts_is_idempotent_for_existing_local_drafts(tmp_workspace):
    first = build_delivery_drafts(_delivery_payload(tmp_workspace))
    second = build_delivery_drafts(_delivery_payload(tmp_workspace))

    assert first["summary"]["drafted_count"] == 2
    assert second["summary"]["drafted_count"] == 0
    assert second["summary"]["duplicate_count"] == 2
    assert second["delivery_state"] == "already_drafted"
    stored = JsonStore(tmp_workspace).read_collection("delivery_drafts")
    assert len(stored) == 2


def test_build_delivery_drafts_blocks_without_delivery_review(tmp_workspace):
    report = build_delivery_drafts(_delivery_payload(tmp_workspace, approved=False))

    assert report["delivery_state"] == "blocked_until_delivery_review"
    assert report["summary"]["drafted_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_delivery_review"
    assert not (tmp_workspace / "data" / "venus" / "delivery_drafts.json").exists()
    assert report["external_actions"] == []


def test_delivery_draft_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        DeliveryDraftConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_delivery_drafts",
        )
