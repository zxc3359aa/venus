from venus.comments import analyze_comments
from venus.persona import PersonaProfile


def test_analyze_comments_classifies_risk_and_drafts_replies():
    profile = PersonaProfile(
        principles=["先看屏障状态"],
        preferred_phrases=["姐妹们"],
        banned_claims=["包治", "根治", "100%有效"],
        tone="专业、口语化、克制",
    )
    comments = [
        {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
        {"id": "c2", "text": "这个是不是100%能修复屏障？"},
        {"id": "c3", "text": "求平价替代！"},
    ]

    result = analyze_comments(comments, profile)

    assert result["summary"]["total"] == 3
    assert result["items"][1]["risk"] == "high"
    assert result["items"][1]["approval_level"] == 3
    assert result["items"][0]["draft_reply"].startswith("姐妹们")
    assert "100%有效" not in result["items"][1]["draft_reply"]
