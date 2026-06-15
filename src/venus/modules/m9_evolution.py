"""M9 自我进化、漏洞弥补与备份离线治理包。

本模块只生成评估、改进、审批和备份校验描述；不执行真实删除、备份、
平台调用或模型训练。所有高风险动作都以 Action 形式交给审批系统。
"""
from __future__ import annotations

from typing import Any

from venus.contracts import Action, DataClass, Tagged


AUTO_CHANGE_CATEGORIES = {"prompt_parameter", "parameter", "strategy_parameter", "rubric_threshold"}
APPROVAL_CHANGE_CATEGORIES = {
    "core_identity",
    "compliance_policy",
    "budget_permission",
    "external_action_strategy",
    "model_training",
    "privacy_boundary",
}
PRIVATE_DESTINATIONS = {"cloud_llm", "third_party_data", "cloud_training", "external_model"}


def build_m9_evolution_report(source: Tagged) -> Tagged:
    """生成系统健康、评估记录、受控改进闭环与 3-2-1 备份校验报告。"""
    _reject_private_payload(source)
    payload = source.payload if isinstance(source.payload, dict) else {}
    eval_records = _eval_runs_sink(list(payload.get("eval_runs") or []))
    incidents = [_normalize_incident(item) for item in list(payload.get("incidents") or [])]
    weaknesses = _weaknesses(eval_records["records"], incidents)
    improvement_loop = _improvement_loop(list(payload.get("candidate_changes") or []), weaknesses)

    return Tagged(
        payload={
            "module": "m9_evolution",
            "system_health": _system_health(eval_records["records"], incidents),
            "eval_runs_sink": eval_records,
            "weaknesses": weaknesses,
            "improvement_loop": improvement_loop,
            "backup_plan": _backup_plan(dict(payload.get("backup") or {})),
            "governance_actions": {
                "high_risk_changes": "build_policy_change_action",
                "data_erasure": "build_data_delete_action",
                "approval_first": True,
            },
            "self_evolution_boundary": {
                "allowed_learning": "aggregate_eval_metrics_and_approved_descriptors",
                "blocked_learning": (
                    "C3 raw persona corpus, private chat, private-domain PII, "
                    "unapproved cloud training"
                ),
                "rollback_policy": "every automated candidate uses canary rollout with rollback_ref",
            },
            "external_actions": [],
        },
        data_class=DataClass.C2_SENSITIVE,
        pii=False,
    )


def validate_evolution_proposal(proposal: dict[str, Any]) -> list[str]:
    """检查候选自进化方案是否越过隐私、审批或安全边界。"""
    issues: list[str] = []
    data_class = str(proposal.get("data_class") or "")
    destination = str(proposal.get("destination") or "")
    category = str(proposal.get("category") or "")
    summary = str(proposal.get("summary") or "")

    if data_class == DataClass.C3_SECRET.name and destination in PRIVATE_DESTINATIONS:
        issues.append("C3 个人画像/语料/私域信息禁止发送到云端或第三方模型。")
    if category in APPROVAL_CHANGE_CATEGORIES:
        issues.append(f"{category} 属于高风险自进化范围，必须先审批并保留回滚方案。")
    if "关闭合规" in summary or "跳过审批" in summary:
        issues.append("自进化方案不得绕过合规门或人在回路审批。")
    return issues


def build_policy_change_action(change_id: str, category: str) -> Action:
    """构造核心策略/身份/权限变更审批动作。"""
    safe_change_id = _safe_identifier(change_id, field_name="change_id")
    safe_category = _safe_identifier(category, field_name="category")
    return Action(
        kind="change_governed_policy",
        summary=f"审批 M9 高风险策略变更：{safe_category}",
        payload={
            "change_id": safe_change_id,
            "category": safe_category,
            "requires_approval": True,
            "rollback_required": True,
            "scope": "m9_governed_change",
            "execution_boundary": "no_change_before_owner_approval",
        },
        idempotency_key=f"policy-change-{safe_change_id}",
        data_class=DataClass.C1_INTERNAL,
        reversible=True,
    )


def build_data_delete_action(subject_ref: str, reason: str) -> Action:
    """构造数据删除审批动作；只接收哈希/内部引用，不接收原始联系方式。"""
    safe_subject_ref = _safe_identifier(subject_ref, field_name="subject_ref")
    safe_reason = _safe_identifier(reason, field_name="reason")
    return Action(
        kind="delete_data",
        summary=f"审批删除数据主体引用：{safe_subject_ref}",
        payload={
            "subject_ref": safe_subject_ref,
            "reason": safe_reason,
            "requires_approval": True,
            "data_minimization": True,
            "proof_required": "deletion_log_and_backup_tombstone",
        },
        idempotency_key=f"delete-data-{safe_subject_ref}",
        data_class=DataClass.C1_INTERNAL,
        reversible=False,
    )


def _reject_private_payload(source: Tagged) -> None:
    if source.data_class == DataClass.C3_SECRET or source.pii:
        raise ValueError(
            "M9 不接收 C3/PII；自进化只使用聚合评估、批准后的描述符与系统指标。"
        )


def _eval_runs_sink(raw_runs: list[Any]) -> dict[str, Any]:
    records = []
    for item in raw_runs:
        raw = dict(item or {})
        score = _float(raw.get("score"))
        threshold = _float(raw.get("threshold"), default=1.0)
        records.append(
            {
                "table": "venus_eval_runs",
                "module": str(raw.get("module") or "unknown_module"),
                "kpi": str(raw.get("kpi") or "unknown_kpi"),
                "score": round(score, 4),
                "threshold": round(threshold, 4),
                "status": "passed" if score >= threshold else "below_threshold",
                "gap": round(score - threshold, 4),
                "data_class": "C2_SENSITIVE",
            }
        )
    return {
        "table": "venus_eval_runs",
        "records": records,
        "retention_policy": "aggregate_metrics_only_no_c3_raw_payload",
    }


def _normalize_incident(raw: Any) -> dict[str, Any]:
    item = dict(raw or {})
    count = max(1, int(_float(item.get("count"), default=1.0)))
    return {
        "module": str(item.get("module") or "unknown_module"),
        "kind": str(item.get("kind") or "unknown_incident"),
        "count": count,
        "severity": str(item.get("severity") or ("high" if count >= 2 else "medium")),
    }


def _system_health(eval_records: list[dict[str, Any]], incidents: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in eval_records if item["status"] == "below_threshold"]
    high_incidents = [item for item in incidents if item["severity"] == "high"]
    status = "healthy" if not failed and not incidents else "needs_attention"
    return {
        "status": status,
        "failed_eval_count": len(failed),
        "incident_count": sum(item["count"] for item in incidents),
        "high_incident_count": len(high_incidents),
        "review_cadence": "daily_when_attention_needed_weekly_when_healthy",
    }


def _weaknesses(eval_records: list[dict[str, Any]], incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_module: dict[str, dict[str, Any]] = {}
    for record in eval_records:
        if record["status"] != "below_threshold":
            continue
        module = record["module"]
        weakness = by_module.setdefault(
            module,
            {
                "module": module,
                "signals": [],
                "severity_score": 0.0,
                "root_cause_hypothesis": "needs_review",
                "next_step": "run_small_reversible_experiment",
            },
        )
        weakness["signals"].append(
            {"kind": "eval_gap", "kpi": record["kpi"], "gap": round(abs(record["gap"]), 4)}
        )
        weakness["severity_score"] += abs(float(record["gap"]))
    for incident in incidents:
        module = incident["module"]
        weakness = by_module.setdefault(
            module,
            {
                "module": module,
                "signals": [],
                "severity_score": 0.0,
                "root_cause_hypothesis": "needs_review",
                "next_step": "run_small_reversible_experiment",
            },
        )
        weakness["signals"].append(
            {"kind": "incident", "incident_kind": incident["kind"], "count": incident["count"]}
        )
        weakness["severity_score"] += incident["count"] * (0.15 if incident["severity"] == "high" else 0.08)
    rows = list(by_module.values())
    for row in rows:
        row["severity_score"] = round(float(row["severity_score"]), 4)
        row["root_cause_hypothesis"] = _root_cause(row["module"], row["signals"])
    rows.sort(key=lambda item: (item["severity_score"], item["module"]), reverse=True)
    return rows


def _root_cause(module: str, signals: list[dict[str, Any]]) -> str:
    signal_text = " ".join(str(signal.get("kpi") or signal.get("incident_kind") or "") for signal in signals)
    if module == "m4" or "reply" in signal_text:
        return "community_reply_safety_or_medical_claim_risk"
    if module == "m7" or "roas" in signal_text or "cost" in signal_text:
        return "ad_budget_or_roas_guardrail_pressure"
    if module == "m1":
        return "content_topic_or_script_quality_drift"
    return "module_metric_below_threshold_needs_owner_review"


def _improvement_loop(candidates: list[Any], weaknesses: list[dict[str, Any]]) -> dict[str, Any]:
    auto_candidates: list[dict[str, Any]] = []
    approval_required: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in candidates:
        candidate = dict(item or {})
        category = str(candidate.get("category") or "unknown")
        normalized = {
            "change_id": str(candidate.get("change_id") or "candidate-unknown"),
            "category": category,
            "summary": str(candidate.get("summary") or ""),
            "expected_gain": _float(candidate.get("expected_gain")),
            "rollback_ref": str(candidate.get("rollback_ref") or "previous_version"),
        }
        issues = validate_evolution_proposal(candidate)
        if issues and category not in APPROVAL_CHANGE_CATEGORIES:
            rejected.append({**normalized, "issues": issues})
        elif category in AUTO_CHANGE_CATEGORIES and not issues:
            auto_candidates.append(
                {
                    **normalized,
                    "rollout": "canary_with_rollback",
                    "max_scope": "single_module_small_traffic_or_offline_eval",
                    "requires_owner_approval": False,
                }
            )
        else:
            approval_required.append(
                {
                    **normalized,
                    "requires_owner_approval": True,
                    "rollback_required": True,
                    "issues": issues,
                }
            )
    if not candidates and weaknesses:
        auto_candidates.append(
            {
                "change_id": f"auto-{weaknesses[0]['module']}-rubric-001",
                "category": "rubric_threshold",
                "summary": "根据评估弱点生成离线小流量校准实验",
                "expected_gain": 0.03,
                "rollback_ref": "current_rubric",
                "rollout": "canary_with_rollback",
                "max_scope": "offline_eval_first",
                "requires_owner_approval": False,
            }
        )
    return {
        "allowed_scope": "authorized_and_privacy_matrix_compliant_only",
        "auto_candidates": auto_candidates,
        "approval_required_changes": approval_required,
        "rejected_candidates": rejected,
        "learning_inputs": ["venus_eval_runs", "venus_metric_timeseries", "approved_persona_descriptor"],
        "privacy_firewall": "C3 never leaves local/private boundary; no third-party model training",
    }


def _backup_plan(raw: dict[str, Any]) -> dict[str, Any]:
    copies = [dict(item or {}) for item in list(raw.get("copies") or [])]
    encrypted_copies = sum(1 for item in copies if bool(item.get("encrypted")))
    checksums = [str(item.get("checksum")) for item in copies if item.get("checksum")]
    media = {str(item.get("medium") or "unknown") for item in copies}
    offsite_or_offline = any(
        "offline" in str(item.get("medium") or "").lower()
        or "offline" in str(item.get("location") or "").lower()
        or "offsite" in str(item.get("location") or "").lower()
        for item in copies
    )
    restore_drill = dict(raw.get("restore_drill") or {})
    restore_verified = (
        len(copies) >= 3
        and len(media) >= 2
        and encrypted_copies == len(copies)
        and len(checksums) == len(copies)
        and offsite_or_offline
        and restore_drill.get("status") == "passed"
        and bool(restore_drill.get("checksum_match"))
        and int(_float(restore_drill.get("sampled_restore_count"))) > 0
    )
    return {
        "strategy": "3-2-1",
        "status": "restore_verified" if restore_verified else "needs_rehearsal",
        "backup_id": str(raw.get("backup_id") or "backup-plan-pending"),
        "copy_count": len(copies),
        "encrypted_copies": encrypted_copies,
        "media_count": len(media),
        "offsite_or_offline_copy": offsite_or_offline,
        "schedule": dict(raw.get("schedule") or {"incremental": "daily", "full": "weekly"}),
        "restore_drill": restore_drill,
        "venus_backups_record": {
            "table": "venus_backups",
            "backup_id": str(raw.get("backup_id") or "backup-plan-pending"),
            "restore_verified": restore_verified,
            "checksums": checksums,
            "data_class": "C2_SENSITIVE",
        },
        "data_residency_policy": "personal_info_cn_or_assessed_before_cross_border",
    }


def _safe_identifier(value: str, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} 不能为空")
    if any(char in text for char in ("@", "+", " ")):
        raise ValueError(f"{field_name} 必须是内部引用或哈希，不能包含原始联系方式")
    digit_count = sum(1 for char in text if char.isdigit())
    if digit_count >= 9 and "-" not in text:
        raise ValueError(f"{field_name} 疑似原始联系方式，请先哈希或替换为内部引用")
    return text


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
