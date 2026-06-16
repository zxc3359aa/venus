import pytest

from venus.content_eval import ContentEvalConfig, build_content_eval_report


def _content_eval_payload():
    return {
        "source": "manual_pre_publish_review",
        "evaluated_at": "2026-06-14T20:00:00+08:00",
        "api_key": "secret-content-eval-token",
        "topic": "早C晚A翻车自查",
        "objective": "提升完播、评论和关注",
        "live_publish_requested": True,
        "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        "script_package": {
            "hook": "姐妹们，早C晚A翻车自查，先别急着跟风，3秒看懂你是不是高风险。",
            "opening": "今天不制造焦虑，直接用早C晚A翻车自查做自查。",
            "body_segments": [
                {
                    "segment_id": "point-1",
                    "spoken_line": "先判断屏障状态",
                    "purpose": "risk_filter",
                },
                {
                    "segment_id": "point-2",
                    "spoken_line": "再看成分刺激叠加，证据比情绪重要。",
                    "purpose": "evidence_check",
                },
                {
                    "segment_id": "point-3",
                    "spoken_line": "这个搭配能100%修复屏障。",
                    "purpose": "comment_trigger",
                },
            ],
            "cta": "了解了吧",
            "comment_prompt": "评论区留下肤质+产品名+使用频率，我按屏障、刺激叠加和证据帮你拆。",
            "title_options": [
                "早C晚A翻车自查",
                "敏感肌先看这3点",
                "别再盲跟早C晚A",
            ],
        },
        "shot_list": [
            {
                "scene_id": "scene-1",
                "scene_type": "hook",
                "retention_goal": "first_three_seconds",
            },
            {"scene_id": "scene-2", "scene_type": "problem_frame"},
            {"scene_id": "scene-3", "scene_type": "evidence_check"},
            {"scene_id": "scene-4", "scene_type": "decision_framework"},
            {"scene_id": "scene-5", "scene_type": "comment_cta"},
        ],
        "publish_package": {
            "caption": "早C晚A不是让你跟风，是先看肤质、耐受和证据。",
            "hashtags": ["#早C晚A", "#护肤", "#屏障护理"],
            "pinned_comment_draft": "评论区留下肤质+产品名+使用频率，我帮你拆风险。",
        },
        "evidence_ids": [],
        "risk_notes": ["避免100%修复屏障这类绝对功效承诺"],
        "forbidden_claims": ["100%修复屏障"],
    }


def test_build_content_eval_report_scores_growth_and_blocks_claim_risk():
    report = build_content_eval_report(_content_eval_payload())

    assert report["workflow"] == "content_eval"
    assert report["namespace"] == "venus_content_eval"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "dimension_count": 6,
        "overall_score": 87,
        "revision_count": 3,
        "high_priority_revision_count": 2,
        "blocking_issue_count": 1,
        "approval_record_count": 2,
        "publish_ready": False,
    }

    assert report["scorecard"]["retention_score"]["score"] >= 90
    assert report["scorecard"]["comment_score"]["score"] >= 90
    assert report["scorecard"]["follow_score"]["status"] == "needs_work"
    assert report["scorecard"]["safety_score"]["status"] == "blocked"
    assert report["publish_readiness"]["status"] == "blocked_by_claim_risk"
    assert report["publish_readiness"]["manual_review_level"] == 3
    assert {item["category"] for item in report["revision_queue"]} == {
        "claim_safety",
        "evidence_gap",
        "follow_cta",
    }
    assert report["revision_queue"][0]["priority"] == "high"
    assert report["kpi_definitions"]["retention_score"]["decision_use"] == "判断开头和节奏是否值得进入剪辑。"
    assert {record["action_type"] for record in report["approval_records"]} == {
        "venus_content_revision_review",
        "venus_content_publish_review",
    }
    assert "secret-content-eval-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_content_eval_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ContentEvalConfig(namespace="xiaolongxia_content_eval")
