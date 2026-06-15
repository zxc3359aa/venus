"""M4 评论/弹幕洞察与回复草稿模块（规格 §8 M4）。

本模块只处理已经由官方/授权渠道进入系统的本账号评论快照，做离线洞察、
合规回复草稿和人工发送建议。不调用平台接口，不自动发送评论或弹幕。
"""
from __future__ import annotations

from typing import Any

from venus.contracts import Action, DataClass, Tagged

_BANNED_REPLY_WORDS = ["根治", "治愈", "100%", "最有效", "第一", "包好"]
_MEDICAL_CLAIM_WORDS = ["诊断", "处方", "治疗"]


def build_m4_community_report(source: Tagged) -> Tagged:
    """构建 M4 评论洞察与回复草稿报告。

    C3 私域 PII 不进入本模块；生产接入时评论作者标识应先做哈希/脱敏。
    """
    if source.data_class == DataClass.C3_SECRET or source.pii:
        raise ValueError("M4 community report rejects C3/PII inputs; comments must be redacted or hashed first")

    payload = dict(source.payload or {})
    video_id = str(payload.get("video_id") or "unknown-video")
    persona_descriptor = str(payload.get("persona_descriptor") or "先问肤质和频率，再给证据化建议。")
    comments = [_normalize_comment(item) for item in list(payload.get("comments") or [])]
    intent_rows = [_classify_comment(item) for item in comments]
    top_intents = _top_intents(intent_rows)
    reply_drafts = [
        _reply_draft(video_id, comment, intent, persona_descriptor)
        for comment, intent in zip(comments, intent_rows)
        if intent["reply_worthy"]
    ]

    live_mode = bool(payload.get("live_mode"))
    requested_auto_send = bool(payload.get("auto_send_barrage"))

    return Tagged(
        payload={
            "module": "m4_community",
            "video_id": video_id,
            "comment_insights": {
                "total_comments": len(comments),
                "top_intents": top_intents,
                "high_attention_comments": _high_attention_comments(comments, intent_rows),
                "map_reduce_ready": True,
            },
            "reply_drafts": reply_drafts,
            "live_assist": {
                "enabled": live_mode,
                "mode": "summary_and_suggested_talk_track",
                "suggested_talk_tracks": _talk_tracks(top_intents),
                "auto_send_requested": requested_auto_send,
                "auto_send_blocked": live_mode and requested_auto_send,
                "tier_c_blocked": True,
            },
            "external_actions": [],
            "safety_boundary": {
                "data_source_tier": "tier_a_official_self_account_only",
                "reply_requires_approval": True,
                "reply_idempotency_required": True,
                "rate_limit": "platform_endpoint_token_bucket_required",
                "medical_boundary": "不做医疗诊断，不承诺治疗效果，只给护肤使用边界与就医提醒",
                "barrage_boundary": "直播弹幕默认只给实时摘要和建议话术，不做非官方自动发送",
                "tier_c_blocked": True,
            },
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def validate_reply_draft(text: str) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        issues.append("回复为空")
    for word in _BANNED_REPLY_WORDS:
        if word in text:
            issues.append(f"违规或高风险词: {word}")
    for word in _MEDICAL_CLAIM_WORDS:
        if word in text:
            issues.append(f"医疗化表达风险: {word}")
    if "关注我" in text:
        issues.append("评论回复不应强行引导关注")
    return issues


def build_reply_action(*, video_id: str, comment_id: str, draft: str) -> Action:
    issues = validate_reply_draft(draft)
    if issues:
        raise ValueError("reply draft failed validation: " + "; ".join(issues))
    return Action(
        kind="reply_comment",
        summary=f"回复视频 {video_id} 下评论 {comment_id}",
        payload={"video_id": video_id, "comment_id": comment_id, "draft": draft},
        idempotency_key=f"reply-{video_id}-{comment_id}",
        data_class=DataClass.C1_INTERNAL,
        reversible=False,
    )


def _normalize_comment(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw.get("id") or raw.get("comment_id") or "unknown-comment"),
        "text": _sanitize_comment_text(str(raw.get("text") or raw.get("content") or "")),
        "like_count": int(_number(raw.get("like_count"), default=0)),
        "author_hash": str(raw.get("author_hash") or "redacted-author"),
    }


def _classify_comment(comment: dict[str, Any]) -> dict[str, Any]:
    text = comment["text"]
    intent = "general_question"
    if any(token in text for token in ["刺痛", "敏感", "泛红", "过敏", "烂脸"]):
        intent = "safety_reaction"
    elif any(token in text for token in ["成分", "视黄醇", "酸", "早C晚A", "叠加"]):
        intent = "ingredient_pairing"
    elif any(token in text for token in ["闭口", "痘", "美白", "淡斑"]):
        intent = "efficacy_expectation"
    return {
        "comment_id": comment["id"],
        "intent": intent,
        "weight": max(1, comment["like_count"]),
        "reply_worthy": bool(text),
    }


def _top_intents(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = totals.setdefault(row["intent"], {"intent": row["intent"], "count": 0, "weight": 0})
        bucket["count"] += 1
        bucket["weight"] += row["weight"]
    ranked = list(totals.values())
    ranked.sort(key=lambda item: (item["weight"], item["count"], item["intent"]), reverse=True)
    return ranked


def _high_attention_comments(comments: list[dict[str, Any]], intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "comment_id": comment["id"],
            "intent": intent["intent"],
            "like_count": comment["like_count"],
            "summary": comment["text"][:80],
        }
        for comment, intent in zip(comments, intents)
    ]
    rows.sort(key=lambda item: item["like_count"], reverse=True)
    return rows[:8]


def _reply_draft(
    video_id: str,
    comment: dict[str, Any],
    intent: dict[str, Any],
    persona_descriptor: str,
) -> dict[str, Any]:
    draft = _draft_text(intent["intent"], persona_descriptor)
    return {
        "comment_id": comment["id"],
        "intent": intent["intent"],
        "draft": draft,
        "validation_issues": validate_reply_draft(draft),
        "approval_required": True,
        "idempotency_key": f"reply-{video_id}-{comment['id']}",
    }


def _draft_text(intent: str, persona_descriptor: str) -> str:
    prefix = persona_descriptor.rstrip("。") + "。"
    if intent == "safety_reaction":
        return prefix + "先暂停叠加，告诉我肤质、频率和具体产品，我按屏障状态帮你拆；如果持续红肿疼痛，先线下咨询专业医生。"
    if intent == "ingredient_pairing":
        return prefix + "先别急着叠加，把成分表和使用时间发清楚，我帮你看刺激叠加和使用顺序。"
    if intent == "efficacy_expectation":
        return prefix + "不要按绝对效果期待来选，先看成分证据、浓度位置和你的耐受，再决定要不要用。"
    return prefix + "把肤质、产品名和使用频率补充一下，我按证据和使用边界帮你拆。"


def _talk_tracks(top_intents: list[dict[str, Any]]) -> list[str]:
    if not top_intents:
        return ["先收集问题，按肤质、产品名、使用频率三类整理后再回答。"]
    tracks = []
    for item in top_intents[:3]:
        if item["intent"] == "safety_reaction":
            tracks.append("敏感刺痛问题先提醒暂停叠加，再问肤质、频率和产品组合。")
        elif item["intent"] == "ingredient_pairing":
            tracks.append("成分叠加问题先讲使用顺序和耐受边界，避免绝对化结论。")
        elif item["intent"] == "efficacy_expectation":
            tracks.append("功效期待问题先降温绝对承诺，回到证据、浓度和肤质差异。")
        else:
            tracks.append("一般问题先补齐肤质、产品名和使用频率，再给建议。")
    return tracks


def _sanitize_comment_text(text: str) -> str:
    # 输入应已脱敏；这里兜底去掉长数字，避免测试/日志暴露可识别信息。
    sanitized = "".join("[数字]" if char.isdigit() else char for char in text)
    return sanitized.strip()


def _number(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
