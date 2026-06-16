import pytest

from venus.video_production import ProductionConfig, build_video_production_package


def _production_payload():
    return {
        "source": "manual_content_brief",
        "retrieved_at": "2026-06-14T14:00:00+08:00",
        "api_key": "secret-production-token",
        "topic": "早C晚A翻车自查",
        "format": "douyin_short_video",
        "duration_seconds": 45,
        "objective": "提升完播、评论和关注",
        "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        "key_points": [
            "先判断屏障状态",
            "再看成分刺激叠加",
            "最后给评论区肤质自查问题",
        ],
        "risk_notes": ["避免100%修复屏障这类绝对功效承诺"],
        "broll_assets": ["评论截图", "成分表特写", "备案截图"],
    }


def test_build_video_production_package_creates_script_shots_edit_and_publish_package():
    package = build_video_production_package(_production_payload())

    assert package["workflow"] == "production"
    assert package["namespace"] == "venus_production"
    assert package["dry_run"] is True
    assert package["approval_mode"] == "manual"
    assert package["external_actions"] == []
    assert package["summary"] == {
        "duration_seconds": 45,
        "scene_count": 5,
        "subtitle_card_count": 5,
        "broll_asset_count": 3,
        "title_option_count": 3,
        "approval_gated_action_count": 2,
    }

    assert "早C晚A翻车自查" in package["script_package"]["hook"]
    assert package["script_package"]["comment_prompt"].startswith("评论区")
    assert package["shot_list"][0]["retention_goal"] == "first_three_seconds"
    assert package["shot_list"][-1]["scene_type"] == "comment_cta"
    assert package["edit_plan"]["timeline"][0]["cut_style"] == "jump_cut"
    assert package["subtitle_cards"][0]["emphasis"] == "争议先抛出，别铺垫"
    assert package["publish_package"]["cover_text"] == "早C晚A翻车自查"
    assert "#早C晚A" in package["publish_package"]["hashtags"]
    assert all(item["status"] == "needs_review" for item in package["asset_checklist"])

    assert len(package["approval_records"]) == 2
    assert {record["status"] for record in package["approval_records"]} == {"pending"}
    assert {
        record["action_type"] for record in package["approval_records"]
    } == {
        "venus_video_claim_review",
        "venus_video_publish_review",
    }
    assert "secret-production-token" not in str(package)
    assert "Xiaolongxia" not in str(package)
    assert "小龙虾" not in str(package)


def test_production_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        ProductionConfig(namespace="xiaolongxia_production")
