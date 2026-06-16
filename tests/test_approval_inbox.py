import pytest

from venus.approval_inbox import ApprovalInboxConfig, build_approval_inbox


def _approval_payload():
    return {
        "source": "manual_approval_export",
        "reviewed_at": "2026-06-14T22:30:00+08:00",
        "access_token": "secret-approval-token",
        "approval_records": [
            {
                "action_type": "venus_autopilot_enablement_review",
                "approval_level": 4,
                "draft": "Review autopilot before enabling live surfaces.",
                "evidence_ids": ["connector_readiness"],
                "status": "pending",
                "reviewer": "owner",
                "created_at": "2026-06-14T22:00:00+08:00",
            },
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
                "action_type": "venus_content_publish_review",
                "approval_level": 3,
                "draft": "Review content publish package.",
                "evidence_ids": ["content-001"],
                "status": "rejected",
                "reviewer": "owner",
                "created_at": "2026-06-14T20:40:00+08:00",
            },
            {
                "action_type": "wechat_private_domain_handoff",
                "approval_level": 2,
                "draft": "Review Enterprise WeChat handoff.",
                "evidence_ids": ["wechat-001"],
                "status": "pending",
                "reviewer": "owner",
                "created_at": "2026-06-14T20:20:00+08:00",
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
                "action_type": "feishu_mobile_report",
                "decision": "needs_changes",
                "reason": "摘要需要更短。",
                "reviewer": "owner",
            },
        ],
    }


def test_build_approval_inbox_prioritizes_high_risk_manual_reviews():
    report = build_approval_inbox(_approval_payload())

    assert report["workflow"] == "approvals"
    assert report["namespace"] == "venus_approvals"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "approval_count": 6,
        "pending_count": 4,
        "approved_count": 1,
        "rejected_count": 1,
        "level4_count": 2,
        "public_or_spend_or_contact_count": 4,
        "decision_intent_count": 2,
        "second_review_count": 1,
    }

    assert [item["action_type"] for item in report["priority_queue"][:2]] == [
        "venus_autopilot_enablement_review",
        "qianchuan_budget_review",
    ]
    assert report["approval_items"][1]["surface"] == "ad_spend"
    assert report["approval_items"][1]["risk_band"] == "critical"
    assert report["surface_summary"]["ad_spend"]["pending_count"] == 1
    assert report["decision_intents"][0]["action_type"] == "qianchuan_budget_review"
    assert report["decision_intents"][0]["execution_state"] == "recorded_only"
    assert report["decision_intents"][0]["requires_second_review"] is True
    assert report["decision_intents"][1]["requires_second_review"] is False
    assert report["next_actions"][0]["action_type"] == "review_critical_approvals"
    assert "secret-approval-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_approval_inbox_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ApprovalInboxConfig(namespace="xiaolongxia_approvals")
