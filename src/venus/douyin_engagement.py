from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval
from venus.comments import analyze_comments
from venus.persona import build_persona_profile, rewrite_in_persona


SECRET_KEYS = {
    "secret",
    "token",
    "password",
    "app_secret",
    "authorization",
    "api_key",
    "auth_token",
    "open_id",
    "union_id",
    "user_id",
}

LIVE_HIGH_RISK_TERMS = [
    "烂脸",
    "过敏",
    "激素",
    "根治",
    "包治",
    "刷酸",
    "爆皮",
    "叠加",
    "孕妇",
]


@dataclass(frozen=True)
class DouyinEngagementConfig:
    namespace: str = "venus_douyin"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus Douyin config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus Douyin namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus Douyin engagement connector must run in dry-run mode")


def build_douyin_engagement_report(
    payload: dict[str, Any],
    config: DouyinEngagementConfig | None = None,
) -> dict[str, Any]:
    active_config = config or DouyinEngagementConfig()
    safe_payload = _redact(payload)
    profile = build_persona_profile(
        list(safe_payload.get("persona_samples") or ["姐妹们，先看屏障状态，证据和体验都要说清楚。"])
    )

    videos = list(safe_payload.get("videos") or [])
    live_sessions = list(safe_payload.get("live_sessions") or [])
    comments = _flatten_video_comments(videos)
    comment_report = analyze_comments(comments, profile) if comments else {"summary": {}, "items": []}
    reply_queue = _build_reply_queue(comment_report, videos)
    live_queue = _build_live_queue(live_sessions, profile)
    approval_records = _build_approval_records(
        reply_queue=reply_queue,
        live_queue=live_queue,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "douyin",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_douyin_export"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "Replace this local import with permissioned Douyin APIs after credentials and approvals are configured.",
        },
        "summary": {
            "video_count": len(videos),
            "comment_count": len(comments),
            "live_session_count": len(live_sessions),
            "live_message_count": sum(len(list(session.get("messages") or [])) for session in live_sessions),
            "high_risk_comment_count": int(comment_report.get("summary", {}).get("high_risk", 0)),
            "high_risk_live_message_count": sum(1 for item in live_queue if item["risk"] == "high"),
            "approval_gated_reply_count": len(approval_records),
        },
        "video_summaries": _build_video_summaries(videos, comment_report),
        "reply_queue": reply_queue,
        "live_queue": live_queue,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "Douyin engagement is read from local/manual exports in this slice.",
                "Comment replies, live replies, pinning, publishing, and user interactions are not executed.",
                "Public replies require approval level 3; live answers are treated as level 4 during dry run.",
            ],
        },
    }


def _flatten_video_comments(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    for video in videos:
        video_id = str(video.get("video_id") or video.get("id") or "unknown-video")
        title = str(video.get("title") or "")
        for comment in list(video.get("comments") or []):
            comment_id = str(comment.get("comment_id") or comment.get("id") or "")
            comments.append(
                {
                    "id": comment_id,
                    "comment_id": comment_id,
                    "video_id": video_id,
                    "video_title": title,
                    "text": str(comment.get("text") or ""),
                    "likes": _number(comment.get("likes")),
                    "created_at": str(comment.get("created_at") or ""),
                }
            )
    return comments


def _build_reply_queue(comment_report: dict[str, Any], videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    titles = {
        str(video.get("video_id") or video.get("id") or "unknown-video"): str(video.get("title") or "")
        for video in videos
    }
    queue = []
    for item in list(comment_report.get("items") or []):
        video_id = str(item.get("video_id") or "")
        approval_level = int(item.get("approval_level") or 1)
        queue.append(
            {
                "action_type": "douyin_comment_reply",
                "comment_id": item.get("comment_id") or item.get("id") or "",
                "video_id": video_id,
                "video_title": titles.get(video_id, item.get("video_title", "")),
                "text": item.get("text", ""),
                "intent": item.get("intent", ""),
                "risk": item.get("risk", ""),
                "approval_level": approval_level,
                "requires_manual_approval": requires_manual_approval(approval_level),
                "execution_state": (
                    "blocked_until_approved"
                    if requires_manual_approval(approval_level)
                    else "ready_for_internal_review"
                ),
                "draft_reply": item.get("draft_reply", ""),
                "external_action_enabled": False,
            }
        )
    return queue


def _build_live_queue(
    live_sessions: list[dict[str, Any]],
    profile: Any,
) -> list[dict[str, Any]]:
    queue = []
    for session in live_sessions:
        session_id = str(session.get("session_id") or session.get("id") or "unknown-live")
        for message in list(session.get("messages") or []):
            text = str(message.get("text") or "")
            risk = "high" if any(term in text for term in LIVE_HIGH_RISK_TERMS) else "medium"
            approval_level = 4 if risk == "high" else 3
            queue.append(
                {
                    "action_type": "douyin_live_reply",
                    "session_id": session_id,
                    "message_id": str(message.get("message_id") or message.get("id") or ""),
                    "text": text,
                    "risk": risk,
                    "approval_level": approval_level,
                    "requires_manual_approval": True,
                    "execution_state": "blocked_until_approved",
                    "draft_reply": rewrite_in_persona(_live_reply_base(text), profile),
                    "external_action_enabled": False,
                }
            )
    return queue


def _build_video_summaries(
    videos: list[dict[str, Any]],
    comment_report: dict[str, Any],
) -> list[dict[str, Any]]:
    items_by_video: dict[str, list[dict[str, Any]]] = {}
    for item in list(comment_report.get("items") or []):
        video_id = str(item.get("video_id") or "")
        items_by_video.setdefault(video_id, []).append(item)

    summaries = []
    for video in videos:
        video_id = str(video.get("video_id") or video.get("id") or "unknown-video")
        items = items_by_video.get(video_id, [])
        summaries.append(
            {
                "video_id": video_id,
                "title": str(video.get("title") or ""),
                "comment_count": len(items),
                "high_risk_comment_count": sum(1 for item in items if item.get("risk") == "high"),
                "approval_gated_reply_count": sum(
                    1 for item in items if int(item.get("approval_level") or 0) >= 2
                ),
                "top_comment_intents": _unique([str(item.get("intent") or "") for item in items]),
            }
        )
    return summaries


def _build_approval_records(
    reply_queue: list[dict[str, Any]],
    live_queue: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    for item in reply_queue + live_queue:
        if not item.get("requires_manual_approval"):
            continue
        records.append(
            create_approval_record(
                action_type=str(item["action_type"]),
                approval_level=int(item["approval_level"]),
                draft=str(item["draft_reply"]),
                evidence_ids=[str(item.get("comment_id") or item.get("message_id") or "")],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _live_reply_base(text: str) -> str:
    if "刷酸" in text or "叠加" in text or "爆皮" in text:
        return "先别叠加，先停刺激组合，观察屏障状态，再看是否需要恢复基础保湿。"
    if "孕妇" in text:
        return "孕期相关问题不要只听直播间一句话，优先看医生建议和产品备案信息。"
    return "这个问题先看肤质、当前状态和正在叠加的产品，不要直接照搬别人方案。"


def _unique(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _number(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
