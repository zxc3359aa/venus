from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from venus.approvals import create_approval_record, requires_manual_approval
from venus.persona import build_persona_profile, rewrite_in_persona


SECRET_KEYS = {
    "secret",
    "token",
    "password",
    "app_secret",
    "authorization",
    "api_key",
    "openid",
    "unionid",
    "wechat_id",
    "phone",
    "mobile",
    "contact",
}

HIGH_RISK_TERMS = ["屏障受损", "泛红", "烂脸", "过敏", "激素", "刷酸", "早C晚A", "孕妇", "爆皮"]
LEAD_INTENT_TERMS = ["企业微信", "企微", "进群", "加微信", "加你", "看产品搭配", "私聊"]


@dataclass(frozen=True)
class WeChatPrivateDomainConfig:
    namespace: str = "venus_wechat"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus WeChat config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus WeChat namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus WeChat private-domain connector must run in dry-run mode")


def build_wechat_private_domain_report(
    payload: dict[str, Any],
    config: WeChatPrivateDomainConfig | None = None,
) -> dict[str, Any]:
    active_config = config or WeChatPrivateDomainConfig()
    safe_payload = _redact(payload)
    profile = build_persona_profile(
        list(safe_payload.get("persona_samples") or ["姐妹们，先看屏障状态，证据和体验都要说清楚。"])
    )

    sessions = list(safe_payload.get("mini_program_sessions") or [])
    answer_queue = _build_answer_queue(sessions, profile)
    handoff_queue = _build_handoff_queue(sessions, answer_queue, profile)
    approval_records = _build_approval_records(
        answer_queue=answer_queue,
        handoff_queue=handoff_queue,
        reviewer=active_config.reviewer,
        created_at=str(safe_payload.get("retrieved_at") or "local-time"),
    )

    return {
        "workflow": "wechat",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "source": {
            "source_type": str(safe_payload.get("source") or "mini_program_export"),
            "retrieved_at": str(safe_payload.get("retrieved_at") or "local-time"),
            "freshness": "manual-import",
            "notes": "Replace this local import with permissioned WeChat Mini Program and Enterprise WeChat APIs after credentials and approvals are configured.",
        },
        "summary": {
            "session_count": len(sessions),
            "question_count": len(answer_queue),
            "high_risk_question_count": sum(1 for item in answer_queue if item["risk"] == "high"),
            "lead_intent_count": sum(1 for item in answer_queue if item["intent"] == "lead_handoff"),
            "enterprise_wechat_handoff_count": len(handoff_queue),
            "approval_gated_action_count": len(approval_records),
        },
        "answer_queue": answer_queue,
        "handoff_queue": handoff_queue,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "WeChat private-domain data is read from local/manual exports in this slice.",
                "Mini-program answers and Enterprise WeChat handoffs are not sent.",
                "Medical-like skincare advice and customer routing require approval level 4.",
            ],
        },
    }


def _build_answer_queue(sessions: list[dict[str, Any]], profile: Any) -> list[dict[str, Any]]:
    queue = []
    for session in sessions:
        session_id = str(session.get("session_id") or session.get("id") or "unknown-session")
        for question in list(session.get("questions") or []):
            text = str(question.get("text") or "")
            risk = _risk_level(text)
            intent = _intent(text)
            approval_level = 4 if risk == "high" or intent == "lead_handoff" else 2
            queue.append(
                {
                    "action_type": "wechat_mini_program_answer",
                    "session_id": session_id,
                    "question_id": str(question.get("question_id") or question.get("id") or ""),
                    "text": text,
                    "intent": intent,
                    "risk": risk,
                    "approval_level": approval_level,
                    "requires_manual_approval": requires_manual_approval(approval_level),
                    "execution_state": "blocked_until_approved",
                    "draft_answer": rewrite_in_persona(_answer_base(text, intent, risk), profile),
                    "external_action_enabled": False,
                }
            )
    return queue


def _build_handoff_queue(
    sessions: list[dict[str, Any]],
    answer_queue: list[dict[str, Any]],
    profile: Any,
) -> list[dict[str, Any]]:
    sessions_by_id = {
        str(session.get("session_id") or session.get("id") or "unknown-session"): session
        for session in sessions
    }
    handoffs = []
    for item in answer_queue:
        if item["intent"] != "lead_handoff":
            continue
        session = sessions_by_id.get(item["session_id"], {})
        handoffs.append(
            {
                "action_type": "enterprise_wechat_handoff",
                "session_id": item["session_id"],
                "question_id": item["question_id"],
                "handoff_channel": "enterprise_wechat",
                "handoff_reason": "user_requested_private_domain_help",
                "approval_level": 4,
                "requires_manual_approval": True,
                "execution_state": "blocked_until_approved",
                "nickname": str(session.get("nickname") or ""),
                "handoff_script": rewrite_in_persona(
                    "可以引导加企业微信，但要先说明用途：只用于肤质信息、产品搭配和后续答疑，不承诺治疗效果。",
                    profile,
                ),
                "external_action_enabled": False,
            }
        )
    return handoffs


def _build_approval_records(
    answer_queue: list[dict[str, Any]],
    handoff_queue: list[dict[str, Any]],
    reviewer: str,
    created_at: str,
) -> list[dict[str, Any]]:
    records = []
    for item in answer_queue:
        if item["intent"] == "lead_handoff":
            continue
        if not item.get("requires_manual_approval"):
            continue
        records.append(
            create_approval_record(
                action_type=str(item["action_type"]),
                approval_level=int(item["approval_level"]),
                draft=str(item["draft_answer"]),
                evidence_ids=[str(item.get("question_id") or "")],
                reviewer=reviewer,
                created_at=created_at,
            )
        )

    for item in handoff_queue:
        records.append(
            create_approval_record(
                action_type=str(item["action_type"]),
                approval_level=int(item["approval_level"]),
                draft=str(item["handoff_script"]),
                evidence_ids=[str(item.get("question_id") or "")],
                reviewer=reviewer,
                created_at=created_at,
            )
        )
    return records


def _intent(text: str) -> str:
    if any(term in text for term in LEAD_INTENT_TERMS):
        return "lead_handoff"
    if "能不能" in text or "还能" in text or "可以" in text:
        return "skincare_question"
    return "general_question"


def _risk_level(text: str) -> str:
    return "high" if any(term in text for term in HIGH_RISK_TERMS) else "medium"


def _answer_base(text: str, intent: str, risk: str) -> str:
    if intent == "lead_handoff":
        return "可以继续帮你看产品搭配，但不要直接发隐私信息，先说明肤质、预算、正在用的产品和不耐受史。"
    if risk == "high":
        return "屏障状态不稳定时先不要叠加强刺激组合，先看泛红、刺痛、爆皮和耐受，再决定是否暂停早C晚A。"
    return "先把肤质、当前诉求和正在用的产品拆开看，再判断是否适合继续使用。"


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
