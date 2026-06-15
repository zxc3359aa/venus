import pytest

from venus.performance import PerformanceConfig, build_performance_report


def _performance_payload():
    return {
        "source": "manual_douyin_video_metrics",
        "analyzed_at": "2026-06-14T21:00:00+08:00",
        "api_key": "secret-performance-token",
        "live_metrics_requested": True,
        "targets": {
            "completion_rate": 0.65,
            "comment_rate": 0.03,
            "follow_rate": 0.008,
            "negative_feedback_rate": 0.015,
        },
        "videos": [
            {
                "video_id": "video-001",
                "title": "早C晚A翻车自查",
                "topic": "早C晚A翻车",
                "published_at": "2026-06-14T10:00:00+08:00",
                "views": 120000,
                "completion_rate": 0.72,
                "comment_rate": 0.042,
                "follow_rate": 0.011,
                "share_rate": 0.018,
                "negative_feedback_rate": 0.006,
                "content_eval_score": 87,
                "content_eval_status": "blocked_by_claim_risk",
                "hook_type": "controversy_self_check",
                "cta_type": "skin_product_frequency_comment",
                "persona_fit": 0.92,
                "claim_risk": "medium",
                "evidence": ["video-metric-001"],
            },
            {
                "video_id": "video-002",
                "title": "温和洁面怎么选",
                "topic": "温和洁面",
                "published_at": "2026-06-13T10:00:00+08:00",
                "views": 68000,
                "completion_rate": 0.54,
                "comment_rate": 0.017,
                "follow_rate": 0.004,
                "share_rate": 0.006,
                "negative_feedback_rate": 0.021,
                "content_eval_score": 76,
                "content_eval_status": "needs_revision",
                "hook_type": "generic_tips",
                "cta_type": "generic",
                "persona_fit": 0.71,
                "claim_risk": "low",
                "evidence": ["video-metric-002"],
            },
            {
                "video_id": "video-003",
                "title": "屏障修护精华备案拆解",
                "topic": "屏障修护精华",
                "published_at": "2026-06-12T10:00:00+08:00",
                "views": 92000,
                "completion_rate": 0.68,
                "comment_rate": 0.036,
                "follow_rate": 0.009,
                "share_rate": 0.014,
                "negative_feedback_rate": 0.011,
                "content_eval_score": 83,
                "content_eval_status": "ready_for_manual_publish_review",
                "hook_type": "evidence_breakdown",
                "cta_type": "product_name_comment",
                "persona_fit": 0.88,
                "claim_risk": "low",
                "evidence": ["video-metric-003"],
            },
        ],
    }


def test_build_performance_report_calibrates_content_loop():
    report = build_performance_report(_performance_payload())

    assert report["workflow"] == "performance"
    assert report["namespace"] == "venus_performance"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "video_count": 3,
        "winner_count": 2,
        "underperformer_count": 1,
        "average_completion_rate": 0.647,
        "average_comment_rate": 0.032,
        "average_follow_rate": 0.008,
        "negative_feedback_alert_count": 1,
        "calibration_rule_count": 3,
        "approval_record_count": 2,
    }

    assert report["leaderboard"][0]["video_id"] == "video-001"
    assert report["leaderboard"][0]["growth_score"] == 47.5
    assert report["leaderboard"][1]["video_id"] == "video-003"
    assert report["leaderboard"][2]["video_id"] == "video-002"
    assert report["underperformers"][0]["video_id"] == "video-002"
    assert report["video_reviews"][1]["negative_feedback_alert"] is True
    assert {item["category"] for item in report["calibration_rules"]} == {
        "amplify_winning_hook",
        "repair_generic_cta",
        "claim_safety_calibration",
    }
    assert report["next_actions"][0]["action_type"] == "draft_next_video_from_winner"
    assert report["next_actions"][0]["execution_state"] == "blocked_until_approved"
    assert (
        report["kpi_definitions"]["completion_rate"]["decision_use"]
        == "判断前3秒和剪辑节奏是否真正留住观众。"
    )
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_performance_learning_review",
        "venus_performance_next_content_review",
    }
    assert "secret-performance-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_performance_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        PerformanceConfig(namespace="xiaolongxia_performance")
