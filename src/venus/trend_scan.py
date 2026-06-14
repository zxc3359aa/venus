from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record


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

COVERAGE_TARGETS = [
    "topics",
    "products",
    "creators",
    "comments",
    "ingredients",
    "tags",
    "controversies",
]

SIGNAL_SOURCES = {
    "topics": "topic",
    "products": "product",
    "creators": "creator",
    "comments": "comment",
    "ingredients": "ingredient",
    "tags": "tag",
    "controversies": "controversy",
}


@dataclass(frozen=True)
class TrendScanConfig:
    namespace: str = "venus_trend_scan"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus trend scan config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus trend scan namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus trend scan must run in dry-run mode")


def build_trend_scan_report(
    payload: dict[str, Any],
    config: TrendScanConfig | None = None,
) -> dict[str, Any]:
    active_config = config or TrendScanConfig()
    safe_payload = _redact(payload)
    refresh_interval = int(_number(safe_payload.get("refresh_interval_minutes")) or 30)
    normalized_signals = _normalize_signals(safe_payload)
    leaderboard = _build_leaderboard(normalized_signals)
    trend_clusters = _build_trend_clusters(safe_payload, leaderboard)
    content_opportunities = _build_content_opportunities(leaderboard[:3], trend_clusters)
    watch_plan = _build_watch_plan(safe_payload, refresh_interval)
    approval_records = _build_approval_records(
        safe_payload=safe_payload,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "trend_scan",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_douyin_beauty_scan"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run trend scan normalizes local/imported Douyin beauty signals without live platform reads.",
        },
        "summary": {
            "signal_count": len(normalized_signals),
            "hot_topic_count": len(list(safe_payload.get("topics") or [])),
            "hot_product_count": len(list(safe_payload.get("products") or [])),
            "hot_creator_count": len(list(safe_payload.get("creators") or [])),
            "hot_comment_count": len(list(safe_payload.get("comments") or [])),
            "hot_ingredient_count": len(list(safe_payload.get("ingredients") or [])),
            "hot_tag_count": len(list(safe_payload.get("tags") or [])),
            "controversy_count": len(list(safe_payload.get("controversies") or [])),
            "content_opportunity_count": len(content_opportunities),
            "refresh_interval_minutes": refresh_interval,
            "approval_gated_action_count": len(approval_records),
        },
        "normalized_signals": normalized_signals,
        "leaderboard": leaderboard,
        "trend_clusters": trend_clusters,
        "content_opportunities": content_opportunities,
        "watch_plan": watch_plan,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No live Douyin search, scrape, login, API call, or browser automation is executed in this slice.",
                "Live all-day scanning requires connector approval, credentials, rate limits, source logs, and privacy review.",
                "Trend outputs are internal analysis and script-planning inputs until publishing is approved separately.",
            ],
        },
    }


def _normalize_signals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    signals = []
    for source_key, signal_type in SIGNAL_SOURCES.items():
        for index, item in enumerate(list(payload.get(source_key) or []), start=1):
            label = _label_for(signal_type, item)
            growth = _number(item.get("growth"))
            controversy = _number(item.get("controversy"))
            volume = _volume_for(signal_type, item)
            score = _score_signal(volume, growth, controversy)
            signals.append(
                {
                    "signal_id": str(item.get("id") or f"{signal_type}-{index:03d}"),
                    "signal_type": signal_type,
                    "label": label,
                    "volume": volume,
                    "growth": growth,
                    "controversy": controversy,
                    "score": score,
                    "priority": _priority(score, controversy),
                    "evidence_ids": [str(evidence) for evidence in list(item.get("evidence") or [])],
                    "source_bucket": source_key,
                }
            )
    return sorted(signals, key=lambda signal: signal["score"], reverse=True)


def _build_leaderboard(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": index,
            "signal_id": signal["signal_id"],
            "signal_type": signal["signal_type"],
            "label": signal["label"],
            "score": signal["score"],
            "priority": signal["priority"],
            "growth": signal["growth"],
            "controversy": signal["controversy"],
        }
        for index, signal in enumerate(signals, start=1)
    ]


def _build_trend_clusters(payload: dict[str, Any], leaderboard: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not leaderboard:
        return []
    primary = leaderboard[0]
    return [
        {
            "cluster_id": "cluster-001",
            "primary_topic": primary["label"],
            "priority": primary["priority"],
            "related_products": [_label_for("product", item) for item in list(payload.get("products") or [])],
            "related_creators": [_label_for("creator", item) for item in list(payload.get("creators") or [])],
            "related_comments": [_label_for("comment", item) for item in list(payload.get("comments") or [])],
            "related_ingredients": [_label_for("ingredient", item) for item in list(payload.get("ingredients") or [])],
            "related_tags": [_label_for("tag", item) for item in list(payload.get("tags") or [])],
            "controversies": [_label_for("controversy", item) for item in list(payload.get("controversies") or [])],
            "analysis": f"{primary['label']}具备高热度和争议度，适合用证据、肤质分层和评论互动切入。",
        }
    ]


def _build_content_opportunities(
    top_signals: list[dict[str, Any]],
    trend_clusters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cluster = trend_clusters[0] if trend_clusters else {}
    opportunities = []
    for signal in top_signals:
        label = str(signal["label"])
        opportunities.append(
            {
                "opportunity_id": f"opp-{signal['rank']:03d}",
                "source_signal_id": signal["signal_id"],
                "angle": _angle_for_signal(str(signal["signal_type"]), label),
                "hook": f"{label}别急着跟风，先看屏障、证据和刺激叠加。",
                "filming_advice": "开头直接抛争议，中段放证据或成分特写，结尾引导用户留下肤质和产品名。",
                "comment_prompt": "评论区留下肤质+正在用的产品，我按屏障状态和成分叠加帮你拆。",
                "completion_levers": [
                    "前3秒争议词贴脸",
                    "中段用三点判断框架降低跳出",
                    "结尾给具体评论格式提升互动",
                ],
                "related_cluster": str(cluster.get("cluster_id") or "cluster-001"),
            }
        )
    return opportunities


def _build_watch_plan(payload: dict[str, Any], refresh_interval: int) -> dict[str, Any]:
    missing = [target for target in COVERAGE_TARGETS if not list(payload.get(target) or [])]
    live_requested = bool(payload.get("live_connector_requested"))
    return {
        "refresh_interval_minutes": refresh_interval,
        "coverage_targets": COVERAGE_TARGETS,
        "gap_alerts": [f"Missing Douyin {target} signals in latest import." for target in missing],
        "live_connector_requested": live_requested,
        "live_connector_state": "blocked_until_approved" if live_requested else "not_requested",
        "next_scan_mode": "manual_import_until_live_connector_is_approved",
        "storage_namespace": "venus_trend_scan",
    }


def _build_approval_records(
    safe_payload: dict[str, Any],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    if not bool(safe_payload.get("live_connector_requested")):
        return []
    return [
        create_approval_record(
            action_type="venus_live_trend_scan_connector",
            approval_level=2,
            draft="Enable all-day Douyin beauty/skincare trend scanning only after credential, rate-limit, privacy, and logging review.",
            evidence_ids=[str(safe_payload.get("source") or "manual_douyin_beauty_scan")],
            reviewer=reviewer,
            created_at=created_at,
        )
    ]


def _label_for(signal_type: str, item: dict[str, Any]) -> str:
    if signal_type == "creator":
        return str(item.get("handle") or item.get("label") or "unknown_creator")
    if signal_type == "comment":
        return str(item.get("text") or item.get("label") or "unknown_comment")
    return str(item.get("label") or item.get("name") or item.get("topic") or "unknown_signal")


def _volume_for(signal_type: str, item: dict[str, Any]) -> float:
    if signal_type == "comment":
        return _number(item.get("mentions") or item.get("likes"))
    return _number(item.get("mentions") or item.get("views") or item.get("likes"))


def _score_signal(volume: float, growth: float, controversy: float) -> float:
    return round(min(volume / 1000, 400) + growth * 100 + controversy * 80, 2)


def _priority(score: float, controversy: float) -> str:
    if score >= 400 or controversy >= 0.9:
        return "urgent"
    if score >= 240 or controversy >= 0.7:
        return "high"
    if score >= 120:
        return "medium"
    return "low"


def _angle_for_signal(signal_type: str, label: str) -> str:
    if signal_type == "product":
        return f"把{label}拆成备案、成分、争议和适合人群四段。"
    if signal_type == "creator":
        return f"复盘{label}爆款结构，但用自己的屏障护理判断框架表达。"
    if signal_type == "comment":
        return f"用高赞评论“{label}”做开头，回答真实顾虑。"
    if signal_type == "ingredient":
        return f"围绕{label}讲清适用肤质、叠加禁忌和耐受边界。"
    if signal_type == "tag":
        return f"借{label}标签热度做自查型短视频。"
    if signal_type == "controversy":
        return f"先承认{label}争议，再给证据和避坑清单。"
    return f"围绕{label}做争议切入和证据型内容。"


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


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
