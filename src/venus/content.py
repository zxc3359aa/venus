from __future__ import annotations

from typing import Any

from venus.persona import PersonaProfile, rewrite_in_persona


def score_hotspot(item: dict[str, Any]) -> int:
    return (
        int(item.get("freshness", 0)) * 3
        + int(item.get("relevance", 0)) * 4
        + int(item.get("controversy", 0)) * 2
    )


def generate_hotspot_brief(hotspots: list[dict[str, Any]], profile: PersonaProfile) -> dict[str, Any]:
    if not hotspots:
        raise ValueError("At least one hotspot is required")

    ranked = sorted(
        [{**item, "score": score_hotspot(item)} for item in hotspots],
        key=lambda item: item["score"],
        reverse=True,
    )
    top = ranked[0]
    topic = top["topic"]
    risk_tags = []
    if int(top.get("controversy", 0)) >= 7:
        risk_tags.append({"label": "争议话题", "level": "high", "reason": "争议分高，需要证据和克制表达"})
    else:
        risk_tags.append({"label": "常规选题", "level": "low", "reason": "争议分较低，适合科普表达"})

    base = f"{topic}可以切入，但要把证据、肤质差异和使用场景讲清楚。"
    persona_line = rewrite_in_persona(base, profile)
    scripts = [
        {
            "hook": f"{profile.preferred_phrases[0]}，{topic}最近又吵起来了，但真正该看的不是情绪。",
            "body": persona_line,
            "cta": "你们把自己的肤质和正在用的搭配打在评论区，我帮你们拆风险。",
        },
        {
            "hook": f"别急着跟风{topic}，先用30秒判断你适不适合。",
            "body": f"第一看屏障，第二看频率，第三看有没有同类功效叠加。{base}",
            "cta": "收藏这条，下次买之前先对照。",
        },
        {
            "hook": f"{topic}不是不能讲，关键是别把护肤讲成玄学。",
            "body": f"我会把支持证据、争议点和适合人群分开说。{persona_line}",
            "cta": "想看我拆哪款产品，评论区留名字。",
        },
    ]

    return {
        "top_topic": topic,
        "analysis": f"围绕{topic}做内容，重点是证据、肤质差异和评论互动。",
        "filming_advice": "开头直接抛争议，中段给判断框架，结尾引导用户留下肤质和产品名。",
        "ranked": ranked,
        "risk_tags": risk_tags,
        "scripts": scripts,
        "evidence_ids": list(top.get("evidence", [])),
    }
