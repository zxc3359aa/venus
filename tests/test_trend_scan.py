import pytest

from venus.trend_scan import TrendScanConfig, build_trend_scan_report


def _trend_scan_payload():
    return {
        "source": "manual_douyin_beauty_scan",
        "retrieved_at": "2026-06-14T15:00:00+08:00",
        "refresh_interval_minutes": 15,
        "access_token": "secret-douyin-token",
        "live_connector_requested": True,
        "topics": [
            {
                "id": "topic-001",
                "label": "早C晚A翻车",
                "mentions": 320000,
                "growth": 0.82,
                "controversy": 0.78,
                "evidence": ["douyin-hot-001"],
            }
        ],
        "products": [
            {
                "id": "prod-001",
                "label": "屏障修护精华",
                "brand": "示例品牌",
                "mentions": 98000,
                "growth": 0.64,
                "controversy": 0.7,
                "evidence": ["douyin-product-001"],
            }
        ],
        "creators": [
            {
                "id": "creator-001",
                "handle": "成分党A",
                "mentions": 65000,
                "growth": 0.55,
                "controversy": 0.4,
                "evidence": ["douyin-creator-001"],
            }
        ],
        "comments": [
            {
                "id": "comment-001",
                "text": "敏感肌用了会不会烂脸？",
                "likes": 1800,
                "growth": 0.8,
                "controversy": 0.9,
                "evidence": ["douyin-comment-001"],
            }
        ],
        "ingredients": [
            {
                "id": "ing-001",
                "label": "视黄醇",
                "mentions": 120000,
                "growth": 0.7,
                "controversy": 0.85,
                "evidence": ["douyin-ingredient-001"],
            }
        ],
        "tags": [
            {
                "id": "tag-001",
                "label": "早C晚A",
                "mentions": 260000,
                "growth": 0.74,
                "controversy": 0.6,
                "evidence": ["douyin-tag-001"],
            }
        ],
        "controversies": [
            {
                "id": "risk-001",
                "label": "A醇叠加刷酸爆皮",
                "mentions": 88000,
                "growth": 0.71,
                "controversy": 0.92,
                "evidence": ["douyin-risk-001"],
            }
        ],
    }


def test_build_trend_scan_report_normalizes_all_douyin_beauty_signals():
    report = build_trend_scan_report(_trend_scan_payload())

    assert report["workflow"] == "trend_scan"
    assert report["namespace"] == "venus_trend_scan"
    assert report["dry_run"] is True
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["summary"] == {
        "signal_count": 7,
        "hot_topic_count": 1,
        "hot_product_count": 1,
        "hot_creator_count": 1,
        "hot_comment_count": 1,
        "hot_ingredient_count": 1,
        "hot_tag_count": 1,
        "controversy_count": 1,
        "content_opportunity_count": 3,
        "refresh_interval_minutes": 15,
        "approval_gated_action_count": 1,
    }

    signal_types = {signal["signal_type"] for signal in report["normalized_signals"]}
    assert signal_types == {
        "topic",
        "product",
        "creator",
        "comment",
        "ingredient",
        "tag",
        "controversy",
    }
    assert report["leaderboard"][0]["label"] == "早C晚A翻车"
    assert report["leaderboard"][0]["priority"] == "urgent"
    assert report["trend_clusters"][0]["primary_topic"] == "早C晚A翻车"
    assert "屏障修护精华" in report["trend_clusters"][0]["related_products"]
    assert report["content_opportunities"][0]["hook"].startswith("早C晚A翻车")
    assert report["content_opportunities"][0]["comment_prompt"].startswith("评论区")
    assert "争议" in report["content_opportunities"][0]["filming_advice"]
    assert report["watch_plan"]["refresh_interval_minutes"] == 15
    assert report["watch_plan"]["coverage_targets"] == [
        "topics",
        "products",
        "creators",
        "comments",
        "ingredients",
        "tags",
        "controversies",
    ]
    assert report["watch_plan"]["gap_alerts"] == []
    assert report["watch_plan"]["live_connector_state"] == "blocked_until_approved"
    assert report["approval_records"][0]["action_type"] == "venus_live_trend_scan_connector"
    assert report["approval_records"][0]["status"] == "pending"
    assert "secret-douyin-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_trend_scan_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        TrendScanConfig(namespace="xiaolongxia_trend_scan")
