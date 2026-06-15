from __future__ import annotations

from typing import Any


RISK_TERMS = ["烂脸", "过敏", "激素", "夸大", "根治", "100%", "刷酸叠加"]


def build_monitoring_report(payload: dict[str, Any]) -> dict[str, Any]:
    competitors = list(payload.get("competitors") or [])
    if not competitors:
        raise ValueError("At least one competitor is required")

    leaderboard = [_build_competitor_row(competitor) for competitor in competitors]
    leaderboard.sort(key=lambda row: row["growth_signal_score"], reverse=True)

    risk_watchlist = _collect_risks(competitors)
    summary = _build_summary(leaderboard, risk_watchlist)

    return {
        "summary": summary,
        "leaderboard": leaderboard,
        "opportunities": _build_opportunities(leaderboard, risk_watchlist),
        "risk_watchlist": risk_watchlist,
        "approval_boundary": {
            "approval_mode": "manual",
            "max_automatic_level": 1,
            "external_actions": [],
            "notes": [
                "Monitoring output is internal analysis only.",
                "Public replies, publishing, ad spend, and brand commitments require approval.",
            ],
        },
        "source_coverage": _build_source_coverage(competitors),
    }


def _build_competitor_row(competitor: dict[str, Any]) -> dict[str, Any]:
    videos = list(competitor.get("videos") or [])
    live_sessions = list(competitor.get("live_sessions") or [])
    video_count = len(videos)
    total_views = sum(_number(video.get("views")) for video in videos)
    total_interactions = sum(
        _number(video.get("likes")) + _number(video.get("comments")) + _number(video.get("shares"))
        for video in videos
    )
    ad_count = sum(1 for video in videos if bool(video.get("is_ad")))
    risk_count = sum(_video_risk_count(video) for video in videos)
    live_hours = sum(_number(session.get("duration_minutes")) for session in live_sessions) / 60
    avg_completion_rate = _average([_number(video.get("completion_rate")) for video in videos])
    avg_engagement_rate = total_interactions / total_views if total_views else 0.0
    ad_ratio = ad_count / video_count if video_count else 0.0

    growth_signal_score = (
        avg_completion_rate * 55
        + avg_engagement_rate * 300
        + min(live_hours, 4) * 4
        + min(ad_ratio, 0.5) * 8
        - risk_count * 4
        - max(ad_ratio - 0.7, 0) * 20
    )

    return {
        "handle": competitor.get("handle", "unknown"),
        "followers": int(_number(competitor.get("followers"))),
        "video_count": video_count,
        "total_views": int(total_views),
        "avg_completion_rate": round(avg_completion_rate, 3),
        "avg_engagement_rate": round(avg_engagement_rate, 4),
        "ad_ratio": round(ad_ratio, 3),
        "live_hours": round(live_hours, 2),
        "risk_count": risk_count,
        "growth_signal_score": round(growth_signal_score, 2),
        "top_topics": _top_topics(videos),
        "source": competitor.get("source", "manual-import"),
    }


def _build_summary(leaderboard: list[dict[str, Any]], risk_watchlist: list[dict[str, Any]]) -> dict[str, Any]:
    video_count = sum(row["video_count"] for row in leaderboard)
    total_views = sum(row["total_views"] for row in leaderboard)
    weighted_completion = sum(
        row["avg_completion_rate"] * row["video_count"] for row in leaderboard
    )
    total_interactions = sum(row["avg_engagement_rate"] * row["total_views"] for row in leaderboard)
    total_ads = sum(row["ad_ratio"] * row["video_count"] for row in leaderboard)

    return {
        "competitor_count": len(leaderboard),
        "video_count": video_count,
        "top_account": leaderboard[0]["handle"],
        "avg_completion_rate": round(weighted_completion / video_count, 3) if video_count else 0.0,
        "avg_engagement_rate": round(total_interactions / total_views, 4) if total_views else 0.0,
        "ad_ratio": round(total_ads / video_count, 3) if video_count else 0.0,
        "live_hours": round(sum(row["live_hours"] for row in leaderboard), 2),
        "risk_count": len(risk_watchlist),
    }


def _build_opportunities(
    leaderboard: list[dict[str, Any]], risk_watchlist: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    top = leaderboard[0]
    opportunities = [
        {
            "action_type": "film",
            "priority": "high",
            "based_on": top["handle"],
            "recommendation": (
                f"围绕{_topic_label(top)}做一条证据框架型短视频，开头直接抛争议，"
                "中段给肤质判断，结尾引导评论区留下产品名和肤质。"
            ),
        }
    ]

    if risk_watchlist:
        opportunities.append(
            {
                "action_type": "comment",
                "priority": "high",
                "based_on": risk_watchlist[0]["account"],
                "recommendation": "把高风险评论先做成答疑选题，不自动公开回复，等人工确认措辞。",
            }
        )

    live_leader = max(leaderboard, key=lambda row: row["live_hours"])
    if live_leader["live_hours"] > 0:
        opportunities.append(
            {
                "action_type": "live",
                "priority": "medium",
                "based_on": live_leader["handle"],
                "recommendation": "复盘对标账号直播主题和时长，优先准备敏感肌、屏障、成分搭配类问答卡片。",
            }
        )

    ad_leader = max(leaderboard, key=lambda row: row["ad_ratio"])
    if ad_leader["ad_ratio"] > 0:
        opportunities.append(
            {
                "action_type": "ad_learning",
                "priority": "medium",
                "based_on": ad_leader["handle"],
                "recommendation": "记录广告密度和内容结构，只生成投流学习笔记，不自动调整千川预算。",
            }
        )

    return opportunities


def _collect_risks(competitors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for competitor in competitors:
        account = competitor.get("handle", "unknown")
        for video in list(competitor.get("videos") or []):
            topic = video.get("topic") or video.get("title") or "unknown"
            for controversy in list(video.get("controversies") or []):
                risks.append(
                    {
                        "account": account,
                        "topic": topic,
                        "level": _risk_level(str(controversy)),
                        "reason": str(controversy),
                        "risk_type": "controversy",
                    }
                )
            for comment in list(video.get("high_risk_comments") or []):
                risks.append(
                    {
                        "account": account,
                        "topic": topic,
                        "level": "high",
                        "reason": str(comment),
                        "risk_type": "comment",
                    }
                )

    level_rank = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda risk: (level_rank.get(risk["level"], 9), risk["account"], risk["topic"]))
    return risks


def _build_source_coverage(competitors: list[dict[str, Any]]) -> dict[str, Any]:
    sources = sorted({str(competitor.get("source", "manual-import")) for competitor in competitors})
    return {
        "source_count": len(sources),
        "sources": sources,
        "freshness": "manual-import",
        "notes": "Replace these local imports with permissioned platform connectors when credentials are approved.",
    }


def _video_risk_count(video: dict[str, Any]) -> int:
    return len(list(video.get("controversies") or [])) + len(list(video.get("high_risk_comments") or []))


def _risk_level(text: str) -> str:
    return "high" if any(term in text for term in RISK_TERMS) else "medium"


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _top_topics(videos: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for video in videos:
        topic = str(video.get("topic") or video.get("title") or "unknown")
        counts[topic] = counts.get(topic, 0) + 1
    return [topic for topic, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:3]]


def _topic_label(row: dict[str, Any]) -> str:
    topics = list(row.get("top_topics") or [])
    return topics[0] if topics else "高互动选题"
