from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record
from venus.persona import build_persona_profile, rewrite_in_persona


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


@dataclass(frozen=True)
class ProductionConfig:
    namespace: str = "venus_production"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus production config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus production namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus production workflow must run in dry-run mode")


def build_video_production_package(
    payload: dict[str, Any],
    config: ProductionConfig | None = None,
) -> dict[str, Any]:
    active_config = config or ProductionConfig()
    safe_payload = _redact(payload)
    topic = str(safe_payload.get("topic") or "护肤选题")
    duration_seconds = max(30, int(_number(safe_payload.get("duration_seconds")) or 45))
    key_points = _key_points(safe_payload)
    broll_assets = [str(item) for item in list(safe_payload.get("broll_assets") or [])]
    profile = build_persona_profile(
        list(safe_payload.get("persona_samples") or ["姐妹们，先看屏障状态，证据和体验都要说清楚。"])
    )

    script_package = _build_script_package(topic, key_points, profile)
    shot_list = _build_shot_list(topic, key_points, broll_assets, duration_seconds)
    subtitle_cards = _build_subtitle_cards(shot_list)
    edit_plan = _build_edit_plan(shot_list)
    publish_package = _build_publish_package(topic, script_package, safe_payload)
    asset_checklist = _build_asset_checklist(broll_assets)
    approval_records = _build_approval_records(
        topic=topic,
        risk_notes=[str(item) for item in list(safe_payload.get("risk_notes") or [])],
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "production",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_content_brief"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run package creates editing instructions and publishing drafts without rendering or uploading video.",
        },
        "summary": {
            "duration_seconds": duration_seconds,
            "scene_count": len(shot_list),
            "subtitle_card_count": len(subtitle_cards),
            "broll_asset_count": len(broll_assets),
            "title_option_count": len(publish_package["title_options"]),
            "approval_gated_action_count": len(approval_records),
        },
        "script_package": script_package,
        "shot_list": shot_list,
        "edit_plan": edit_plan,
        "subtitle_cards": subtitle_cards,
        "asset_checklist": asset_checklist,
        "publish_package": publish_package,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "No video file is rendered, edited, uploaded, scheduled, or published in this slice.",
                "Claim-sensitive wording and final publishing require manual approval.",
                "Future剪映/CapCut/FFmpeg integrations must add source-file checks, export logs, rollback, and publish approval gates.",
            ],
        },
    }


def _build_script_package(topic: str, key_points: list[str], profile: Any) -> dict[str, Any]:
    hook = rewrite_in_persona(f"{topic}，先别急着跟风，30秒看你会不会踩坑。", profile)
    body_segments = [
        {
            "segment_id": f"point-{index}",
            "spoken_line": rewrite_in_persona(point, profile),
            "purpose": purpose,
        }
        for index, (point, purpose) in enumerate(
            zip(key_points, ["risk_filter", "evidence_check", "comment_trigger"]),
            start=1,
        )
    ]
    return {
        "hook": hook,
        "opening": f"今天不制造焦虑，直接用{topic}做自查。",
        "body_segments": body_segments,
        "cta": "想让我帮你看搭配，先把肤质、产品名和使用频率打出来。",
        "comment_prompt": "评论区留下肤质+正在用的搭配，我按屏障、刺激叠加和证据帮你拆。",
        "title_options": [
            topic,
            f"{topic}：敏感肌先看这3点",
            f"别再盲跟{topic}",
        ],
    }


def _build_shot_list(
    topic: str,
    key_points: list[str],
    broll_assets: list[str],
    duration_seconds: int,
) -> list[dict[str, Any]]:
    boundaries = [0, 3, 12, 24, 36, duration_seconds]
    assets = broll_assets or ["口播正面镜头", "手写框架板", "评论区问题截图"]
    scenes = [
        ("hook", "first_three_seconds", f"{topic}先别急着照抄。", "争议词大字贴脸"),
        ("problem_frame", "hold_attention", key_points[0], "屏障状态三选一"),
        ("evidence_check", "build_trust", key_points[1], "成分和备案证据并排"),
        ("decision_framework", "save_value", key_points[2], "自查清单逐条出现"),
        ("comment_cta", "drive_comments", "把肤质和搭配发评论区，我帮你拆风险。", "评论区问题引导"),
    ]
    shot_list = []
    for index, (scene_type, goal, spoken_line, overlay) in enumerate(scenes):
        shot_list.append(
            {
                "scene_id": f"scene-{index + 1}",
                "scene_type": scene_type,
                "start_second": boundaries[index],
                "end_second": boundaries[index + 1],
                "visual": _visual_for_scene(scene_type),
                "spoken_line": spoken_line,
                "overlay_text": overlay,
                "broll_asset": assets[index % len(assets)],
                "retention_goal": goal,
            }
        )
    return shot_list


def _build_edit_plan(shot_list: list[dict[str, Any]]) -> dict[str, Any]:
    timeline = []
    for index, scene in enumerate(shot_list):
        timeline.append(
            {
                "scene_id": scene["scene_id"],
                "start_second": scene["start_second"],
                "end_second": scene["end_second"],
                "cut_style": "jump_cut" if index == 0 else "tight_cut",
                "transition": "none" if index == 0 else "hard_cut",
                "subtitle": scene["overlay_text"],
                "sound_design": "light_hit" if index == 0 else "low_bed",
                "retention_goal": scene["retention_goal"],
            }
        )
    return {
        "format": "9:16",
        "pace": "fast_with_clear_pauses",
        "timeline": timeline,
        "export_notes": "Keep the first 3 seconds visually dense, then use clean subtitles and evidence close-ups.",
    }


def _build_subtitle_cards(shot_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for index, scene in enumerate(shot_list):
        cards.append(
            {
                "scene_id": scene["scene_id"],
                "text": scene["overlay_text"],
                "style": "large_keyword_caption",
                "emphasis": "争议先抛出，别铺垫" if index == 0 else "只保留一句核心判断",
            }
        )
    return cards


def _build_asset_checklist(broll_assets: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "asset": asset,
            "status": "needs_review",
            "usage": "broll_or_evidence_insert",
            "rights_note": "Confirm source, privacy, and claim context before export.",
        }
        for asset in broll_assets
    ]


def _build_publish_package(
    topic: str,
    script_package: dict[str, Any],
    safe_payload: dict[str, Any],
) -> dict[str, Any]:
    hashtags = ["#护肤", "#屏障护理", "#成分党"]
    if "早C晚A" in topic:
        hashtags.insert(0, "#早C晚A")
    return {
        "cover_text": topic,
        "title_options": script_package["title_options"],
        "caption": f"{topic}不是让你跟风，是先看肤质、耐受和证据。{script_package['comment_prompt']}",
        "hashtags": hashtags,
        "pinned_comment_draft": script_package["comment_prompt"],
        "objective": str(safe_payload.get("objective") or "提升完播、评论和关注"),
    }


def _build_approval_records(
    topic: str,
    risk_notes: list[str],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    return [
        create_approval_record(
            action_type="venus_video_claim_review",
            approval_level=2,
            draft="; ".join(risk_notes) or f"Review claim boundaries before exporting {topic}.",
            evidence_ids=[topic],
            reviewer=reviewer,
            created_at=created_at,
        ),
        create_approval_record(
            action_type="venus_video_publish_review",
            approval_level=3,
            draft=f"Review final cut, cover, caption, hashtags, and pinned comment before publishing {topic}.",
            evidence_ids=[topic],
            reviewer=reviewer,
            created_at=created_at,
        ),
    ]


def _key_points(safe_payload: dict[str, Any]) -> list[str]:
    points = [str(item) for item in list(safe_payload.get("key_points") or []) if str(item)]
    defaults = [
        "先判断屏障状态",
        "再看成分刺激叠加",
        "最后给评论区肤质自查问题",
    ]
    return (points + defaults)[:3]


def _visual_for_scene(scene_type: str) -> str:
    visuals = {
        "hook": "正面近景，字幕关键词快速弹出",
        "problem_frame": "手势拆三点，屏幕左侧保留关键词",
        "evidence_check": "成分表、备案或评论截图做局部放大",
        "decision_framework": "清单式画面，一条一条打勾",
        "comment_cta": "回到正面口播，评论样式浮层",
    }
    return visuals[scene_type]


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
