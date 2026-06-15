"""M5 文案输出 + 基础视频剪辑模块（规格 §8 M5）。

当前切片生成离线、可编辑的剪辑工程描述，不调用 FFmpeg、剪映或发布平台。
真实渲染/导出/发布后续必须接授权、审批和幂等链路。
"""
from __future__ import annotations

from typing import Any

from venus.contracts import Action, DataClass, Tagged

_ASSET_TYPES_REQUIRING_AUTH = {"video", "image", "music", "font", "voice", "avatar"}


def build_m5_video_package(source: Tagged) -> Tagged:
    """把脚本和已授权素材编排成可编辑工程包。"""
    if source.data_class == DataClass.C3_SECRET or source.pii:
        raise ValueError("M5 video editing rejects C3/PII inputs; use C1 persona descriptors only")

    payload = dict(source.payload or {})
    script = _normalize_script(payload.get("script") or {})
    assets = [dict(item) for item in list(payload.get("assets") or [])]
    authorization = validate_asset_authorizations(assets)
    if authorization["status"] != "passed":
        raise ValueError("素材授权门禁未通过: " + ", ".join(item["id"] for item in authorization["blocked_assets"]))

    timeline = _timeline(script, assets)
    project_id = _project_id(script)
    editable_project = {
        "id": project_id,
        "format": "venus_edit_decision_list",
        "version": 1,
        "tracks": ["video", "caption", "audio", "overlay"],
        "timeline": timeline,
        "assets": assets,
        "roundtrip_editable": True,
    }

    return Tagged(
        payload={
            "module": "m5_video_editing",
            "project_id": project_id,
            "script": script,
            "editable_project": editable_project,
            "timeline": timeline,
            "caption_track": _caption_track(timeline["shots"]),
            "cover_suggestions": _cover_suggestions(script),
            "title_suggestions": _title_suggestions(script),
            "tag_suggestions": _tag_suggestions(script),
            "authorization_gate": authorization,
            "export_status": "draft_only_requires_human_review_before_render_or_publish",
            "external_actions": [],
            "safety_boundary": {
                "asset_authorization_required": True,
                "publish_requires_approval": True,
                "render_or_export_is_local_only_until_approved": True,
                "medical_claim_guard": "no_medical_diagnosis_or_treatment_claims",
            },
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def validate_asset_authorizations(assets: list[dict]) -> dict:
    blocked = []
    checked = []
    for raw in assets:
        asset = dict(raw)
        asset_id = str(asset.get("id") or asset.get("uri") or "unknown-asset")
        asset_type = str(asset.get("type") or "unknown")
        requires_auth = asset_type in _ASSET_TYPES_REQUIRING_AUTH
        authorized = bool(asset.get("authorized")) and bool(str(asset.get("license") or "").strip())
        row = {
            "id": asset_id,
            "type": asset_type,
            "license": str(asset.get("license") or ""),
            "authorized": authorized,
            "requires_authorization": requires_auth,
        }
        checked.append(row)
        if requires_auth and not authorized:
            blocked.append(row)
    return {
        "status": "passed" if not blocked else "blocked",
        "checked_assets": checked,
        "blocked_assets": blocked,
    }


def build_video_publish_action(*, project_id: str, platform: str) -> Action:
    return Action(
        kind="publish_video",
        summary=f"发布剪辑工程 {project_id} 到 {platform}",
        payload={"project_id": project_id, "platform": platform},
        idempotency_key=f"publish-{platform}-{project_id}",
        data_class=DataClass.C1_INTERNAL,
        reversible=False,
    )


def _normalize_script(raw: dict[str, Any]) -> dict[str, Any]:
    full_text = str(raw.get("full_text") or " ".join(str(raw.get(key) or "") for key in ("hook", "body", "comment_prompt", "follow_reason"))).strip()
    topic = str(raw.get("topic") or _topic_from_text(full_text))
    sentences = _sentences(full_text)
    hook = str(raw.get("hook") or (sentences[0] if sentences else full_text[:30]))
    body = str(raw.get("body") or full_text)
    comment_prompt = str(raw.get("comment_prompt") or "评论区留下肤质、产品名和使用频率。")
    follow_reason = str(raw.get("follow_reason") or "关注我，少踩一次护肤坑。")
    return {
        "topic": topic,
        "hook": hook,
        "body": body,
        "comment_prompt": comment_prompt,
        "follow_reason": follow_reason,
        "full_text": full_text,
    }


def _timeline(script: dict[str, str], assets: list[dict[str, Any]]) -> dict[str, Any]:
    sentences = _sentences(script["full_text"]) or [script["full_text"]]
    shots = []
    cursor = 0.0
    for index, sentence in enumerate(sentences):
        duration = max(2.2, min(5.5, len(sentence) / 9))
        asset = assets[index % len(assets)] if assets else {}
        shots.append(
            {
                "shot_id": f"shot-{index + 1:02d}",
                "start": round(cursor, 2),
                "end": round(cursor + duration, 2),
                "duration": round(duration, 2),
                "text": sentence,
                "asset_id": str(asset.get("id") or "generated-placeholder"),
                "visual_direction": _visual_direction(index, sentence),
                "caption_style": "high_contrast_bottom_subtitle",
            }
        )
        cursor += duration
    return {
        "duration_seconds": round(cursor, 2),
        "aspect_ratio": "9:16",
        "shots": shots,
        "beat_policy": "caption_aligned_cuts",
    }


def _caption_track(shots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "start": shot["start"],
            "end": shot["end"],
            "text": shot["text"],
            "style": shot["caption_style"],
        }
        for shot in shots
    ]


def _cover_suggestions(script: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"headline": f"{script['topic']}先别跟风", "subhead": "先看屏障和刺激叠加"},
        {"headline": "这一步错了很容易刺痛", "subhead": script["topic"][:20]},
    ]


def _title_suggestions(script: dict[str, str]) -> list[str]:
    return [
        f"{script['topic']}别急着跟风，先看这3点",
        f"敏感肌做{script['topic']}前，先避开这个坑",
    ]


def _tag_suggestions(script: dict[str, str]) -> list[str]:
    base = ["护肤", "敏感肌", "成分党", "屏障修护"]
    topic = script["topic"].replace(" ", "")
    if topic and topic not in base:
        base.insert(0, topic)
    return base[:6]


def _visual_direction(index: int, sentence: str) -> str:
    if index == 0:
        return "开头用标题卡或评论截图制造停留。"
    if any(token in sentence for token in ["成分", "屏障", "刺激", "证据"]):
        return "用成分表、使用顺序或皮肤状态示意做证据化画面。"
    return "用口播 B-roll 和字幕强调关键信息。"


def _sentences(text: str) -> list[str]:
    chunks = []
    current = []
    for char in text:
        current.append(char)
        if char in "。！？!?":
            chunk = "".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []
    rest = "".join(current).strip()
    if rest:
        chunks.append(rest)
    return chunks


def _topic_from_text(text: str) -> str:
    if "早C晚A" in text:
        return "早C晚A"
    if "屏障" in text:
        return "屏障修护"
    return "护肤选题"


def _project_id(script: dict[str, str]) -> str:
    safe = "".join(ch for ch in script["topic"].lower() if ch.isalnum()) or "video"
    return f"m5-{safe}-{abs(hash(script['full_text'])) % 10**6:06d}"
