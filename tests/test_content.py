from venus.content import generate_hotspot_brief
from venus.persona import PersonaProfile


def test_generate_hotspot_brief_ranks_topics_and_scripts():
    profile = PersonaProfile(
        principles=["先看屏障状态", "证据和体验都要说清楚"],
        preferred_phrases=["姐妹们"],
        banned_claims=["包治", "根治", "100%有效"],
        tone="专业、口语化、克制",
    )
    hotspots = [
        {
            "topic": "早C晚A翻车",
            "type": "controversy",
            "freshness": 9,
            "relevance": 10,
            "controversy": 8,
            "evidence": ["douyin-export-001"],
        },
        {
            "topic": "夏季防晒补涂",
            "type": "routine",
            "freshness": 7,
            "relevance": 8,
            "controversy": 3,
            "evidence": ["manual-note-002"],
        },
    ]

    brief = generate_hotspot_brief(hotspots, profile)

    assert brief["top_topic"] == "早C晚A翻车"
    assert brief["ranked"][0]["score"] > brief["ranked"][1]["score"]
    assert brief["risk_tags"][0]["label"] == "争议话题"
    assert len(brief["scripts"]) == 3
    assert brief["scripts"][0]["hook"].startswith("姐妹们")
    assert "证据" in brief["analysis"]
