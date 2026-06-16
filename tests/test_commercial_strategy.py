import pytest

from venus.commercial_strategy import CommercialStrategyConfig, build_commercial_strategy_report


def _commercial_payload():
    return {
        "source": "manual_commercial_brief",
        "retrieved_at": "2026-06-14T12:00:00+08:00",
        "access_token": "secret-commercial-token",
        "qianchuan": {
            "campaign_id": "qc-001",
            "objective": "直播间成交",
            "daily_budget": 3000,
            "spent_today": 1800,
            "roi": 1.4,
            "target_roi": 2.0,
            "audiences": ["敏感肌", "屏障修护", "早C晚A兴趣"],
            "creatives": [
                {
                    "creative_id": "ad-001",
                    "title": "早C晚A翻车自查",
                    "completion_rate": 0.72,
                    "ctr": 0.035,
                    "conversion_rate": 0.018,
                },
                {
                    "creative_id": "ad-002",
                    "title": "屏障修护精华测评",
                    "completion_rate": 0.41,
                    "ctr": 0.012,
                    "conversion_rate": 0.006,
                },
            ],
        },
        "xingtu": {
            "brief_id": "xt-001",
            "brand": "示例品牌",
            "product": "屏障修护精华",
            "budget": 50000,
            "requirements": [
                "突出100%修复屏障",
                "必须口播三次品牌名",
                "评论区引导私信购买",
            ],
            "forbidden_claims": ["100%修复屏障"],
            "deliverables": ["60秒短视频", "直播口播切片"],
        },
        "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
    }


def test_build_commercial_strategy_report_gates_qianchuan_and_xingtu_actions():
    report = build_commercial_strategy_report(_commercial_payload())

    assert report["workflow"] == "commercial"
    assert report["namespace"] == "venus_commercial"
    assert report["dry_run"] is True
    assert report["external_actions"] == []
    assert report["source"]["source_type"] == "manual_commercial_brief"
    assert report["summary"] == {
        "qianchuan_campaign_count": 1,
        "xingtu_brief_count": 1,
        "high_risk_brief_count": 1,
        "budget_recommendation_count": 1,
        "script_recommendation_count": 2,
        "approval_gated_action_count": 3,
    }

    budget = report["qianchuan_recommendations"][0]
    assert budget["campaign_id"] == "qc-001"
    assert budget["recommendation_type"] == "budget_guardrail"
    assert budget["approval_level"] == 4
    assert budget["execution_state"] == "blocked_until_approved"
    assert "不要加预算" in budget["recommendation"]

    brief = report["xingtu_brief_reviews"][0]
    assert brief["brief_id"] == "xt-001"
    assert brief["risk_level"] == "high"
    assert "100%修复屏障" in brief["forbidden_claims"]
    assert brief["approval_level"] == 4
    assert brief["execution_state"] == "blocked_until_approved"

    scripts = report["commercial_script_recommendations"]
    assert [script["script_type"] for script in scripts] == ["short_video_ad", "live_slice"]
    assert all(script["approval_level"] == 1 for script in scripts)
    assert "证据" in scripts[0]["hook"]

    assert {record["action_type"] for record in report["approval_records"]} == {
        "qianchuan_budget_recommendation",
        "xingtu_brief_decision",
        "xingtu_brand_commitment",
    }
    assert "secret-commercial-token" not in str(report)


def test_commercial_strategy_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        CommercialStrategyConfig(namespace="xiaolongxia_commercial")
