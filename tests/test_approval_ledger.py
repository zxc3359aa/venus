import pytest

from venus.approval_ledger import ApprovalLedgerConfig, build_approval_ledger


def _approval_ledger_payload():
    return {
        "source": "manual_approval_ledger",
        "recorded_at": "2026-06-14T23:00:00+08:00",
        "access_token": "secret-ledger-token",
        "write_requested": True,
        "approval_records": [
            {
                "action_type": "qianchuan_budget_review",
                "approval_level": 4,
                "draft": "Review budget before changing spend.",
                "evidence_ids": ["qianchuan-app-001"],
                "status": "pending",
                "reviewer": "owner",
                "created_at": "2026-06-14T21:30:00+08:00",
            },
            {
                "action_type": "douyin_comment_reply_queue",
                "approval_level": 3,
                "draft": "Review high-risk Douyin reply drafts.",
                "evidence_ids": ["comment-001"],
                "status": "pending",
                "reviewer": "owner",
                "created_at": "2026-06-14T21:10:00+08:00",
            },
            {
                "action_type": "feishu_mobile_report",
                "approval_level": 2,
                "draft": "Send private Feishu summary.",
                "evidence_ids": ["run-001"],
                "status": "approved",
                "reviewer": "owner",
                "created_at": "2026-06-14T20:00:00+08:00",
            },
        ],
        "requested_decisions": [
            {
                "action_type": "qianchuan_budget_review",
                "decision": "approve",
                "reason": "预算建议合理，但仍需二次确认。",
                "reviewer": "owner",
            },
            {
                "action_type": "douyin_comment_reply_queue",
                "decision": "reject",
                "reason": "回复语气还需要更克制。",
                "reviewer": "owner",
            },
            {
                "action_type": "feishu_mobile_report",
                "decision": "needs_changes",
                "reason": "摘要需要更短。",
                "reviewer": "owner",
            },
        ],
        "existing_ledger_entries": [
            {
                "decision_id": "feishu_mobile_report-needs_changes-owner-feishu_mobile_report-20260614-2000000800",
                "action_type": "feishu_mobile_report",
                "decision": "needs_changes",
                "reviewer": "owner",
                "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
            }
        ],
    }


def test_build_approval_ledger_drafts_deduplicated_decision_entries():
    report = build_approval_ledger(_approval_ledger_payload())

    assert report["workflow"] == "approval_ledger"
    assert report["namespace"] == "venus_approval_ledger"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "decision_intent_count": 3,
        "new_entry_count": 2,
        "duplicate_intent_count": 1,
        "second_review_count": 1,
        "ready_to_record_count": 1,
        "blocked_intent_count": 1,
        "approval_record_count": 2,
    }

    assert report["ledger_entries"][0]["action_type"] == "qianchuan_budget_review"
    assert report["ledger_entries"][0]["record_state"] == "blocked_for_second_review"
    assert report["ledger_entries"][0]["requires_second_review"] is True
    assert report["ledger_entries"][1]["action_type"] == "douyin_comment_reply_queue"
    assert report["ledger_entries"][1]["record_state"] == "ready_for_local_ledger_review"
    assert report["duplicate_intents"][0]["action_type"] == "feishu_mobile_report"
    assert report["write_plan"] == {
        "target_collection": "approval_decision_ledger",
        "write_requested": True,
        "record_count": 2,
        "existing_entry_count": 1,
        "execution_state": "blocked_until_approved",
        "external_action_enabled": False,
    }
    assert report["rollback_plan"]["decision_ids_to_remove"] == [
        report["ledger_entries"][0]["decision_id"],
        report["ledger_entries"][1]["decision_id"],
    ]
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_approval_ledger_write_review",
        "venus_high_risk_decision_second_review",
    }
    assert "secret-ledger-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_approval_ledger_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ApprovalLedgerConfig(namespace="xiaolongxia_approval_ledger")
