from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval


SECRET_KEYS = {
    "secret",
    "token",
    "password",
    "app_secret",
    "authorization",
    "api_key",
    "openai_api_key",
    "access_token",
}

DEFAULT_TARGETS = {
    "completion_rate": 0.65,
    "comment_rate": 0.03,
    "follow_rate": 0.008,
    "negative_feedback_rate": 0.015,
}

KPI_DEFINITIONS = {
    "completion_rate": {
        "definition": "Completed views divided by total views for the video.",
        "decision_use": "判断前3秒和剪辑节奏是否真正留住观众。",
    },
    "comment_rate": {
        "definition": "Comments divided by total views for the video.",
        "decision_use": "判断选题和提问是否能激发用户留下肤质、产品和频率信息。",
    },
    "follow_rate": {
        "definition": "New follows attributed to the video divided by total views.",
        "decision_use": "判断内容是否让用户觉得值得持续关注。",
    },
    "share_rate": {
        "definition": "Shares divided by total views for the video.",
        "decision_use": "判断内容是否具备转发给同类肤质朋友的价值。",
    },
    "negative_feedback_rate": {
        "definition": "Dislikes, reports, hides, or negative feedback events divided by total views.",
        "decision_use": "判断内容是否引发误解、争议失控或不适合继续放大。",
    },
    "growth_score": {
        "definition": "Weighted local score using completion, comment, follow, share, and negative feedback rates.",
        "decision_use": "把复盘视频排序，优先学习高留存、高互动、低负反馈的内容结构。",
    },
}


@dataclass(frozen=True)
class PerformanceConfig:
    namespace: str = "venus_performance"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus performance config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus performance namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus performance workflow must run in dry-run mode")


def build_performance_report(
    payload: dict[str, Any],
    config: PerformanceConfig | None = None,
) -> dict[str, Any]:
    active_config = config or PerformanceConfig()
    safe_payload = _redact(payload)
    targets = _targets(dict(safe_payload.get("targets") or {}))
    videos = [dict(item) for item in list(safe_payload.get("videos") or [])]
    video_reviews = [_review_video(video, targets) for video in videos]
    leaderboard = _leaderboard(video_reviews)
    winners = [item for item in video_reviews if item["winner"]]
    underperformers = [item for item in video_reviews if not item["winner"]]
    calibration_rules = _calibration_rules(leaderboard, underperformers, video_reviews)
    next_actions = _next_actions(leaderboard, underperformers)
    evidence_ids = _evidence_ids(video_reviews)
    approval_records = _approval_records(
        safe_payload=safe_payload,
        calibration_rules=calibration_rules,
        next_actions=next_actions,
        evidence_ids=evidence_ids,
        reviewer=active_config.reviewer,
    )

    return {
        "workflow": "performance",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_douyin_video_metrics"),
            "analyzed_at": str(safe_payload.get("analyzed_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run report analyzes local video metrics only and does not read live Douyin data.",
        },
        "summary": {
            "video_count": len(video_reviews),
            "winner_count": len(winners),
            "underperformer_count": len(underperformers),
            "average_completion_rate": _rate_average(video_reviews, "completion_rate"),
            "average_comment_rate": _rate_average(video_reviews, "comment_rate"),
            "average_follow_rate": _rate_average(video_reviews, "follow_rate"),
            "negative_feedback_alert_count": sum(
                1 for item in video_reviews if item["negative_feedback_alert"]
            ),
            "calibration_rule_count": len(calibration_rules),
            "approval_record_count": len(approval_records),
        },
        "targets": targets,
        "leaderboard": leaderboard,
        "video_reviews": video_reviews,
        "winners": winners,
        "underperformers": underperformers,
        "calibration_rules": calibration_rules,
        "next_actions": next_actions,
        "kpi_definitions": KPI_DEFINITIONS,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "Performance calibration proposes learning rules and next-content drafts for review only.",
                "No live Douyin metric read, Feishu send, memory write, publish, reply, ad spend, or platform action is executed.",
                "Live connector enablement and learning-rule adoption remain approval-gated.",
            ],
        },
    }


def _targets(raw_targets: dict[str, Any]) -> dict[str, float]:
    targets = dict(DEFAULT_TARGETS)
    for key in DEFAULT_TARGETS:
        if key in raw_targets:
            targets[key] = _float(raw_targets[key])
    return targets


def _review_video(video: dict[str, Any], targets: dict[str, float]) -> dict[str, Any]:
    completion_rate = _float(video.get("completion_rate"))
    comment_rate = _float(video.get("comment_rate"))
    follow_rate = _float(video.get("follow_rate"))
    share_rate = _float(video.get("share_rate"))
    negative_feedback_rate = _float(video.get("negative_feedback_rate"))
    meets_completion = completion_rate >= targets["completion_rate"]
    meets_comment = comment_rate >= targets["comment_rate"]
    meets_follow = follow_rate >= targets["follow_rate"]
    negative_feedback_alert = negative_feedback_rate > targets["negative_feedback_rate"]
    winner = meets_completion and meets_comment and meets_follow and not negative_feedback_alert

    return {
        "video_id": str(video.get("video_id") or "unknown-video"),
        "title": str(video.get("title") or "untitled"),
        "topic": str(video.get("topic") or "unknown-topic"),
        "published_at": str(video.get("published_at") or "local-time"),
        "views": int(_float(video.get("views"))),
        "completion_rate": completion_rate,
        "comment_rate": comment_rate,
        "follow_rate": follow_rate,
        "share_rate": share_rate,
        "negative_feedback_rate": negative_feedback_rate,
        "growth_score": _growth_score(
            completion_rate=completion_rate,
            comment_rate=comment_rate,
            follow_rate=follow_rate,
            share_rate=share_rate,
            negative_feedback_rate=negative_feedback_rate,
        ),
        "winner": winner,
        "meets_completion_target": meets_completion,
        "meets_comment_target": meets_comment,
        "meets_follow_target": meets_follow,
        "negative_feedback_alert": negative_feedback_alert,
        "content_eval_score": int(_float(video.get("content_eval_score"))),
        "content_eval_status": str(video.get("content_eval_status") or "unknown"),
        "hook_type": str(video.get("hook_type") or "unknown"),
        "cta_type": str(video.get("cta_type") or "unknown"),
        "persona_fit": _float(video.get("persona_fit")),
        "claim_risk": str(video.get("claim_risk") or "unknown"),
        "evidence_ids": [str(item) for item in list(video.get("evidence") or [])],
    }


def _leaderboard(video_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(video_reviews, key=lambda item: item["growth_score"], reverse=True)
    return [
        {
            "rank": index,
            "video_id": item["video_id"],
            "title": item["title"],
            "topic": item["topic"],
            "growth_score": item["growth_score"],
            "winner": item["winner"],
            "completion_rate": item["completion_rate"],
            "comment_rate": item["comment_rate"],
            "follow_rate": item["follow_rate"],
            "share_rate": item["share_rate"],
            "negative_feedback_rate": item["negative_feedback_rate"],
            "hook_type": item["hook_type"],
            "cta_type": item["cta_type"],
            "evidence_ids": item["evidence_ids"],
        }
        for index, item in enumerate(ranked, start=1)
    ]


def _calibration_rules(
    leaderboard: list[dict[str, Any]],
    underperformers: list[dict[str, Any]],
    video_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    top_winner = next((item for item in leaderboard if item["winner"]), None)
    if top_winner:
        rules.append(
            {
                "category": "amplify_winning_hook",
                "priority": "high",
                "rule": f"Repeat {top_winner['hook_type']} hooks around {top_winner['topic']} when evidence and skin-state framing are available.",
                "evidence_ids": list(top_winner["evidence_ids"]),
                "execution_state": "blocked_until_approved",
            }
        )

    generic_underperformers = [
        item for item in underperformers if _is_generic_cta(str(item.get("cta_type") or ""))
    ]
    if generic_underperformers:
        rules.append(
            {
                "category": "repair_generic_cta",
                "priority": "high",
                "rule": "Replace generic CTAs with prompts that ask for skin type, product name, and use frequency.",
                "evidence_ids": _evidence_ids(generic_underperformers),
                "execution_state": "blocked_until_approved",
            }
        )

    claim_risk_items = [
        item
        for item in video_reviews
        if item["content_eval_score"] >= 85
        and item["content_eval_status"] != "ready_for_manual_publish_review"
    ]
    if claim_risk_items:
        rules.append(
            {
                "category": "claim_safety_calibration",
                "priority": "high",
                "rule": "Do not let strong growth scores override claim-safety blockers from pre-publish review.",
                "evidence_ids": _evidence_ids(claim_risk_items),
                "execution_state": "blocked_until_approved",
            }
        )

    return rules


def _next_actions(
    leaderboard: list[dict[str, Any]],
    underperformers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    top_winner = next((item for item in leaderboard if item["winner"]), None)
    if top_winner:
        actions.append(
            _action(
                action_type="draft_next_video_from_winner",
                title="Draft next short video from winning pattern",
                approval_level=2,
                draft=f"Use {top_winner['title']} as the benchmark: keep the hook pattern, preserve evidence framing, and write a sharper follow CTA.",
                evidence_ids=list(top_winner["evidence_ids"]),
            )
        )

    if underperformers:
        weakest = sorted(underperformers, key=lambda item: item["growth_score"])[0]
        actions.append(
            _action(
                action_type="revise_underperforming_cta",
                title="Revise underperforming CTA and opening",
                approval_level=2,
                draft=f"Revise {weakest['title']} before repeating this topic: strengthen the first 3 seconds and replace generic CTA wording.",
                evidence_ids=list(weakest["evidence_ids"]),
            )
        )
    return actions


def _action(
    action_type: str,
    title: str,
    approval_level: int,
    draft: str,
    evidence_ids: list[str],
) -> dict[str, Any]:
    manual = requires_manual_approval(approval_level)
    return {
        "action_type": action_type,
        "title": title,
        "approval_level": approval_level,
        "requires_manual_approval": manual,
        "execution_state": "blocked_until_approved" if manual else "ready_for_internal_review",
        "draft": draft,
        "evidence_ids": evidence_ids,
        "external_action_enabled": False,
    }


def _approval_records(
    safe_payload: dict[str, Any],
    calibration_rules: list[dict[str, Any]],
    next_actions: list[dict[str, Any]],
    evidence_ids: list[str],
    reviewer: str,
) -> list[dict[str, Any]]:
    records = []
    created_at = str(safe_payload.get("analyzed_at") or "local-time")
    if calibration_rules:
        records.append(
            create_approval_record(
                action_type="venus_performance_learning_review",
                approval_level=2,
                draft="Review performance calibration rules before updating Venus memory, persona rules, or content strategy.",
                evidence_ids=evidence_ids,
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    if bool(safe_payload.get("live_metrics_requested")) or next_actions:
        records.append(
            create_approval_record(
                action_type="venus_performance_next_content_review",
                approval_level=2,
                draft="Review next-video actions from the performance report before drafting, editing, publishing, or promoting content.",
                evidence_ids=evidence_ids,
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _growth_score(
    completion_rate: float,
    comment_rate: float,
    follow_rate: float,
    share_rate: float,
    negative_feedback_rate: float,
) -> float:
    return round(
        completion_rate * 40
        + comment_rate * 300
        + follow_rate * 500
        + share_rate * 100
        - negative_feedback_rate * 200,
        1,
    )


def _rate_average(items: list[dict[str, Any]], key: str) -> float:
    if not items:
        return 0.0
    return round(sum(_float(item.get(key)) for item in items) / len(items), 3)


def _evidence_ids(items: list[dict[str, Any]]) -> list[str]:
    evidence_ids: list[str] = []
    for item in items:
        evidence_ids.extend(str(evidence) for evidence in list(item.get("evidence_ids") or []))
    return sorted(set(evidence_ids))


def _is_generic_cta(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "generic", "none", "了解了吧", "看懂了吗"}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
