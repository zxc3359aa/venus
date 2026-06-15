"""M8 24h 对标达人盯盘离线分析包。

本模块只处理已由官方数据产品或持牌第三方进入系统的对标快照；
不连接抖音、不采集竞品页面、不处理个人隐私。
"""
from __future__ import annotations

from typing import Any

from venus.contracts import DataClass, Tagged


ALLOWED_TIERS = {"A", "B", "tier_a_official_products", "tier_b_licensed_provider"}
DEFAMATION_RISK_TERMS = ("造假", "骗子", "黑心", "违法", "垃圾", "劣质")


def build_m8_benchmark_report(source: Tagged) -> Tagged:
    """生成对标达人矩阵、趋势/分位/直播/广告分析与异动告警。"""
    _reject_private_payload(source)
    payload = source.payload if isinstance(source.payload, dict) else {}
    data_source = _validate_source(payload.get("data_source") or {})
    creators = [_normalize_creator(item) for item in list(payload.get("creators") or [])]
    matrix = _build_matrix(creators)
    alerts = _build_anomaly_alerts(matrix)

    return Tagged(
        payload={
            "module": "m8_benchmark",
            "source_boundary": {
                "primary_source": data_source["name"],
                "source_tier": data_source["tier"],
                "allowed_tiers": ["tier_a_official_products", "tier_b_licensed_provider"],
                "tier_c_blocked": True,
                "privacy_boundary": "只处理聚合后的公开/授权指标，不抓个人隐私或未授权页面。",
            },
            "provider_switching": {
                "primary": data_source["name"],
                "fallbacks": list(payload.get("fallback_sources") or []),
                "portable_provider_contract": "DataSourceProvider.fetch_creator/search_hotspots",
            },
            "polling_policy": _polling_policy(payload.get("polling") or {}, alerts),
            "benchmark_matrix": {
                "method": "percentile_trend_baseline_comparison",
                "creators": matrix,
            },
            "anomaly_alerts": alerts,
            "recommendations": _recommendations(matrix, alerts),
            "timeseries_sink": _timeseries_sink(matrix),
            "official_api_status": "no_platform_or_datasource_calls_pending_context7_and_authorization",
            "external_actions": [],
            "safety_boundary": {
                "commentary_policy": "只做指标对比和策略建议，不诽谤、不臆测动机、不抓个人隐私。",
                "data_source_policy": "仅允许 Tier A 官方数据产品或 Tier B 持牌/授权数据源。",
                "metric_storage": "对标时序指标写入 venus_metric_timeseries，避免实体行膨胀。",
            },
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def validate_benchmark_commentary(text: str) -> list[str]:
    """校验对标建议是否含诽谤或未经证实的攻击性表达。"""
    issues: list[str] = []
    if not text.strip():
        issues.append("对标建议为空")
    for term in DEFAMATION_RISK_TERMS:
        if term in text:
            issues.append(f"对标建议含诽谤或攻击风险词：{term}")
    if "数据来源" not in text and "授权数据" not in text and "指标" not in text:
        issues.append("对标建议需要回到指标或授权数据")
    return issues


def _reject_private_payload(source: Tagged) -> None:
    if source.data_class == DataClass.C3_SECRET or source.pii:
        raise ValueError("M8 不接收 C3/PII；对标分析只使用公开或授权的聚合 C0/C1 指标。")


def _validate_source(raw: dict[str, Any]) -> dict[str, Any]:
    name = str(raw.get("name") or "unknown-authorized-source")
    tier = str(raw.get("tier") or "").strip()
    authorized = bool(raw.get("authorized", True))
    if tier.upper() == "C" or tier == "Tier C":
        raise ValueError("Tier C 数据源被禁止；请切换到官方数据产品或持牌授权数据源。")
    if tier not in ALLOWED_TIERS and tier.upper() not in ALLOWED_TIERS:
        raise ValueError("M8 数据源必须是 Tier A 官方产品或 Tier B 持牌授权来源。")
    if not authorized:
        raise ValueError("M8 数据源缺少授权标记。")
    normalized_tier = "tier_a_official_products" if tier.upper() == "A" else "tier_b_licensed_provider"
    return {"name": name, "tier": normalized_tier}


def _normalize_creator(raw: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(raw.get("metrics") or {})
    previous = dict(raw.get("previous_metrics") or {})
    videos = [dict(item) for item in list(raw.get("videos") or [])]
    live = dict(raw.get("live") or {})
    return {
        "creator_id": str(raw.get("creator_id") or raw.get("id") or "unknown-creator"),
        "handle": str(raw.get("handle") or raw.get("name") or "unknown-handle"),
        "style_tags": [str(item) for item in list(raw.get("style_tags") or [])],
        "metrics": {
            "engagement_rate": _float(metrics.get("engagement_rate")),
            "avg_views": _float(metrics.get("avg_views")),
            "ad_post_ratio": _float(metrics.get("ad_post_ratio")),
        },
        "previous_metrics": {
            "engagement_rate": _float(previous.get("engagement_rate")),
            "avg_views": _float(previous.get("avg_views")),
        },
        "videos": videos,
        "live": {
            "sessions": int(_float(live.get("sessions"))),
            "avg_gpm": _float(live.get("avg_gpm")),
            "peak_online": int(_float(live.get("peak_online"))),
        },
    }


def _build_matrix(creators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    engagement_values = [creator["metrics"]["engagement_rate"] for creator in creators]
    view_values = [creator["metrics"]["avg_views"] for creator in creators]
    rows = []
    for creator in creators:
        video = _video_analysis(creator["videos"])
        ad = _ad_analysis(creator["videos"], creator["metrics"]["ad_post_ratio"])
        live = _live_analysis(creator["live"])
        current = creator["metrics"]
        previous = creator["previous_metrics"]
        rows.append(
            {
                "creator_id": creator["creator_id"],
                "handle": creator["handle"],
                "engagement_rate": round(current["engagement_rate"], 4),
                "avg_views": round(current["avg_views"], 2),
                "engagement_percentile": _percentile(current["engagement_rate"], engagement_values),
                "view_percentile": _percentile(current["avg_views"], view_values),
                "trend": _trend(current, previous),
                "baseline_delta": {
                    "engagement_rate": round(current["engagement_rate"] - previous["engagement_rate"], 4),
                    "avg_views": round(current["avg_views"] - previous["avg_views"], 2),
                },
                "style_analysis": {"tags": creator["style_tags"], "signature": _style_signature(creator["style_tags"])},
                "video_analysis": video,
                "ad_analysis": ad,
                "live_analysis": live,
            }
        )
    rows.sort(key=lambda item: (item["engagement_percentile"], item["view_percentile"], item["creator_id"]), reverse=True)
    return rows


def _video_analysis(videos: list[dict[str, Any]]) -> dict[str, Any]:
    views = [_float(video.get("views")) for video in videos]
    completion = [_float(video.get("completion_rate")) for video in videos]
    return {
        "video_count": len(videos),
        "avg_video_views": round(sum(views) / len(views), 2) if views else 0.0,
        "avg_completion_rate": round(sum(completion) / len(completion), 4) if completion else 0.0,
        "top_video_id": str(max(videos, key=lambda item: _float(item.get("views"))).get("id")) if videos else None,
    }


def _ad_analysis(videos: list[dict[str, Any]], ad_post_ratio: float) -> dict[str, Any]:
    ad_count = sum(1 for video in videos if bool(video.get("ad")))
    return {
        "ad_post_count": ad_count,
        "ad_post_ratio": round(ad_post_ratio, 4),
        "ad_load_level": "high" if ad_post_ratio >= 0.6 else "normal",
    }


def _live_analysis(live: dict[str, Any]) -> dict[str, Any]:
    return {
        "sessions": int(live["sessions"]),
        "avg_gpm": round(float(live["avg_gpm"]), 2),
        "peak_online": int(live["peak_online"]),
        "live_strength": "strong" if live["sessions"] >= 3 and live["avg_gpm"] >= 5000 else "watch",
    }


def _build_anomaly_alerts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for row in rows:
        previous_views = row["avg_views"] - row["baseline_delta"]["avg_views"]
        if previous_views > 0 and row["avg_views"] / previous_views >= 1.8:
            alerts.append(
                {
                    "creator_id": row["creator_id"],
                    "kind": "view_velocity_spike",
                    "severity": "high",
                    "summary": f"{row['handle']} 授权指标显示均播播放显著上升，建议拆解选题与开场结构。",
                    "requires_review": True,
                }
            )
        if row["ad_analysis"]["ad_post_ratio"] >= 0.6:
            alerts.append(
                {
                    "creator_id": row["creator_id"],
                    "kind": "ad_load_risk",
                    "severity": "medium",
                    "summary": f"{row['handle']} 广告占比偏高，建议观察互动承压与评论反馈。",
                    "requires_review": True,
                }
            )
        if row["live_analysis"]["live_strength"] == "strong":
            alerts.append(
                {
                    "creator_id": row["creator_id"],
                    "kind": "live_strength_signal",
                    "severity": "medium",
                    "summary": f"{row['handle']} 直播 GPM 与在线峰值值得拆解。",
                    "requires_review": True,
                }
            )
    return alerts


def _recommendations(rows: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["授权数据源暂无对标样本，先补齐达人清单、时序指标和直播字段。"]
    leader = rows[0]
    recs = [
        (
            f"基于授权指标，优先拆解 {leader['handle']} 的高分位内容结构："
            f"互动分位 {leader['engagement_percentile']:.1f}、播放分位 {leader['view_percentile']:.1f}，"
            "提炼开场钩子、证据表达和评论触发点。"
        )
    ]
    if alerts:
        recs.append("异动告警先做人工复核，再转为选题实验；只引用指标变化，不评价达人动机。")
    recs.append("广告占比、直播 GPM、完播率和风格标签分开建模，避免把商业密度误判为内容能力。")
    return recs


def _timeseries_sink(rows: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for row in rows:
        for metric in ("engagement_rate", "avg_views"):
            records.append(
                {
                    "table": "venus_metric_timeseries",
                    "entity_type": "benchmark_creator",
                    "entity_id": row["creator_id"],
                    "metric": metric,
                    "value": row[metric],
                    "data_class": "C1_INTERNAL",
                }
            )
    return {
        "table": "venus_metric_timeseries",
        "records": records,
        "large_volume_upgrade": "clickhouse_when_metric_timeseries_grows",
    }


def _polling_policy(raw: dict[str, Any], alerts: list[dict[str, Any]]) -> dict[str, Any]:
    base = int(_float(raw.get("base_interval_minutes"), default=360))
    burst = int(_float(raw.get("burst_interval_minutes"), default=60))
    return {
        "mode": "near_real_time_configurable",
        "base_interval_minutes": max(60, base),
        "burst_interval_minutes": max(15, burst),
        "burst_enabled": bool(alerts),
        "default_frequency": "multiple_times_daily",
    }


def _percentile(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    below_or_equal = sum(1 for item in values if item <= value)
    return round(below_or_equal / len(values) * 100, 2)


def _trend(current: dict[str, float], previous: dict[str, float]) -> str:
    current_score = current["avg_views"] * max(current["engagement_rate"], 0.0001)
    previous_score = previous["avg_views"] * max(previous["engagement_rate"], 0.0001)
    if previous_score <= 0:
        return "new"
    change = (current_score - previous_score) / previous_score
    if change >= 0.15:
        return "rising"
    if change <= -0.15:
        return "declining"
    return "stable"


def _style_signature(tags: list[str]) -> str:
    if not tags:
        return "unknown_style"
    return "+".join(tags[:4])


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
