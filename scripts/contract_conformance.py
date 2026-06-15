"""维纳斯契约核对：确认实现仍以 contracts.py 为接口锚点。"""
from __future__ import annotations

from venus.approval import InMemoryApprovalGate
from venus.contracts import Action, ApprovalStatus, DataClass, LLMProvider, MemoryStore, Tagged
from venus.llm import FakeLLMProvider
from venus.modules.m1_hotspot import build_m1_hotspot_package, build_publish_action
from venus.modules.m2_product_diligence import build_m2_product_diligence_report
from venus.modules.m3_persona_memory import (
    InMemoryPersonaMemoryStore,
    build_m3_persona_learning_report,
    distill_persona_descriptor,
)
from venus.modules.m4_community import build_m4_community_report, build_reply_action
from venus.modules.m5_video_editing import build_m5_video_package, build_video_publish_action
from venus.modules.m6_private_domain import (
    build_m6_private_domain_report,
    build_wecom_add_contact_action,
)
from venus.modules.m7_ads import (
    build_campaign_approval_action,
    build_m7_ads_report,
    build_xingtu_accept_order_action,
)
from venus.modules.m8_benchmark import build_m8_benchmark_report
from venus.modules.m9_evolution import (
    build_data_delete_action,
    build_m9_evolution_report,
    build_policy_change_action,
)


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_llm_provider())
    failures.extend(_check_approval_gate_shape())
    failures.extend(_check_m1_contracts())
    failures.extend(_check_m2_contracts())
    failures.extend(_check_m3_contracts())
    failures.extend(_check_m4_contracts())
    failures.extend(_check_m5_contracts())
    failures.extend(_check_m6_contracts())
    failures.extend(_check_m7_contracts())
    failures.extend(_check_m8_contracts())
    failures.extend(_check_m9_contracts())

    if failures:
        print("contract-conformance: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("contract-conformance: PASS")
    return 0


def _check_llm_provider() -> list[str]:
    if isinstance(FakeLLMProvider(), LLMProvider):
        return []
    return ["FakeLLMProvider 不满足 LLMProvider Protocol"]


def _check_approval_gate_shape() -> list[str]:
    gate = InMemoryApprovalGate()
    required = ["submit", "resolve", "get"]
    missing = [name for name in required if not callable(getattr(gate, name, None))]
    if missing:
        return [f"InMemoryApprovalGate 缺少方法: {', '.join(missing)}"]
    action = Action(
        kind="publish_video",
        summary="发布",
        payload={"id": 1},
        idempotency_key="contract-check",
        data_class=DataClass.C1_INTERNAL,
    )
    req = gate.submit(action)
    resolved = gate.resolve(req.id, ApprovalStatus.APPROVED, "owner")
    again = gate.resolve(req.id, ApprovalStatus.REJECTED, "owner")
    if resolved.status != again.status:
        return ["ApprovalGate.resolve 非幂等"]
    return []


def _check_m1_contracts() -> list[str]:
    llm = FakeLLMProvider()
    source = Tagged(
        payload={"hotspots": [{"topic": "早C晚A翻车", "mentions": 100, "evidence": ["a", "b"]}]},
        data_class=DataClass.C0_PUBLIC,
    )
    package = build_m1_hotspot_package(source, llm)
    failures = []
    if not isinstance(package, Tagged):
        failures.append("M1 输出必须是 Tagged")
    if package.data_class != DataClass.C1_INTERNAL:
        failures.append("M1 输出 data_class 必须是 C1_INTERNAL")
    action = build_publish_action(package.payload["brief"])
    if not isinstance(action, Action):
        failures.append("build_publish_action 必须返回 Action")
    if not action.idempotency_key:
        failures.append("Action 必须带 idempotency_key")
    return failures


def _check_m2_contracts() -> list[str]:
    source = Tagged(
        payload={
            "product_name": "契约核对精华",
            "nmpa": {"verified": False, "source": "manual-contract-check"},
            "ingredients": [{"name": "烟酰胺", "sources": ["ingredient-db"], "impact": 0.2}],
        },
        data_class=DataClass.C0_PUBLIC,
    )
    report = build_m2_product_diligence_report(source)
    failures = []
    if not isinstance(report, Tagged):
        failures.append("M2 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL:
        failures.append("M2 输出 data_class 必须是 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M2 不应产生对外动作")
    risk = report.payload.get("risk") or {}
    if risk.get("method") != "weighted_evidence_strength_times_impact":
        failures.append("M2 风险评分必须给透明方法")
    nmpa = report.payload.get("nmpa_verification") or {}
    if not nmpa.get("tier_c_blocked"):
        failures.append("M2 NMPA 边界必须保留 Tier 限制")
    return failures


def _check_m3_contracts() -> list[str]:
    store = InMemoryPersonaMemoryStore()
    source = Tagged(
        payload={
            "raw_corpus": ["私有原始语料只留本地"],
            "values": ["先证据后建议"],
            "tone": ["口语、克制"],
            "events": [
                {
                    "id": "contract-m3",
                    "kind": "episodic",
                    "content": "外部真实信号：证据型脚本互动更好",
                    "source": "external_metric:script",
                    "confidence": 0.8,
                }
            ],
        },
        data_class=DataClass.C3_SECRET,
        pii=True,
    )
    descriptor = distill_persona_descriptor(source)
    report = build_m3_persona_learning_report(source, store)
    failures = []
    if not isinstance(store, MemoryStore):
        failures.append("M3 记忆实现必须满足 MemoryStore")
    if not isinstance(descriptor, Tagged):
        failures.append("M3 风格描述符必须是 Tagged")
    if descriptor.data_class != DataClass.C1_INTERNAL or descriptor.pii:
        failures.append("M3 C3 蒸馏输出必须降级为无 PII 的 C1")
    if not isinstance(report, Tagged):
        failures.append("M3 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL:
        failures.append("M3 报告输出 data_class 必须是 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M3 不应产生对外动作")
    if report.payload.get("slow_layer_policy") != "core_identity_changes_require_approval":
        failures.append("M3 慢层核心身份变更必须人审")
    return failures


def _check_m4_contracts() -> list[str]:
    source = Tagged(
        payload={
            "video_id": "contract-video",
            "comments": [
                {"id": "c1", "text": "敏感肌叠加刺痛怎么办", "like_count": 3},
                {"id": "c2", "text": "视黄醇和酸能不能一起用", "like_count": 2},
            ],
            "live_mode": True,
            "auto_send_barrage": True,
        },
        data_class=DataClass.C1_INTERNAL,
    )
    report = build_m4_community_report(source)
    action = build_reply_action(video_id="contract-video", comment_id="c1", draft=report.payload["reply_drafts"][0]["draft"])
    failures = []
    if not isinstance(report, Tagged):
        failures.append("M4 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL or report.pii:
        failures.append("M4 输出必须是无 PII 的 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M4 报告不应直接产生外部动作")
    if not isinstance(action, Action):
        failures.append("M4 回复动作必须是 Action")
    if action.kind != "reply_comment" or not action.idempotency_key:
        failures.append("M4 回复 Action 必须带 reply_comment 与 idempotency_key")
    if action.reversible:
        failures.append("M4 公开回复动作必须标为不可逆")
    live = report.payload.get("live_assist") or {}
    if not live.get("auto_send_blocked") or not live.get("tier_c_blocked"):
        failures.append("M4 必须阻止非官方弹幕自动发送")
    return failures


def _check_m5_contracts() -> list[str]:
    source = Tagged(
        payload={
            "script": {
                "topic": "契约核对短视频",
                "full_text": "千万别急着跟风，先看屏障状态。评论区留下肤质和产品名，关注我少踩坑。",
            },
            "assets": [{"id": "asset-1", "type": "video", "uri": "local://asset.mp4", "license": "owned", "authorized": True}],
        },
        data_class=DataClass.C1_INTERNAL,
    )
    package = build_m5_video_package(source)
    action = build_video_publish_action(project_id=package.payload["project_id"], platform="douyin")
    failures = []
    if not isinstance(package, Tagged):
        failures.append("M5 输出必须是 Tagged")
    if package.data_class != DataClass.C1_INTERNAL or package.pii:
        failures.append("M5 输出必须是无 PII 的 C1_INTERNAL")
    if package.payload.get("external_actions") != []:
        failures.append("M5 工程包不应直接产生外部动作")
    if (package.payload.get("authorization_gate") or {}).get("status") != "passed":
        failures.append("M5 必须通过素材授权门禁")
    if not package.payload.get("editable_project"):
        failures.append("M5 必须生成可编辑工程描述")
    if not isinstance(action, Action):
        failures.append("M5 发布动作必须是 Action")
    if action.kind != "publish_video" or not action.idempotency_key:
        failures.append("M5 发布 Action 必须带 publish_video 与 idempotency_key")
    if action.reversible:
        failures.append("M5 发布动作必须标为不可逆")
    return failures


def _check_m6_contracts() -> list[str]:
    source = Tagged(
        payload={
            "question": "契约核对：敏感肌早C晚A刺痛怎么办？",
            "consent": {"privacy_notice_accepted": True},
            "lead": {"lead_hash": "contract-lead", "skin_type": "sensitive"},
        },
        data_class=DataClass.C1_INTERNAL,
    )
    try:
        report = build_m6_private_domain_report(source)
        action = build_wecom_add_contact_action(lead_id="contract-lead", contact_ref="wecom-ref")
    except NotImplementedError:
        return ["M6 私域模块尚未实现"]

    failures = []
    if not isinstance(report, Tagged):
        failures.append("M6 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL or report.pii:
        failures.append("M6 输出必须是无 PII 的 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M6 报告不应直接产生外部动作")
    consent = report.payload.get("pipl_consent") or {}
    if not consent.get("requires_explicit_notice"):
        failures.append("M6 必须声明 PIPL 明示告知与同意")
    funnel = report.payload.get("funnel_dashboard") or {}
    if funnel.get("method") != "cohort_conversion_retention_payback":
        failures.append("M6 漏斗必须使用 cohort + 留存 + 回本周期方法")
    if not isinstance(action, Action):
        failures.append("M6 企微加客动作必须是 Action")
    if action.kind != "add_contact" or not action.idempotency_key:
        failures.append("M6 企微 Action 必须带 add_contact 与 idempotency_key")
    if action.reversible:
        failures.append("M6 加客户动作必须标为不可逆")
    return failures


def _check_m7_contracts() -> list[str]:
    source = Tagged(
        payload={
            "objective": {"budget_cap": 2000.0, "roas_floor": 3.0, "attribution_window_days": 3},
            "ad_groups": [
                {
                    "id": "contract-ad",
                    "stage": "active",
                    "learning_day": 8,
                    "spend": 500.0,
                    "gmv": 2000.0,
                    "orders": 10,
                    "impressions": 6000,
                    "clicks": 300,
                    "attribution_mature": True,
                }
            ],
            "xingtu_offer": {
                "order_id": "contract-xingtu",
                "brand": "契约核对品牌",
                "fee": 12000.0,
                "production_cost": 3000.0,
                "opportunity_cost": 2000.0,
                "audience_match": 0.8,
                "brand_safety": 0.9,
                "reputation_risk": 0.1,
                "compliance_risk": 0.1,
            },
        },
        data_class=DataClass.C2_SENSITIVE,
    )
    try:
        report = build_m7_ads_report(source)
        campaign = build_campaign_approval_action(plan_id=report.payload["plan_id"], budget=2000.0)
        xingtu = build_xingtu_accept_order_action(order_id="contract-xingtu", quoted_fee=12000.0)
    except NotImplementedError:
        return ["M7 投流模块尚未实现"]

    failures = []
    if not isinstance(report, Tagged):
        failures.append("M7 输出必须是 Tagged")
    if report.data_class != DataClass.C2_SENSITIVE or report.pii:
        failures.append("M7 输出必须是无 PII 的 C2_SENSITIVE")
    if report.payload.get("external_actions") != []:
        failures.append("M7 报告不应直接产生外部动作")
    policy = report.payload.get("optimization_policy") or {}
    if policy.get("objective") != "maximize_gmv_under_roas_constraint":
        failures.append("M7 必须体现预算/ROAS 约束下最大化 GMV")
    if policy.get("exploration_method") != "discounted_sliding_window_thompson_sampling":
        failures.append("M7 必须体现非平稳投放下的滑窗/折扣型探索")
    testing = report.payload.get("sequential_testing") or {}
    if testing.get("method") != "bayesian_sequential_with_predeclared_mde":
        failures.append("M7 A/B 必须使用预设 MDE 的序贯/贝叶斯检验")
    xingtu_guidance = report.payload.get("xingtu_guidance") or {}
    if xingtu_guidance.get("method") != "expected_value_minus_costs_risk_discounted":
        failures.append("M7 星图接单必须使用期望价值与风险折扣")
    for action in (campaign, xingtu):
        if not isinstance(action, Action):
            failures.append("M7 对外动作必须是 Action")
        elif not action.idempotency_key or action.reversible:
            failures.append("M7 对外动作必须不可逆且带 idempotency_key")
        elif action.data_class != DataClass.C2_SENSITIVE:
            failures.append("M7 投流/星图动作必须标记为 C2_SENSITIVE")
    return failures


def _check_m8_contracts() -> list[str]:
    source = Tagged(
        payload={
            "data_source": {"name": "contract-licensed-provider", "tier": "B", "authorized": True},
            "creators": [
                {
                    "creator_id": "contract-creator",
                    "handle": "契约对标样本",
                    "style_tags": ["evidence", "review"],
                    "metrics": {"engagement_rate": 0.06, "avg_views": 50000, "ad_post_ratio": 0.2},
                    "previous_metrics": {"engagement_rate": 0.05, "avg_views": 42000},
                    "videos": [{"id": "contract-video", "views": 52000, "completion_rate": 0.36, "ad": False}],
                    "live": {"sessions": 2, "avg_gpm": 3200, "peak_online": 1000},
                }
            ],
        },
        data_class=DataClass.C1_INTERNAL,
    )
    try:
        report = build_m8_benchmark_report(source)
    except NotImplementedError:
        return ["M8 对标模块尚未实现"]

    failures = []
    if not isinstance(report, Tagged):
        failures.append("M8 输出必须是 Tagged")
    if report.data_class != DataClass.C1_INTERNAL or report.pii:
        failures.append("M8 输出必须是无 PII 的 C1_INTERNAL")
    if report.payload.get("external_actions") != []:
        failures.append("M8 报告不应直接产生外部动作")
    source_boundary = report.payload.get("source_boundary") or {}
    if not source_boundary.get("tier_c_blocked"):
        failures.append("M8 必须声明 Tier C 阻断")
    matrix = report.payload.get("benchmark_matrix") or {}
    if matrix.get("method") != "percentile_trend_baseline_comparison":
        failures.append("M8 必须使用分位、趋势与基准比较方法")
    timeseries = report.payload.get("timeseries_sink") or {}
    if timeseries.get("table") != "venus_metric_timeseries":
        failures.append("M8 对标时序指标必须落 venus_metric_timeseries")
    polling = report.payload.get("polling_policy") or {}
    if polling.get("mode") != "near_real_time_configurable":
        failures.append("M8 必须体现近实时可配置轮询")
    return failures


def _check_m9_contracts() -> list[str]:
    source = Tagged(
        payload={
            "eval_runs": [
                {"module": "m4", "kpi": "reply_safety", "score": 0.72, "threshold": 0.85},
                {"module": "m7", "kpi": "roas_guardrail", "score": 0.78, "threshold": 0.85},
            ],
            "incidents": [{"module": "m4", "kind": "compliance_alert", "count": 2}],
            "candidate_changes": [
                {
                    "change_id": "prompt-m4-contract",
                    "category": "prompt_parameter",
                    "summary": "降低回复草稿医疗化表达",
                    "expected_gain": 0.05,
                    "rollback_ref": "prompt-m4-current",
                },
                {
                    "change_id": "core-identity-contract",
                    "category": "core_identity",
                    "summary": "修改核心人设",
                    "expected_gain": 0.1,
                },
            ],
            "backup": {
                "backup_id": "contract-backup",
                "copies": [
                    {
                        "id": "local-db",
                        "medium": "disk",
                        "location": "primary_cn",
                        "encrypted": True,
                        "checksum": "sha256:a",
                    },
                    {
                        "id": "object-store",
                        "medium": "object",
                        "location": "secondary_cn",
                        "encrypted": True,
                        "checksum": "sha256:b",
                    },
                    {
                        "id": "offline-archive",
                        "medium": "offline",
                        "location": "offline_cn",
                        "encrypted": True,
                        "checksum": "sha256:c",
                    },
                ],
                "restore_drill": {"status": "passed", "checksum_match": True, "sampled_restore_count": 2},
            },
        },
        data_class=DataClass.C2_SENSITIVE,
    )
    try:
        report = build_m9_evolution_report(source)
        policy = build_policy_change_action(change_id="core-identity-contract", category="core_identity")
        delete = build_data_delete_action(subject_ref="lead-hash-contract", reason="user_requested_erasure")
    except NotImplementedError:
        return ["M9 自进化与备份模块尚未实现"]

    failures = []
    if not isinstance(report, Tagged):
        failures.append("M9 输出必须是 Tagged")
    if report.data_class != DataClass.C2_SENSITIVE or report.pii:
        failures.append("M9 输出必须是无 PII 的 C2_SENSITIVE")
    if report.payload.get("external_actions") != []:
        failures.append("M9 报告不应直接产生外部动作")
    eval_sink = report.payload.get("eval_runs_sink") or {}
    if eval_sink.get("table") != "venus_eval_runs":
        failures.append("M9 评估记录必须落 venus_eval_runs")
    loop = report.payload.get("improvement_loop") or {}
    if loop.get("allowed_scope") != "authorized_and_privacy_matrix_compliant_only":
        failures.append("M9 自进化必须受授权与隐私矩阵约束")
    backup = report.payload.get("backup_plan") or {}
    if backup.get("strategy") != "3-2-1" or backup.get("status") != "restore_verified":
        failures.append("M9 备份必须体现 3-2-1、加密、校验和恢复演练")
    if not isinstance(policy, Action) or policy.kind != "change_governed_policy":
        failures.append("M9 高风险策略变更必须是 Action")
    elif not policy.payload.get("requires_approval") or not policy.payload.get("rollback_required"):
        failures.append("M9 高风险策略变更必须先审批且可回滚")
    if not isinstance(delete, Action) or delete.kind != "delete_data":
        failures.append("M9 数据删除必须是 Action")
    elif delete.reversible or not delete.payload.get("requires_approval"):
        failures.append("M9 数据删除必须不可逆且先审批")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
