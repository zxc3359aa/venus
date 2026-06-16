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

DEFAULT_TOOLS = [
    {
        "tool_name": "run_trend_scan",
        "workflow": "trend_scan",
        "description": "Normalize Douyin beauty and skincare trend signals into content opportunities.",
        "approval_level": 1,
    },
    {
        "tool_name": "build_product_intel",
        "workflow": "product_intel",
        "description": "Build product dossiers with filing, ingredient, supplier, report, and controversy checks.",
        "approval_level": 1,
    },
    {
        "tool_name": "analyze_comments",
        "workflow": "comments",
        "description": "Summarize comment intent and draft approval-gated replies.",
        "approval_level": 2,
    },
    {
        "tool_name": "monitor_competitors",
        "workflow": "monitoring",
        "description": "Review competitor videos, lives, ad ratio, risks, and growth opportunities.",
        "approval_level": 1,
    },
    {
        "tool_name": "draft_video_package",
        "workflow": "production",
        "description": "Create scripts, shot lists, subtitle cards, and editing briefs.",
        "approval_level": 2,
    },
    {
        "tool_name": "evaluate_content",
        "workflow": "content_eval",
        "description": "Score retention, interaction, comment, follow, persona, evidence, and claim safety gates.",
        "approval_level": 2,
    },
    {
        "tool_name": "calibrate_performance",
        "workflow": "performance",
        "description": "Turn imported performance metrics into calibration rules and next-content actions.",
        "approval_level": 2,
    },
    {
        "tool_name": "draft_douyin_replies",
        "workflow": "douyin",
        "description": "Prepare Douyin comment and live-message reply queues without posting.",
        "approval_level": 3,
    },
    {
        "tool_name": "plan_ecommerce_ops",
        "workflow": "ecommerce",
        "description": "Plan shop catalog, inventory, product-card, promotion, and after-sales actions.",
        "approval_level": 3,
    },
    {
        "tool_name": "prepare_wechat_handoff",
        "workflow": "wechat",
        "description": "Draft Mini Program answers and Enterprise WeChat handoff notes.",
        "approval_level": 4,
    },
    {
        "tool_name": "plan_commercial_strategy",
        "workflow": "commercial",
        "description": "Prepare Qianchuan and Xingtu recommendations without spend or brand commitments.",
        "approval_level": 4,
    },
    {
        "tool_name": "review_memory",
        "workflow": "memory",
        "description": "Review proposed memory diffs, privacy blocks, and rollback plans.",
        "approval_level": 3,
    },
    {
        "tool_name": "plan_scheduler",
        "workflow": "scheduler",
        "description": "Build 24-hour run queues, approval-gated jobs, and private digests.",
        "approval_level": 2,
    },
    {
        "tool_name": "audit_connectors",
        "workflow": "connectors",
        "description": "Audit connector permissions, logs, rollback readiness, and launch order.",
        "approval_level": 3,
    },
    {
        "tool_name": "plan_airtable_sync",
        "workflow": "airtable_sync_plan",
        "description": "Validate Airtable-ready packages before any future live record write.",
        "approval_level": 2,
    },
    {
        "tool_name": "run_agent_evals",
        "workflow": "evals",
        "description": "Evaluate Agent Run gates before live autopilot is considered.",
        "approval_level": 2,
    },
]


@dataclass(frozen=True)
class AgentsSdkRuntimeConfig:
    namespace: str = "venus_agents_sdk"
    dry_run: bool = True
    approval_mode: str = "manual"
    reviewer: str = "owner"
    sdk_mode: str = "manifest_only"

    def __post_init__(self) -> None:
        values = f"{self.namespace} {self.approval_mode} {self.reviewer} {self.sdk_mode}".lower()
        if "xiaolongxia" in values or "小龙虾" in values:
            raise ValueError("Venus Agents SDK config must not reference Xiaolongxia")
        if not self.namespace.startswith("venus_"):
            raise ValueError("Venus Agents SDK namespace must start with venus_")
        if not self.dry_run:
            raise ValueError("Venus Agents SDK runtime must run in dry-run mode")
        if self.sdk_mode != "manifest_only":
            raise ValueError("Venus Agents SDK runtime must stay in manifest_only mode")


def build_agents_sdk_manifest(
    payload: dict[str, Any],
    config: AgentsSdkRuntimeConfig | None = None,
) -> dict[str, Any]:
    active_config = config or AgentsSdkRuntimeConfig()
    safe_payload = _redact(payload)
    environment = dict(safe_payload.get("environment") or {})
    agent_run = dict(safe_payload.get("agent_run") or {})
    eval_report = dict(safe_payload.get("eval_report") or {})
    tool_registry, blocked_tools = _tool_registry(safe_payload)
    deployment_readiness = _deployment_readiness(
        environment=environment,
        eval_report=eval_report,
        blocked_tools=blocked_tools,
    )
    approval_records = _approval_records(
        safe_payload=safe_payload,
        deployment_readiness=deployment_readiness,
        reviewer=active_config.reviewer,
    )

    return {
        "workflow": "agents_sdk",
        "namespace": active_config.namespace,
        "dry_run": active_config.dry_run,
        "approval_mode": active_config.approval_mode,
        "sdk_mode": active_config.sdk_mode,
        "source": str(safe_payload.get("source") or "local_agents_sdk_runtime_manifest"),
        "generated_at": str(safe_payload.get("generated_at") or "local-time"),
        "summary": {
            "agent_count": 1,
            "tool_count": len(tool_registry),
            "blocked_tool_count": len(blocked_tools),
            "readiness_blocker_count": len(deployment_readiness["blockers"]),
            "approval_record_count": len(approval_records),
            "deployment_ready": deployment_readiness["ready"],
        },
        "agent_manifest": _agent_manifest(active_config),
        "tool_registry": tool_registry,
        "blocked_tools": blocked_tools,
        "runtime_plan": _runtime_plan(deployment_readiness, agent_run),
        "guardrails": _guardrails(),
        "eval_hooks": _eval_hooks(eval_report),
        "deployment_readiness": deployment_readiness,
        "approval_records": approval_records,
        "external_actions": [],
        "safety_boundary": {
            "max_automatic_level": 1,
            "notes": [
                "This workflow creates a local Agents SDK-ready manifest only.",
                "No OpenAI API call, model run, trace upload, hosted eval, deployment, Feishu send, Douyin reply, Airtable write, ad spend, WeChat contact, memory write, backup write, or external action is executed.",
                "Live SDK execution remains blocked until credentials, dependency installation, eval readiness, and level-4 owner approval are complete.",
            ],
        },
    }


def _agent_manifest(config: AgentsSdkRuntimeConfig) -> dict[str, Any]:
    return {
        "name": "VenusSkincareOperator",
        "namespace": config.namespace,
        "model_env_var": "VENUS_OPENAI_MODEL",
        "default_model": "gpt-5.5",
        "instructions": [
            "Operate as Venus, a beauty and skincare growth agent for Douyin creator operations.",
            "Ground skincare and product claims in evidence, filing status, ingredient context, and risk language.",
            "Keep Venus data, files, commands, logs, and secrets isolated from other Feishu agents.",
            "Treat public replies, publishing, lead routing, memory writes, connector writes, and ad spend as approval-gated.",
        ],
        "output_contract": {
            "format": "json",
            "required_keys": [
                "workflow",
                "summary",
                "action_plan",
                "approval_records",
                "external_actions",
                "safety_boundary",
            ],
        },
    }


def _tool_registry(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tools = [_tool(item) for item in DEFAULT_TOOLS]
    blocked_tools: list[dict[str, Any]] = []
    for override in [dict(item) for item in list(payload.get("tool_overrides") or [])]:
        if bool(override.get("external_action_enabled")):
            blocked_tools.append(_blocked_tool(override, "external_tool_not_allowed"))
            continue
        tools.append(_tool(override))
    return tools, blocked_tools


def _tool(item: dict[str, Any]) -> dict[str, Any]:
    approval_level = int(_number(item.get("approval_level")))
    return {
        "tool_name": str(item.get("tool_name") or item.get("workflow") or "tool"),
        "workflow": str(item.get("workflow") or ""),
        "description": str(item.get("description") or ""),
        "tool_type": "function_tool_candidate",
        "approval_level": approval_level,
        "requires_manual_approval": approval_level >= 2,
        "state_access": "local_venus_payload_only",
        "external_action_enabled": False,
    }


def _blocked_tool(item: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "tool_name": str(item.get("tool_name") or item.get("workflow") or "tool"),
        "workflow": str(item.get("workflow") or ""),
        "skip_reason": reason,
    }


def _runtime_plan(
    deployment_readiness: dict[str, Any],
    agent_run: dict[str, Any],
) -> dict[str, Any]:
    return {
        "entrypoint": "venus agents-sdk data/samples/agents_sdk.json",
        "future_sdk_command": "uv run python -m venus.agents_app",
        "required_env": ["OPENAI_API_KEY", "VENUS_OPENAI_MODEL"],
        "state_strategy": "server_managed_local_json_then_approved_external_sync",
        "approval_strategy": "manual_level_2_plus",
        "readiness_state": deployment_readiness["status"],
        "agent_run_reference": str(agent_run.get("run_id") or "venus-run-local"),
        "external_action_enabled": False,
    }


def _guardrails() -> list[dict[str, Any]]:
    return [
        {
            "guardrail_id": "privacy_isolation",
            "rule": "Reject other-agent references, direct personal data, and secret-like payload values.",
            "severity": "critical",
        },
        {
            "guardrail_id": "skincare_claim_safety",
            "rule": "Block medical or cosmetic efficacy claims without evidence and risk wording.",
            "severity": "critical",
        },
        {
            "guardrail_id": "external_action_lock",
            "rule": "Block replies, publishing, ad spend, connector writes, memory writes, and backups until approved.",
            "severity": "critical",
        },
    ]


def _eval_hooks(eval_report: dict[str, Any]) -> dict[str, Any]:
    summary = dict(eval_report.get("summary") or {})
    return {
        "local_eval_workflow": "evals",
        "required_before_live": True,
        "current_readiness_status": str(summary.get("readiness_status") or "missing_eval_report"),
        "autopilot_ready": bool(summary.get("autopilot_ready")),
        "recommended_next_step": "run_local_evals_before_sdk_execution",
    }


def _deployment_readiness(
    environment: dict[str, Any],
    eval_report: dict[str, Any],
    blocked_tools: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers = []
    if not bool(environment.get("OPENAI_API_KEY_configured")):
        blockers.append(_blocker("missing_openai_api_key", "Configure OPENAI_API_KEY before any SDK run."))
    if not bool(environment.get("openai_agents_installed")):
        blockers.append(_blocker("missing_openai_agents_dependency", "Install openai-agents before building the SDK app."))
    eval_summary = dict(eval_report.get("summary") or {})
    if not bool(eval_summary.get("autopilot_ready")):
        blockers.append(_blocker("evals_not_ready", "Local eval gates are not ready for SDK execution."))
    if blocked_tools:
        blockers.append(_blocker("external_tool_blocked", "One or more requested tools attempted to enable external actions."))
    ready = not blockers and bool(environment.get("deployment_manager_ready"))
    return {
        "status": "ready_for_sdk_build_review" if ready else "blocked_by_sdk_readiness",
        "ready": ready,
        "blockers": blockers,
        "checks": {
            "OPENAI_API_KEY_configured": bool(environment.get("OPENAI_API_KEY_configured")),
            "openai_agents_installed": bool(environment.get("openai_agents_installed")),
            "deployment_manager_ready": bool(environment.get("deployment_manager_ready")),
            "evals_autopilot_ready": bool(eval_summary.get("autopilot_ready")),
            "external_tool_block_count": len(blocked_tools),
        },
    }


def _blocker(blocker_id: str, message: str) -> dict[str, str]:
    return {"blocker_id": blocker_id, "message": message}


def _approval_records(
    safe_payload: dict[str, Any],
    deployment_readiness: dict[str, Any],
    reviewer: str,
) -> list[dict[str, Any]]:
    if not bool(safe_payload.get("live_sdk_requested")):
        return []
    return [
        create_approval_record(
            action_type="venus_agents_sdk_live_enablement_review",
            approval_level=4,
            draft=(
                "Review whether Venus can move from manifest-only Agents SDK planning "
                f"to live SDK execution. Current readiness: {deployment_readiness['status']}."
            ),
            evidence_ids=[str(item["blocker_id"]) for item in deployment_readiness["blockers"]],
            reviewer=reviewer,
            created_at=str(safe_payload.get("generated_at") or "local-time"),
        )
    ]


def _number(value: Any) -> float:
    try:
        return float(value or 0)
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
