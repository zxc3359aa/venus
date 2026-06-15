import pytest

from venus.douyin_engagement import DouyinEngagementConfig, build_douyin_engagement_report


def _douyin_payload():
    return {
        "source": "manual_douyin_export",
        "retrieved_at": "2026-06-14T10:00:00+08:00",
        "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        "auth_token": "secret-douyin-token",
        "videos": [
            {
                "video_id": "video-001",
                "title": "早C晚A翻车自查",
                "published_at": "2026-06-13T20:00:00+08:00",
                "comments": [
                    {
                        "comment_id": "c1",
                        "user_id": "open-user-secret",
                        "text": "敏感肌用了会不会烂脸？",
                        "likes": 18,
                        "created_at": "2026-06-14T09:10:00+08:00",
                    },
                    {
                        "comment_id": "c2",
                        "user_id": "open-user-002",
                        "text": "求平价替代，学生党能不能用？",
                        "likes": 9,
                        "created_at": "2026-06-14T09:30:00+08:00",
                    },
                ],
            }
        ],
        "live_sessions": [
            {
                "session_id": "live-001",
                "started_at": "2026-06-14T08:00:00+08:00",
                "messages": [
                    {
                        "message_id": "l1",
                        "user_id": "live-user-001",
                        "text": "刷酸爆皮了还能叠加这个吗？",
                        "likes": 3,
                        "created_at": "2026-06-14T08:20:00+08:00",
                    }
                ],
            }
        ],
    }


def test_build_douyin_engagement_report_summarizes_comments_and_live_queue():
    report = build_douyin_engagement_report(_douyin_payload())

    assert report["workflow"] == "douyin"
    assert report["dry_run"] is True
    assert report["namespace"] == "venus_douyin"
    assert report["external_actions"] == []
    assert report["source"]["source_type"] == "manual_douyin_export"
    assert report["summary"] == {
        "video_count": 1,
        "comment_count": 2,
        "live_session_count": 1,
        "live_message_count": 1,
        "high_risk_comment_count": 1,
        "high_risk_live_message_count": 1,
        "approval_gated_reply_count": 2,
    }

    assert report["video_summaries"][0]["video_id"] == "video-001"
    assert report["video_summaries"][0]["top_comment_intents"] == ["risk_question", "shopping_advice"]
    assert report["reply_queue"][0]["comment_id"] == "c1"
    assert report["reply_queue"][0]["approval_level"] == 3
    assert report["reply_queue"][0]["execution_state"] == "blocked_until_approved"
    assert "肤质" in report["reply_queue"][0]["draft_reply"]
    assert report["live_queue"][0]["message_id"] == "l1"
    assert report["live_queue"][0]["approval_level"] == 4
    assert report["live_queue"][0]["execution_state"] == "blocked_until_approved"
    assert report["approval_records"]
    assert {record["action_type"] for record in report["approval_records"]} == {
        "douyin_comment_reply",
        "douyin_live_reply",
    }
    assert "secret-douyin-token" not in str(report)
    assert "open-user-secret" not in str(report)


def test_douyin_engagement_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        DouyinEngagementConfig(namespace="xiaolongxia_douyin")
