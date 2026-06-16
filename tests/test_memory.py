import pytest

from venus.memory import MemoryConfig, build_memory_report


def _memory_payload():
    return {
        "source": "manual_memory_review",
        "retrieved_at": "2026-06-14T18:00:00+08:00",
        "api_key": "secret-memory-token",
        "current_memory": {
            "version": "v3",
            "principles": ["先看屏障状态"],
            "style_phrases": ["姐妹们"],
            "product_beliefs": ["成分要看浓度、配方和肤质"],
            "content_rules": ["先抛出用户真实问题，再给专业判断"],
            "banned_claims": ["100%修复屏障"],
            "privacy_boundaries": ["不记录手机号、地址、订单号等直接个人信息"],
        },
        "learning_candidates": [
            {
                "candidate_id": "mem-001",
                "category": "principles",
                "proposed_rule": "先判断屏障状态，再谈功效、搭配和频率。",
                "evidence": ["fb-001"],
                "source": "content_feedback",
            },
            {
                "candidate_id": "mem-002",
                "category": "style_phrases",
                "proposed_rule": "姐妹们，先别急着跟风。",
                "evidence": ["script-001"],
                "source": "script_edit",
            },
            {
                "candidate_id": "mem-003",
                "category": "privacy_boundaries",
                "proposed_rule": "用户联系方式 contact-token-001 不进入任何记忆。",
                "evidence": ["privacy-001"],
                "source": "comment_review",
                "contains_personal_data": True,
            },
        ],
        "approval_decisions": [
            {"candidate_id": "mem-001", "decision": "approved", "reviewer": "owner"},
            {"candidate_id": "mem-002", "decision": "pending", "reviewer": "owner"},
            {"candidate_id": "mem-003", "decision": "approved", "reviewer": "owner"},
        ],
        "backup": {
            "target": "local-memory-ledger",
            "last_snapshot_version": "v3",
            "last_backup_at": "2026-06-14T07:00:00+08:00",
            "last_verified_at": "",
            "status": "missing_verification",
        },
    }


def test_build_memory_report_stages_approved_rules_without_writing_memory():
    report = build_memory_report(_memory_payload())

    assert report["workflow"] == "memory"
    assert report["namespace"] == "venus_memory"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "current_version": "v3",
        "candidate_count": 3,
        "approved_candidate_count": 2,
        "rejected_candidate_count": 0,
        "pending_candidate_count": 1,
        "blocked_sensitive_candidate_count": 1,
        "proposed_version": "v4",
        "proposed_change_count": 1,
        "backup_issue_count": 1,
        "approval_gated_action_count": 2,
    }

    assert report["candidate_reviews"][0]["candidate_id"] == "mem-001"
    assert report["candidate_reviews"][0]["decision"] == "approved"
    assert report["candidate_reviews"][0]["execution_state"] == "staged_for_manual_merge"
    assert report["candidate_reviews"][1]["execution_state"] == "blocked_until_approved"
    assert report["candidate_reviews"][2]["privacy_flag"] is True
    assert report["candidate_reviews"][2]["execution_state"] == "blocked_sensitive_data"

    assert report["memory_diff"]["additions"]["principles"] == [
        "先判断屏障状态，再谈功效、搭配和频率。"
    ]
    assert report["memory_diff"]["excluded_candidate_ids"] == ["mem-002", "mem-003"]
    assert report["proposed_memory"]["version"] == "v4"
    assert report["proposed_memory"]["previous_version"] == "v3"
    assert "先判断屏障状态，再谈功效、搭配和频率。" in report["proposed_memory"]["principles"]
    assert "姐妹们，先别急着跟风。" not in report["proposed_memory"]["style_phrases"]
    assert report["rollback_plan"]["from_version"] == "v4"
    assert report["rollback_plan"]["to_version"] == "v3"
    assert report["rollback_plan"]["execution_state"] == "blocked_until_approved"
    assert report["backup_tasks"][0]["target"] == "local-memory-ledger"
    assert report["backup_tasks"][0]["execution_state"] == "blocked_until_approved"
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_memory_merge",
        "venus_memory_backup_verification",
    }
    assert "secret-memory-token" not in str(report)
    assert "contact-token-001" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_memory_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        MemoryConfig(namespace="xiaolongxia_memory")
