import pytest

from venus.monitoring import build_monitoring_report


def test_build_monitoring_report_ranks_competitors_and_surfaces_opportunities():
    payload = {
        "competitors": [
            {
                "handle": "成分党A",
                "followers": 380000,
                "source": "manual-douyin-export-001",
                "videos": [
                    {
                        "title": "早C晚A翻车自查",
                        "topic": "早C晚A翻车",
                        "views": 120000,
                        "likes": 9800,
                        "comments": 1680,
                        "shares": 2400,
                        "completion_rate": 0.72,
                        "is_ad": False,
                        "ingredients": ["视黄醇", "维C"],
                        "controversies": ["刷酸叠加争议"],
                        "high_risk_comments": ["敏感肌会不会烂脸"],
                    },
                    {
                        "title": "屏障修护精华测评",
                        "topic": "屏障修护",
                        "views": 84000,
                        "likes": 5200,
                        "comments": 620,
                        "shares": 900,
                        "completion_rate": 0.61,
                        "is_ad": True,
                        "ingredients": ["泛醇", "神经酰胺NP"],
                    },
                ],
                "live_sessions": [
                    {"title": "敏感肌答疑", "duration_minutes": 95, "peak_viewers": 3200}
                ],
            },
            {
                "handle": "种草号B",
                "followers": 510000,
                "source": "manual-douyin-export-002",
                "videos": [
                    {
                        "title": "贵妇面霜必买",
                        "topic": "面霜种草",
                        "views": 200000,
                        "likes": 6000,
                        "comments": 300,
                        "shares": 500,
                        "completion_rate": 0.38,
                        "is_ad": True,
                        "controversies": ["夸大淡纹效果"],
                    }
                ],
                "live_sessions": [],
            },
        ]
    }

    report = build_monitoring_report(payload)

    assert report["summary"]["competitor_count"] == 2
    assert report["summary"]["video_count"] == 3
    assert report["summary"]["top_account"] == "成分党A"
    assert report["leaderboard"][0]["handle"] == "成分党A"
    assert report["leaderboard"][0]["ad_ratio"] == pytest.approx(0.5)
    assert report["leaderboard"][0]["live_hours"] == pytest.approx(1.58, abs=0.01)
    assert report["summary"]["risk_count"] == 3
    assert report["opportunities"][0]["action_type"] == "film"
    assert report["risk_watchlist"][0]["level"] in {"medium", "high"}
    assert report["approval_boundary"]["external_actions"] == []


def test_build_monitoring_report_rejects_empty_competitor_list():
    with pytest.raises(ValueError, match="At least one competitor"):
        build_monitoring_report({"competitors": []})
