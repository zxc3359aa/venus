from venus.persona import PersonaProfile, build_persona_profile, rewrite_in_persona


def test_build_persona_profile_extracts_style_rules():
    samples = [
        "姐妹们，别一上来就追猛药，先看自己的屏障状态。",
        "这个成分不是不能用，而是要看浓度、搭配和你的皮肤耐受。",
        "我不喜欢把护肤讲成玄学，证据和体验都要说清楚。",
    ]

    profile = build_persona_profile(samples)

    assert "先看屏障状态" in profile.principles
    assert "证据和体验都要说清楚" in profile.principles
    assert "姐妹们" in profile.preferred_phrases
    assert "包治" in profile.banned_claims


def test_rewrite_in_persona_adds_style_and_boundaries():
    profile = PersonaProfile(
        principles=["先看屏障状态", "证据和体验都要说清楚"],
        preferred_phrases=["姐妹们"],
        banned_claims=["包治", "根治", "100%有效"],
        tone="专业、口语化、克制",
    )

    draft = "这个产品可以修护皮肤。"

    rewritten = rewrite_in_persona(draft, profile)

    assert rewritten.startswith("姐妹们，")
    assert "先看屏障状态" in rewritten
    assert "包治" not in rewritten
    assert "100%有效" not in rewritten
