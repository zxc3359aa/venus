import pytest

from venus.wechat_private_domain import (
    WeChatPrivateDomainConfig,
    build_wechat_private_domain_report,
)


def _wechat_payload():
    return {
        "source": "mini_program_export",
        "retrieved_at": "2026-06-14T11:00:00+08:00",
        "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        "app_secret": "secret-wechat-value",
        "mini_program_sessions": [
            {
                "session_id": "mp-001",
                "openid": "openid-secret",
                "nickname": "敏敏",
                "questions": [
                    {
                        "question_id": "q1",
                        "text": "屏障受损泛红，早C晚A还能继续吗？",
                        "created_at": "2026-06-14T10:30:00+08:00",
                    },
                    {
                        "question_id": "q2",
                        "text": "我想加企业微信进群，让你帮我看产品搭配",
                        "created_at": "2026-06-14T10:33:00+08:00",
                    },
                ],
                "contact": {
                    "wechat_id": "wxid-private",
                    "phone": "13800000000",
                },
            }
        ],
    }


def test_build_wechat_private_domain_report_creates_qna_and_handoff_queues():
    report = build_wechat_private_domain_report(_wechat_payload())

    assert report["workflow"] == "wechat"
    assert report["namespace"] == "venus_wechat"
    assert report["dry_run"] is True
    assert report["external_actions"] == []
    assert report["source"]["source_type"] == "mini_program_export"
    assert report["summary"] == {
        "session_count": 1,
        "question_count": 2,
        "high_risk_question_count": 1,
        "lead_intent_count": 1,
        "enterprise_wechat_handoff_count": 1,
        "approval_gated_action_count": 2,
    }

    assert report["answer_queue"][0]["question_id"] == "q1"
    assert report["answer_queue"][0]["approval_level"] == 4
    assert report["answer_queue"][0]["execution_state"] == "blocked_until_approved"
    assert "屏障" in report["answer_queue"][0]["draft_answer"]
    assert report["handoff_queue"][0]["session_id"] == "mp-001"
    assert report["handoff_queue"][0]["approval_level"] == 4
    assert report["handoff_queue"][0]["handoff_channel"] == "enterprise_wechat"
    assert "加企业微信" in report["handoff_queue"][0]["handoff_script"]
    assert {record["action_type"] for record in report["approval_records"]} == {
        "wechat_mini_program_answer",
        "enterprise_wechat_handoff",
    }
    rendered = str(report)
    assert "secret-wechat-value" not in rendered
    assert "openid-secret" not in rendered
    assert "wxid-private" not in rendered
    assert "13800000000" not in rendered


def test_wechat_private_domain_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        WeChatPrivateDomainConfig(namespace="xiaolongxia_wechat")
