import pytest

from venus.approval_archive import ApprovalArchiveConfig, build_approval_archive
from venus.storage import JsonStore


def _approval_archive_payload(tmp_workspace, approved=True):
    return {
        "source": "manual_approval_archive",
        "recorded_at": "2026-06-14T23:20:00+08:00",
        "workspace_root": str(tmp_workspace),
        "archive_requested": True,
        "approved_ledger_write_review": approved,
        "access_token": "secret-archive-token",
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
        ],
        "existing_ledger_entries": [],
    }


def test_build_approval_archive_persists_ready_entries_and_skips_high_risk(tmp_workspace):
    report = build_approval_archive(_approval_archive_payload(tmp_workspace))

    assert report["workflow"] == "approval_archive"
    assert report["namespace"] == "venus_approval_archive"
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "ledger_entry_count": 2,
        "archived_count": 1,
        "duplicate_count": 0,
        "skipped_second_review_count": 1,
        "stored_total_count": 1,
    }
    assert report["archive_state"] == "archived"
    assert report["archived_entries"][0]["action_type"] == "douyin_comment_reply_queue"
    assert report["skipped_entries"][0]["action_type"] == "qianchuan_budget_review"
    assert report["skipped_entries"][0]["skip_reason"] == "requires_second_review"
    assert report["rollback_plan"]["collection"] == "approval_decision_ledger"
    assert report["rollback_plan"]["decision_ids_to_remove"] == [
        report["archived_entries"][0]["decision_id"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("approval_decision_ledger")
    assert stored == report["archived_entries"]
    assert "secret-archive-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_approval_archive_is_idempotent_for_existing_local_records(tmp_workspace):
    first = build_approval_archive(_approval_archive_payload(tmp_workspace))
    second = build_approval_archive(_approval_archive_payload(tmp_workspace))

    assert first["summary"]["archived_count"] == 1
    assert second["summary"]["archived_count"] == 0
    assert second["summary"]["duplicate_count"] == 1
    assert second["archive_state"] == "already_archived"
    stored = JsonStore(tmp_workspace).read_collection("approval_decision_ledger")
    assert len(stored) == 1


def test_build_approval_archive_blocks_without_approved_write_review(tmp_workspace):
    report = build_approval_archive(_approval_archive_payload(tmp_workspace, approved=False))

    assert report["archive_state"] == "blocked_until_ledger_write_review"
    assert report["summary"]["archived_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_ledger_write_review"
    assert not (tmp_workspace / "data" / "venus" / "approval_decision_ledger.json").exists()
    assert report["external_actions"] == []


def test_approval_archive_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ApprovalArchiveConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_approval_archive",
        )
