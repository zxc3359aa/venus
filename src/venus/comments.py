from __future__ import annotations

from typing import Any

from venus.persona import PersonaProfile, rewrite_in_persona


HIGH_RISK_TERMS = ["烂脸", "过敏", "激素", "100%", "根治", "包治", "修复屏障"]


def analyze_comments(comments: list[dict[str, Any]], profile: PersonaProfile) -> dict[str, Any]:
    items = []
    for comment in comments:
        text = str(comment.get("text", ""))
        risk = "high" if any(term in text for term in HIGH_RISK_TERMS) else "medium"
        approval_level = 3 if risk == "high" else 1
        intent = _classify_intent(text)
        draft = rewrite_in_persona(_base_reply(intent), profile)
        items.append(
            {
                "id": comment.get("id"),
                "comment_id": comment.get("comment_id") or comment.get("id"),
                "video_id": comment.get("video_id"),
                "video_title": comment.get("video_title"),
                "text": text,
                "likes": comment.get("likes"),
                "created_at": comment.get("created_at"),
                "intent": intent,
                "risk": risk,
                "approval_level": approval_level,
                "draft_reply": draft,
            }
        )

    return {
        "summary": {
            "total": len(items),
            "high_risk": sum(1 for item in items if item["risk"] == "high"),
            "approval_gated": sum(1 for item in items if item["approval_level"] >= 2),
        },
        "items": items,
    }


def _classify_intent(text: str) -> str:
    if "会不会" in text or "是不是" in text:
        return "risk_question"
    if "平价" in text or "替代" in text:
        return "shopping_advice"
    return "general_comment"


def _base_reply(intent: str) -> str:
    if intent == "risk_question":
        return "这个问题不能一刀切，要看肤质、屏障状态、使用频率和搭配。"
    if intent == "shopping_advice":
        return "先看你要解决的核心问题，再看预算和耐受，不要只看热门。"
    return "我会先看证据，再结合使用场景判断。"
