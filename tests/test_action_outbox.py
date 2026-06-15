import pytest

from venus.action_outbox import ActionOutboxConfig, build_action_outbox
from venus.storage import JsonStore


def _action_outbox_payload(tmp_workspace, approved=True):
    return {
        "source": "manual_action_outbox",
        "workspace_root": str(tmp_workspace),
        "queued_at": "2026-06-14T23:40:00+08:00",
        "execution_requested": True,
        "approved_execution_review": approved,
        "access_token": "secret-action-token",
        "action_plan": [
            {
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "surface": "feishu",
                "approval_level": 2,
                "draft": "Prepare a private Feishu card summary.",
                "external_action_enabled": False,
            },
            {
                "action_id": "qianchuan-budget-001",
                "action_type": "qianchuan_budget_review",
                "surface": "qianchuan",
                "approval_level": 4,
                "draft": "Review budget before spend changes.",
                "external_action_enabled": False,
            },
            {
                "action_id": "airtable-sync-001",
                "action_type": "airtable_sync_review",
                "surface": "airtable",
                "approval_level": 2,
                "draft": "Review Airtable sync package.",
                "external_action_enabled": False,
            },
        ],
        "archived_decisions": [
            {
                "decision_id": "feishu_mobile_report-approve-owner-feishu_mobile_report-20260614-2000000800",
                "action_type": "feishu_mobile_report",
                "decision": "approve",
                "reviewer": "owner",
                "approval_level": 2,
                "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                "archive_state": "archived",
                "record_state": "ready_for_local_ledger_review",
            },
            {
                "decision_id": "qianchuan_budget_review-approve-owner-qianchuan_budget_review-20260614-2130000800",
                "action_type": "qianchuan_budget_review",
                "decision": "approve",
                "reviewer": "owner",
                "approval_level": 4,
                "matched_approval_id": "qianchuan_budget_review-20260614-2130000800",
                "archive_state": "archived",
                "record_state": "ready_for_local_ledger_review",
            },
            {
                "decision_id": "airtable_sync_review-reject-owner-airtable_sync_review-20260614-2020000800",
                "action_type": "airtable_sync_review",
                "decision": "reject",
                "reviewer": "owner",
                "approval_level": 2,
                "matched_approval_id": "airtable_sync_review-20260614-2020000800",
                "archive_state": "archived",
                "record_state": "ready_for_local_ledger_review",
            },
        ],
    }


def test_build_action_outbox_queues_approved_local_actions_and_blocks_external(tmp_workspace):
    report = build_action_outbox(_action_outbox_payload(tmp_workspace))

    assert report["workflow"] == "action_outbox"
    assert report["namespace"] == "venus_action_outbox"
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["outbox_state"] == "queued"
    assert report["summary"] == {
        "action_count": 3,
        "queued_count": 1,
        "duplicate_count": 0,
        "blocked_count": 1,
        "rejected_count": 1,
        "missing_decision_count": 0,
        "stored_total_count": 1,
    }
    assert report["queued_items"][0]["action_type"] == "feishu_mobile_report"
    assert report["queued_items"][0]["delivery_state"] == "local_manual_dispatch_required"
    assert report["blocked_items"][0]["action_type"] == "qianchuan_budget_review"
    assert report["blocked_items"][0]["skip_reason"] == "external_or_high_risk_action"
    assert report["rejected_items"][0]["action_type"] == "airtable_sync_review"
    assert report["rejected_items"][0]["skip_reason"] == "decision_not_approved"
    assert report["rollback_plan"]["outbox_ids_to_remove"] == [
        report["queued_items"][0]["outbox_id"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("action_outbox")
    assert stored == report["queued_items"]
    assert "secret-action-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_action_outbox_is_idempotent_for_existing_local_queue(tmp_workspace):
    first = build_action_outbox(_action_outbox_payload(tmp_workspace))
    second = build_action_outbox(_action_outbox_payload(tmp_workspace))

    assert first["summary"]["queued_count"] == 1
    assert second["summary"]["queued_count"] == 0
    assert second["summary"]["duplicate_count"] == 1
    assert second["outbox_state"] == "already_queued"
    stored = JsonStore(tmp_workspace).read_collection("action_outbox")
    assert len(stored) == 1


def test_build_action_outbox_blocks_without_execution_review(tmp_workspace):
    report = build_action_outbox(_action_outbox_payload(tmp_workspace, approved=False))

    assert report["outbox_state"] == "blocked_until_execution_review"
    assert report["summary"]["queued_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_execution_review"
    assert not (tmp_workspace / "data" / "venus" / "action_outbox.json").exists()
    assert report["external_actions"] == []


def test_action_outbox_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ActionOutboxConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_action_outbox",
        )
