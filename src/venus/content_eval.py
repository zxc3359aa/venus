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

KPI_DEFINITIONS = {
    "retention_score": {
        "definition": "Scores hook clarity, first-three-second tension, and scene pacing.",
        "decision_use": "判断开头和节奏是否值得进入剪辑。",
    },
    "interaction_score": {
        "definition": "Scores whether the package gives viewers a reason to comment, save, or ask for help.",
        "decision_use": "判断内容是否有明确互动动作。",
    },
    "comment_score": {
        "definition": "Scores how specific the comment prompt is about skin state, products, and frequency.",
        "decision_use": "判断评论区能否产生可回复的问题。",
    },
    "follow_score": {
        "definition": "Scores whether the content gives viewers a credible reason to follow for more analysis.",
        "decision_use": "判断内容是否能沉淀关注关系。",
    },
    "persona_score": {
        "definition": "Scores alignment with Venus' evidence-first, conversational skincare persona.",
        "decision_use": "判断文案是否像用户本人表达。",
    },
    "safety_score": {
        "definition": "Scores skincare claim restraint, evidence framing, and absence of forbidden claims.",
        "decision_use": "判断内容是否需要先改合规风险再发布。",
    },
}


@dataclass(frozen=True)
class ContentEvalConfig:
    namespace: str = "venus_content_eval"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus content eval config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus content eval namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus content eval must run in dry-run mode")


def build_content_eval_report(
    payload: dict[str, Any],
    config: ContentEvalConfig | None = None,
) -> dict[str, Any]:
    active_config = config or ContentEvalConfig()
    safe_payload = _redact(payload)
    text = _combined_text(safe_payload)
    forbidden_claims = [str(item) for item in list(safe_payload.get("forbidden_claims") or [])]
    blocking_terms = _blocking_terms(text, forbidden_claims)
    evidence_ids = [str(item) for item in list(safe_payload.get("evidence_ids") or [])]

    scorecard = _build_scorecard(safe_payload, text, blocking_terms)
    revision_queue = _build_revision_queue(
        safe_payload=safe_payload,
        scorecard=scorecard,
        blocking_terms=blocking_terms,
        evidence_ids=evidence_ids,
    )
    publish_readiness = _publish_readiness(scorecard, revision_queue)
    approval_records = _build_approval_records(
        safe_payload=safe_payload,
        revision_queue=revision_queue,
        publish_readiness=publish_readiness,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("evaluated_at") or "local-time"),
    )

    return {
        "workflow": "content_eval",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "manual_pre_publish_review"),
            "evaluated_at": str(safe_payload.get("evaluated_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "This dry-run evaluation scores local script structure and claim safety without reading live Douyin metrics.",
        },
        "summary": {
            "dimension_count": len(scorecard),
            "overall_score": _overall_score(scorecard),
            "revision_count": len(revision_queue),
            "high_priority_revision_count": sum(1 for item in revision_queue if item["priority"] == "high"),
            "blocking_issue_count": sum(1 for item in revision_queue if item["blocks_publish"]),
            "approval_record_count": len(approval_records),
            "publish_ready": publish_readiness["publish_ready"],
        },
        "scorecard": scorecard,
        "publish_readiness": publish_readiness,
        "revision_queue": revision_queue,
        "kpi_definitions": KPI_DEFINITIONS,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "Scores are deterministic pre-publish signals, not measured Douyin performance.",
                "No video is rendered, uploaded, scheduled, promoted, or published.",
                "Claim-risk blockers and live publish requests remain approval-gated.",
            ],
        },
    }


def _build_scorecard(
    safe_payload: dict[str, Any],
    text: str,
    blocking_terms: list[str],
) -> dict[str, dict[str, Any]]:
    script = dict(safe_payload.get("script_package") or {})
    publish = dict(safe_payload.get("publish_package") or {})
    hook = str(script.get("hook") or "")
    cta = str(script.get("cta") or "")
    comment_prompt = str(script.get("comment_prompt") or "")
    shot_list = list(safe_payload.get("shot_list") or [])
    title_options = list(script.get("title_options") or [])
    hashtags = list(publish.get("hashtags") or [])
    caption = str(publish.get("caption") or "")

    retention = 40
    if hook:
        retention += 20
    if _contains_any(hook, ["3秒", "30秒", "先别急", "别急", "踩坑", "高风险"]):
        retention += 20
    if shot_list and str(dict(shot_list[0]).get("retention_goal") or "") == "first_three_seconds":
        retention += 10
    if len(shot_list) >= 5:
        retention += 5

    interaction = 40
    if cta and not _is_generic_cta(cta):
        interaction += 10
    if comment_prompt:
        interaction += 20
    if caption:
        interaction += 10
    if hashtags:
        interaction += 10
    if _contains_any(f"{cta} {comment_prompt}", ["评论", "收藏", "关注", "留下"]):
        interaction += 10

    comment = 35
    if "评论区" in comment_prompt:
        comment += 25
    if "肤质" in comment_prompt:
        comment += 15
    if "产品" in comment_prompt:
        comment += 10
    if "频率" in comment_prompt:
        comment += 10
    if "帮你拆" in comment_prompt:
        comment += 5

    follow = 35
    if "关注" in cta:
        follow += 35
    if len(title_options) >= 3:
        follow += 15
    if _contains_any(text, ["后续", "继续", "每天", "系列"]):
        follow += 10
    if cta and not _is_generic_cta(cta):
        follow += 15
    else:
        follow += 10

    persona = 50
    if "姐妹们" in text:
        persona += 15
    if "屏障" in text:
        persona += 15
    if "证据" in text:
        persona += 15
    if _contains_any(text, ["先别急", "别急", "先看"]):
        persona += 5

    safety = max(0, 100 - 45 * len(blocking_terms))

    return {
        "retention_score": _dimension(min(retention, 100), "opening_and_pacing"),
        "interaction_score": _dimension(min(interaction, 100), "viewer_action"),
        "comment_score": _dimension(min(comment, 100), "comment_prompt_specificity"),
        "follow_score": _dimension(min(follow, 100), "follow_reason"),
        "persona_score": _dimension(min(persona, 100), "voice_fit"),
        "safety_score": _dimension(min(safety, 100), "claim_safety", blocked=bool(blocking_terms)),
    }


def _build_revision_queue(
    safe_payload: dict[str, Any],
    scorecard: dict[str, dict[str, Any]],
    blocking_terms: list[str],
    evidence_ids: list[str],
) -> list[dict[str, Any]]:
    revisions = []
    topic = str(safe_payload.get("topic") or "content")
    if blocking_terms:
        revisions.append(
            {
                "category": "claim_safety",
                "priority": "high",
                "blocks_publish": True,
                "issue": f"Remove or qualify forbidden claim wording: {', '.join(blocking_terms)}.",
                "suggested_fix": "Replace absolute repair promises with evidence, skin-state, tolerance, and usage-context language.",
                "evidence_ids": [topic],
            }
        )
    if not evidence_ids:
        revisions.append(
            {
                "category": "evidence_gap",
                "priority": "high",
                "blocks_publish": False,
                "issue": "The package does not cite evidence IDs for the claim-sensitive segment.",
                "suggested_fix": "Attach filing, ingredient, test-report, or controversy evidence before final review.",
                "evidence_ids": [topic],
            }
        )
    if scorecard["follow_score"]["score"] < 70:
        revisions.append(
            {
                "category": "follow_cta",
                "priority": "medium",
                "blocks_publish": False,
                "issue": "The CTA does not give viewers a clear reason to follow.",
                "suggested_fix": "Add a follow reason tied to future product breakdowns, skin-state checks, or ingredient comparisons.",
                "evidence_ids": [topic],
            }
        )
    return sorted(revisions, key=lambda item: {"high": 0, "medium": 1, "low": 2}[str(item["priority"])])


def _publish_readiness(
    scorecard: dict[str, dict[str, Any]],
    revision_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    if any(item["category"] == "claim_safety" and item["blocks_publish"] for item in revision_queue):
        status = "blocked_by_claim_risk"
        manual_review_level = 3
    elif _overall_score(scorecard) < 80 or revision_queue:
        status = "needs_revision"
        manual_review_level = 2
    else:
        status = "ready_for_manual_publish_review"
        manual_review_level = 2
    return {
        "status": status,
        "publish_ready": status == "ready_for_manual_publish_review",
        "manual_review_level": manual_review_level,
        "blocking_reasons": [
            str(item["category"]) for item in revision_queue if item["blocks_publish"]
        ],
        "external_action_enabled": False,
    }


def _build_approval_records(
    safe_payload: dict[str, Any],
    revision_queue: list[dict[str, Any]],
    publish_readiness: dict[str, Any],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    topic = str(safe_payload.get("topic") or "content")
    if revision_queue:
        records.append(
            create_approval_record(
                action_type="venus_content_revision_review",
                approval_level=2,
                draft=f"Review {len(revision_queue)} content revision tasks before publishing {topic}.",
                evidence_ids=[str(item["category"]) for item in revision_queue],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    if bool(safe_payload.get("live_publish_requested")) or publish_readiness["manual_review_level"] >= 3:
        records.append(
            create_approval_record(
                action_type="venus_content_publish_review",
                approval_level=int(publish_readiness["manual_review_level"]),
                draft=f"Review publish readiness for {topic}; no upload or public action is allowed in dry-run mode.",
                evidence_ids=[topic],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _dimension(score: int, signal: str, blocked: bool = False) -> dict[str, Any]:
    if blocked:
        status = "blocked"
    elif score >= 85:
        status = "strong"
    elif score >= 70:
        status = "usable"
    else:
        status = "needs_work"
    return {
        "score": score,
        "status": status,
        "signal": signal,
    }


def _overall_score(scorecard: dict[str, dict[str, Any]]) -> int:
    weights = {
        "retention_score": 0.25,
        "interaction_score": 0.15,
        "comment_score": 0.20,
        "follow_score": 0.10,
        "persona_score": 0.15,
        "safety_score": 0.15,
    }
    total = sum(scorecard[key]["score"] * weight for key, weight in weights.items())
    return int(total + 0.5)


def _blocking_terms(text: str, forbidden_claims: list[str]) -> list[str]:
    terms = []
    for claim in forbidden_claims:
        if claim and claim in text:
            terms.append(claim)
    if not forbidden_claims and _contains_any(text, ["100%", "根治", "治愈", "一定修复"]):
        terms.append("absolute_claim")
    return sorted(set(terms))


def _combined_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            chunks.append(value)

    walk(
        {
            "topic": payload.get("topic"),
            "objective": payload.get("objective"),
            "script_package": payload.get("script_package"),
            "publish_package": payload.get("publish_package"),
            "risk_notes": payload.get("risk_notes"),
        }
    )
    return " ".join(chunks)


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _is_generic_cta(text: str) -> bool:
    return text.strip() in {"了解了吧", "记住了吗", "懂了吗"}


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
