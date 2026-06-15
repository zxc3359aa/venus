"""核心单元测试：接口契约一致性、隐私矩阵、审批幂等、日志脱敏、文案校验。"""
from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta, timezone

import pytest

from venus.approval import IdempotentExecutor, InMemoryApprovalGate
from venus.contracts import (
    Action,
    ApprovalStatus,
    DataClass,
    Destination,
    LLMMessage,
    LLMProvider,
    MemoryItem,
    MemoryKind,
    Tagged,
)
from venus.connectors_feishu import PlatformInterfaceNotVerified, real_start
from venus.llm import FakeLLMProvider
from venus.logging_setup import RedactingFormatter
from venus.modules.m1_hotspot import build_m1_hotspot_package, validate_copy
from venus.modules.m2_product_diligence import build_m2_product_diligence_report
from venus.modules.m3_persona_memory import (
    InMemoryPersonaMemoryStore,
    build_m3_persona_learning_report,
    distill_persona_descriptor,
)
from venus.modules.m4_community import (
    build_m4_community_report,
    build_reply_action,
    validate_reply_draft,
)
from venus.modules.m5_video_editing import (
    build_m5_video_package,
    build_video_publish_action,
    validate_asset_authorizations,
)
from venus.modules.m6_private_domain import (
    build_m6_private_domain_report,
    build_wecom_add_contact_action,
    validate_miniprogram_answer,
)
from venus.modules.m7_ads import (
    build_campaign_approval_action,
    build_m7_ads_report,
    build_xingtu_accept_order_action,
    validate_ad_script,
)
from venus.modules.m8_benchmark import build_m8_benchmark_report, validate_benchmark_commentary
from venus.modules.m9_evolution import (
    build_data_delete_action,
    build_m9_evolution_report,
    build_policy_change_action,
    validate_evolution_proposal,
)
from venus.privacy import DefaultPrivacyFirewall, PrivacyError


# ---- 接口契约一致性（runtime_checkable Protocol） ----
def test_fake_llm_conforms_to_protocol():
    assert isinstance(FakeLLMProvider(), LLMProvider)


def test_fake_llm_is_deterministic():
    llm = FakeLLMProvider(scripted={"汇总": "固定输出"})
    a = llm.complete([LLMMessage("user", "请汇总")], max_tokens=64)
    b = llm.complete([LLMMessage("user", "请汇总")], max_tokens=64)
    assert a.text == b.text == "固定输出"


# ---- 隐私防火墙：数据流向矩阵（修订 A1 的运行期闭环） ----
def test_c3_blocked_from_cloud_llm():
    fw = DefaultPrivacyFirewall()
    persona = Tagged(payload={"语料": "x"}, data_class=DataClass.C3_SECRET, pii=True)
    assert fw.allow_egress(Destination.CLOUD_LLM, persona) is False
    with pytest.raises(PrivacyError):
        fw.redact(persona, Destination.CLOUD_LLM)  # C3 不可自动脱敏外发


def test_c0_allowed_to_cloud_llm():
    fw = DefaultPrivacyFirewall()
    pub = Tagged(payload="公开热点", data_class=DataClass.C0_PUBLIC)
    assert fw.allow_egress(Destination.CLOUD_LLM, pub) is True


def test_c2_redacts_to_c1_for_cloud():
    fw = DefaultPrivacyFirewall()
    data = Tagged(payload={"报价": 1000, "phone": "13800138000"}, data_class=DataClass.C2_SENSITIVE, pii=True)
    assert fw.allow_egress(Destination.CLOUD_LLM, data) is False  # REDACT, 非 ALLOW
    red = fw.redact(data, Destination.CLOUD_LLM)
    assert red.data_class == DataClass.C1_INTERNAL
    assert "phone" not in red.payload  # PII 字段被剥离


def test_destination_allowlist():
    fw = DefaultPrivacyFirewall()
    fw.assert_destination_allowlisted("https://api.openai.com/v1/chat/completions")
    with pytest.raises(PrivacyError):
        fw.assert_destination_allowlisted("https://evil.example.com/exfil")


def test_real_feishu_start_is_blocked_until_context7_verification():
    with pytest.raises(PlatformInterfaceNotVerified):
        real_start("app-id", "app-secret", lambda _: None)


# ---- 审批网关：幂等与过期 ----
def _action():
    return Action(
        kind="publish_video", summary="发布", payload={"id": 1},
        idempotency_key="k1", data_class=DataClass.C1_INTERNAL, reversible=False,
    )


def test_approval_resolve_is_idempotent():
    gate = InMemoryApprovalGate()
    req = gate.submit(_action())
    r1 = gate.resolve(req.id, ApprovalStatus.APPROVED, decided_by="owner")
    r2 = gate.resolve(req.id, ApprovalStatus.REJECTED, decided_by="other")  # 重复回调
    assert r1.status == ApprovalStatus.APPROVED
    assert r2.status == ApprovalStatus.APPROVED  # 幂等：不被二次改写
    assert len(gate.pushed) == 1


def test_approval_expiry():
    gate = InMemoryApprovalGate(ttl_seconds=-1)  # 立即过期
    req = gate.submit(_action())
    r = gate.resolve(req.id, ApprovalStatus.APPROVED, decided_by="owner")
    assert r.status == ApprovalStatus.EXPIRED


def test_idempotent_executor_runs_once():
    ex = IdempotentExecutor()
    calls = {"n": 0}

    def fn(action):
        calls["n"] += 1
        return "ok"

    a = _action()
    ex.execute(a, fn)
    ex.execute(a, fn)  # 同 idempotency_key
    assert calls["n"] == 1


# ---- 日志脱敏 ----
def test_logging_redacts_secret_and_phone():
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(RedactingFormatter("%(message)s"))
    logger = logging.getLogger("venus.test.redact")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info("app_secret=abcd1234secret 用户手机 13800138000")
    out = buf.getvalue()
    assert "abcd1234secret" not in out
    assert "13800138000" not in out
    assert "***" in out


# ---- 中文文案校验器 ----
def test_validate_copy_pass_and_fail():
    assert validate_copy("你知道吗？千万别踩坑，关注我，评论区扣1") == []
    issues = validate_copy("这是一段普通分享，关注我，评论区扣1")
    assert "缺少3秒钩子" in issues
    banned = validate_copy("你知道吗？这是全网最有效100%根治方法，关注，评论")
    assert any("广告法风险词" in i for i in banned)


def test_m1_hotspot_package_ranks_topics_and_outputs_valid_script():
    llm = FakeLLMProvider(scripted={"汇总要点成简报": "早C晚A争议升温：屏障受损用户最关心叠加刺激。"})
    source = Tagged(
        data_class=DataClass.C0_PUBLIC,
        payload={
            "hotspots": [
                {
                    "topic": "温和洁面",
                    "mentions": 30000,
                    "growth": 0.2,
                    "controversy": 0.1,
                    "evidence": ["source-a"],
                },
                {
                    "topic": "早C晚A翻车",
                    "mentions": 120000,
                    "growth": 0.8,
                    "controversy": 0.9,
                    "evidence": ["source-a", "source-b"],
                },
            ],
            "comments": ["敏感肌早C晚A会不会烂脸？", "刷酸后还能叠加 A 醇吗？"],
            "persona_descriptor": "先看屏障状态，证据和体验都要说清楚。",
        },
    )

    package = build_m1_hotspot_package(source, llm)

    assert package.data_class == DataClass.C1_INTERNAL
    assert package.pii is False
    assert package.payload["top_signal"]["topic"] == "早C晚A翻车"
    assert package.payload["top_signal"]["controversy_verified"] is True
    assert package.payload["script"]["topic"] == "早C晚A翻车"
    assert validate_copy(package.payload["script"]["full_text"]) == []
    assert package.payload["shooting_advice"]
    assert package.payload["external_actions"] == []


def test_m1_hotspot_package_marks_single_source_controversy_for_manual_cross_check():
    llm = FakeLLMProvider()
    source = Tagged(
        data_class=DataClass.C0_PUBLIC,
        payload={
            "hotspots": [
                {
                    "topic": "某成分争议",
                    "mentions": 90000,
                    "growth": 0.7,
                    "controversy": 0.95,
                    "evidence": ["single-source"],
                }
            ],
            "comments": [],
        },
    )

    package = build_m1_hotspot_package(source, llm)

    assert package.payload["top_signal"]["controversy_verified"] is False
    assert package.payload["top_signal"]["manual_cross_check_required"] is True


def test_m1_hotspot_package_rejects_c3_inputs_before_llm():
    llm = FakeLLMProvider()
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"hotspots": [{"topic": "我的私域用户语料", "mentions": 1}]},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m1_hotspot_package(source, llm)
    assert llm.calls == []


def test_m2_product_diligence_report_separates_fact_claim_and_inference():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "product_name": "维纳斯修护精华",
            "brand": "Venus Lab",
            "nmpa": {
                "registration_no": "国妆网备字20260001",
                "status": "active",
                "verified": True,
                "source": "https://www.nmpa.gov.cn/xxgk/ggtg/hzhpggtg/",
            },
            "ingredients": [
                {
                    "name": "烟酰胺",
                    "inci": "Niacinamide",
                    "position": 3,
                    "evidence_strength": 0.8,
                    "impact": 0.3,
                    "sources": ["ingredient-db"],
                },
                {
                    "name": "视黄醇",
                    "inci": "Retinol",
                    "position": 8,
                    "evidence_strength": 0.7,
                    "impact": 0.6,
                    "controversy": "敏感肌刺激风险",
                    "sources": ["cosmetic-review", "derm-paper"],
                },
            ],
            "supplier_reports": [
                {
                    "ingredient": "视黄醇",
                    "supplier": "授权原料商A",
                    "report_id": "COA-001",
                    "verified": False,
                    "source": "brand-provided-coa",
                }
            ],
            "brand_backing": [
                {
                    "claim": "品牌称拥有第三方检测报告",
                    "source": "brand-site",
                    "verified": False,
                }
            ],
            "incidents": [
                {
                    "title": "用户反馈刺痛",
                    "severity": 0.4,
                    "source": "public-comment-cluster",
                    "verified": False,
                }
            ],
        },
    )

    report = build_m2_product_diligence_report(source)

    assert report.data_class == DataClass.C1_INTERNAL
    assert report.pii is False
    assert report.payload["module"] == "m2_product_diligence"
    assert report.payload["product"]["name"] == "维纳斯修护精华"
    assert report.payload["nmpa_verification"]["status"] == "verified"
    assert report.payload["risk"]["method"] == "weighted_evidence_strength_times_impact"
    assert 0 < report.payload["risk"]["score"] < 1
    assert report.payload["risk"]["confidence_interval"][0] < report.payload["risk"]["score"]
    assert report.payload["facts"]
    assert report.payload["external_claims"]
    assert report.payload["inferences"]
    assert all("source" in item for section in ("facts", "external_claims") for item in report.payload[section])
    assert report.payload["medical_boundary"] == "no_medical_diagnosis_or_treatment_claims"
    assert report.payload["external_actions"] == []


def test_m2_product_diligence_report_marks_nmpa_manual_review_when_unverified():
    source = Tagged(
        data_class=DataClass.C0_PUBLIC,
        payload={
            "product_name": "同名精华",
            "nmpa": {
                "registration_no": "待查",
                "verified": False,
                "requires_captcha": True,
                "source": "https://www.nmpa.gov.cn/",
            },
            "ingredients": [],
        },
    )

    report = build_m2_product_diligence_report(source)

    assert report.payload["nmpa_verification"]["status"] == "manual_review_required"
    assert report.payload["nmpa_verification"]["tier_c_blocked"] is True
    assert "不绕验证码" in report.payload["nmpa_verification"]["note"]


def test_m2_product_diligence_report_rejects_c3_inputs():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"product_name": "私域用户追问过的产品", "ingredients": []},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m2_product_diligence_report(source)


def test_m3_distills_c3_persona_to_c1_descriptor_without_raw_corpus():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={
            "raw_corpus": ["我叫Chris，手机号13800138000，私域客户A问过屏障修护。"],
            "values": ["先看屏障，再谈成分功效"],
            "tone": ["口语、直接、讲证据"],
            "taboo_words": ["根治", "100%"],
        },
    )

    descriptor = distill_persona_descriptor(source)

    assert descriptor.data_class == DataClass.C1_INTERNAL
    assert descriptor.pii is False
    assert descriptor.payload["cloud_llm_safe"] is True
    rendered = str(descriptor.payload)
    assert "13800138000" not in rendered
    assert "私域客户A" not in rendered
    assert "raw_corpus" not in descriptor.payload
    assert descriptor.payload["external_actions"] == []


def test_m3_memory_store_consolidates_without_self_reinforcing_echo_chamber():
    store = InMemoryPersonaMemoryStore()
    since = datetime.now(timezone.utc) - timedelta(days=1)
    store.write(
        MemoryItem(
            id="self-accepted",
            kind=MemoryKind.EPISODIC,
            content="模型生成内容被采纳：以后都用同一个开头模板",
            data_class=DataClass.C1_INTERNAL,
            confidence=0.95,
            source="model_output_accepted",
            created_at=datetime.now(timezone.utc),
        )
    )
    store.write(
        MemoryItem(
            id="metric-signal",
            kind=MemoryKind.EPISODIC,
            content="外部真实信号：证据型开头完播率提升",
            data_class=DataClass.C1_INTERNAL,
            confidence=0.82,
            source="external_metric:douyin_video",
            created_at=datetime.now(timezone.utc),
        )
    )
    store.write(
        MemoryItem(
            id="owner-override",
            kind=MemoryKind.EPISODIC,
            content="我的显式设置：不要使用根治、100%这类绝对词",
            data_class=DataClass.C3_SECRET,
            confidence=1.0,
            source="explicit_owner_override",
            created_at=datetime.now(timezone.utc),
        )
    )

    report = store.consolidate(since)

    assert report.metrics["processed"] == 3
    assert "self-accepted" in report.rejected_feedback_loops
    candidate_ids = {item.id for item in report.candidate_items}
    assert "metric-signal:consolidated" in candidate_ids
    assert "owner-override:consolidated" in candidate_ids
    assert all(item.data_class != DataClass.C3_SECRET for item in report.candidate_items)


def test_m3_core_identity_changes_require_approval_before_slow_layer_update():
    store = InMemoryPersonaMemoryStore()
    store.write(
        MemoryItem(
            id="identity-change",
            kind=MemoryKind.EPISODIC,
            content="核心身份变更：以后改成强销售强逼单人设",
            data_class=DataClass.C3_SECRET,
            confidence=0.9,
            source="explicit_owner_override:core_identity",
            created_at=datetime.now(timezone.utc),
        )
    )

    report = store.consolidate(datetime.now(timezone.utc) - timedelta(hours=1))

    assert report.requires_approval
    assert report.requires_approval[0]["item_id"] == "identity-change"
    assert report.candidate_items == []


def test_m3_persona_learning_report_uses_tagged_contracts_and_no_external_actions():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={
            "values": ["敏感肌优先看屏障"],
            "tone": ["像真人聊天，不装专家"],
            "taboo_words": ["根治"],
            "events": [
                {
                    "id": "e1",
                    "kind": "episodic",
                    "content": "外部真实信号：评论区更爱成分证据拆解",
                    "source": "external_metric:comment_cluster",
                    "confidence": 0.8,
                }
            ],
        },
    )

    report = build_m3_persona_learning_report(source, InMemoryPersonaMemoryStore())

    assert report.data_class == DataClass.C1_INTERNAL
    assert report.pii is False
    assert report.payload["module"] == "m3_persona_memory"
    assert report.payload["descriptor"]["cloud_llm_safe"] is True
    assert report.payload["consolidation"]["metrics"]["processed"] == 1
    assert report.payload["slow_layer_policy"] == "core_identity_changes_require_approval"
    assert report.payload["external_actions"] == []


def test_m4_community_report_summarizes_comments_and_drafts_safe_replies():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "video_id": "video-001",
            "comments": [
                {
                    "id": "c1",
                    "text": "敏感肌用了早C晚A刺痛怎么办？",
                    "like_count": 18,
                    "author_hash": "u1",
                },
                {
                    "id": "c2",
                    "text": "可以直接根治闭口吗？",
                    "like_count": 7,
                    "author_hash": "u2",
                },
                {
                    "id": "c3",
                    "text": "成分表里视黄醇和酸能不能一起用？",
                    "like_count": 12,
                    "author_hash": "u3",
                },
            ],
            "persona_descriptor": "先问肤质和频率，再给证据化建议。",
        },
    )

    report = build_m4_community_report(source)

    assert report.data_class == DataClass.C1_INTERNAL
    assert report.pii is False
    assert report.payload["module"] == "m4_community"
    assert report.payload["comment_insights"]["total_comments"] == 3
    assert report.payload["comment_insights"]["top_intents"][0]["intent"] in {"safety_reaction", "ingredient_pairing"}
    assert report.payload["reply_drafts"]
    assert all(validate_reply_draft(item["draft"]) == [] for item in report.payload["reply_drafts"])
    assert "医疗诊断" in report.payload["safety_boundary"]["medical_boundary"]
    assert report.payload["external_actions"] == []


def test_m4_reply_action_is_idempotent_and_requires_approval():
    action = build_reply_action(
        video_id="video-001",
        comment_id="c1",
        draft="先暂停叠加，告诉我肤质、频率和具体产品，我按屏障状态帮你拆。",
    )

    assert isinstance(action, Action)
    assert action.kind == "reply_comment"
    assert action.idempotency_key == "reply-video-001-c1"
    assert action.reversible is False
    assert action.data_class == DataClass.C1_INTERNAL


def test_m4_rejects_c3_comment_payloads():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"comments": [{"id": "private", "text": "我的手机号 13800138000"}]},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m4_community_report(source)


def test_m4_live_barrage_is_advice_only_and_blocks_unofficial_auto_send():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "video_id": "live-001",
            "comments": [{"id": "b1", "text": "主播这个能不能刷酸后用？"}],
            "live_mode": True,
            "auto_send_barrage": True,
        },
    )

    report = build_m4_community_report(source)

    assert report.payload["live_assist"]["mode"] == "summary_and_suggested_talk_track"
    assert report.payload["live_assist"]["auto_send_blocked"] is True
    assert report.payload["live_assist"]["tier_c_blocked"] is True


def test_m5_video_package_builds_editable_timeline_and_caption_tracks():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "script": {
                "topic": "早C晚A翻车",
                "hook": "千万别急着跟风早C晚A，三秒先看你是不是高风险。",
                "body": "先看屏障状态，再看刺激叠加，最后看证据来源。",
                "comment_prompt": "评论区留下肤质、产品名和频率。",
                "follow_reason": "关注我，少踩一次护肤坑。",
                "full_text": "千万别急着跟风早C晚A，三秒先看你是不是高风险。先看屏障状态，再看刺激叠加，最后看证据来源。评论区留下肤质、产品名和频率。关注我，少踩一次护肤坑。",
            },
            "assets": [
                {
                    "id": "a-roll-1",
                    "type": "video",
                    "uri": "local://camera/intro.mp4",
                    "license": "owned",
                    "authorized": True,
                },
                {
                    "id": "font-1",
                    "type": "font",
                    "uri": "local://fonts/brand.otf",
                    "license": "owned",
                    "authorized": True,
                },
            ],
            "style_descriptor": "口语、克制、证据化。",
        },
    )

    package = build_m5_video_package(source)

    assert package.data_class == DataClass.C1_INTERNAL
    assert package.pii is False
    assert package.payload["module"] == "m5_video_editing"
    assert package.payload["editable_project"]["format"] == "venus_edit_decision_list"
    assert package.payload["timeline"]["duration_seconds"] > 0
    assert package.payload["timeline"]["shots"]
    assert package.payload["caption_track"]
    assert package.payload["cover_suggestions"]
    assert package.payload["title_suggestions"]
    assert package.payload["tag_suggestions"]
    assert package.payload["authorization_gate"]["status"] == "passed"
    assert package.payload["external_actions"] == []


def test_m5_blocks_unlicensed_assets_before_project_package():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "script": {"full_text": "你知道吗？先看屏障，再看成分。评论区告诉我肤质，关注我。"},
            "assets": [
                {
                    "id": "music-1",
                    "type": "music",
                    "uri": "local://music/trending.mp3",
                    "license": "",
                    "authorized": False,
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="素材授权"):
        build_m5_video_package(source)
    gate = validate_asset_authorizations(source.payload["assets"])
    assert gate["status"] == "blocked"
    assert gate["blocked_assets"][0]["id"] == "music-1"


def test_m5_rejects_c3_inputs_and_does_not_emit_publish_actions():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"script": {"full_text": "我的私域用户真实经历"}},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m5_video_package(source)


def test_m5_publish_action_is_idempotent_and_requires_approval():
    action = build_video_publish_action(project_id="m5-project-001", platform="douyin")

    assert isinstance(action, Action)
    assert action.kind == "publish_video"
    assert action.idempotency_key == "publish-douyin-m5-project-001"
    assert action.reversible is False
    assert action.data_class == DataClass.C1_INTERNAL


def test_m6_miniprogram_answer_requires_consent_and_has_medical_guardrails():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "question": "脸烂了是不是激素脸？能不能直接根治？",
            "consent": {"privacy_notice_accepted": False},
            "lead": {"lead_hash": "lead-hash-001", "skin_type": "sensitive"},
        },
    )

    report = build_m6_private_domain_report(source)

    assert report.data_class == DataClass.C1_INTERNAL
    assert report.pii is False
    assert report.payload["module"] == "m6_private_domain"
    assert report.payload["pipl_consent"]["status"] == "blocked_pending_consent"
    assert report.payload["pipl_consent"]["requires_explicit_notice"] is True
    assert validate_miniprogram_answer(report.payload["answer_draft"]) == []
    assert "医疗诊断" in report.payload["safety_boundary"]["medical_boundary"]
    assert report.payload["wecom_handoff"]["status"] == "blocked_pending_consent"
    assert report.payload["external_actions"] == []


def test_m6_builds_redacted_lead_and_cohort_funnel_when_consented():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "question": "敏感肌早C晚A刺痛怎么办？",
            "consent": {"privacy_notice_accepted": True, "marketing_opt_in": True},
            "lead": {
                "lead_hash": "lead-hash-002",
                "skin_type": "sensitive",
                "concerns": ["barrier", "retinol"],
            },
            "funnel_events": [
                {"cohort": "2026-06", "stage": "visit", "count": 100, "spend": 300.0},
                {"cohort": "2026-06", "stage": "qa_completed", "count": 64},
                {"cohort": "2026-06", "stage": "wecom_intent", "count": 36},
                {"cohort": "2026-06", "stage": "wecom_added", "count": 24},
                {"cohort": "2026-06", "stage": "purchase", "count": 9, "revenue": 900.0},
                {"cohort": "2026-06", "stage": "retained_7d", "count": 7},
            ],
        },
    )

    report = build_m6_private_domain_report(source)
    rendered = str(report.payload)

    assert report.payload["lead_record"]["table"] == "venus_leads"
    assert report.payload["lead_record"]["data_class"] == "C3_SECRET_AT_REST"
    assert report.payload["lead_record"]["stored_fields"] == ["lead_hash", "skin_type", "concerns", "consent"]
    assert "phone" not in rendered
    assert "name" not in rendered
    assert report.payload["funnel_dashboard"]["method"] == "cohort_conversion_retention_payback"
    assert report.payload["funnel_dashboard"]["cohorts"][0]["cohort"] == "2026-06"
    assert report.payload["funnel_dashboard"]["cohorts"][0]["payback_days"] is not None
    assert report.payload["wecom_handoff"]["status"] == "draft_ready"
    assert report.payload["external_actions"] == []


def test_m6_wecom_add_contact_action_is_idempotent_and_requires_approval():
    action = build_wecom_add_contact_action(lead_id="lead-hash-002", contact_ref="wecom-user-hash")

    assert isinstance(action, Action)
    assert action.kind == "add_contact"
    assert action.idempotency_key == "add-contact-lead-hash-002"
    assert action.reversible is False
    assert action.data_class == DataClass.C1_INTERNAL
    assert action.payload["platform"] == "wecom"
    assert action.payload["official_api_status"] == "pending_context7_verification"


def test_m6_rejects_c3_or_pii_private_lead_payloads():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"lead": {"phone": "13800138000"}, "question": "我的私域用户问题"},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m6_private_domain_report(source)


def test_m7_builds_budget_constrained_media_plan_with_learning_protection():
    source = Tagged(
        data_class=DataClass.C2_SENSITIVE,
        payload={
            "plan_id": "m7-live-20260615",
            "objective": {
                "primary": "maximize_gmv",
                "budget_cap": 3000.0,
                "roas_floor": 3.0,
                "attribution_window_days": 3,
            },
            "ad_groups": [
                {
                    "id": "creative-a",
                    "name": "直播间敏感肌人群",
                    "stage": "learning",
                    "learning_day": 2,
                    "spend": 600.0,
                    "gmv": 2100.0,
                    "orders": 12,
                    "impressions": 12000,
                    "clicks": 600,
                    "attribution_mature": False,
                },
                {
                    "id": "creative-b",
                    "name": "早C晚A兴趣人群",
                    "stage": "active",
                    "learning_day": 8,
                    "spend": 900.0,
                    "gmv": 3900.0,
                    "orders": 20,
                    "impressions": 15000,
                    "clicks": 900,
                    "attribution_mature": True,
                },
            ],
        },
    )

    report = build_m7_ads_report(source)

    assert report.data_class == DataClass.C2_SENSITIVE
    assert report.pii is False
    assert report.payload["module"] == "m7_ads"
    assert report.payload["optimization_policy"]["objective"] == "maximize_gmv_under_roas_constraint"
    assert report.payload["optimization_policy"]["secondary_constraint"]["roas_floor"] == 3.0
    assert report.payload["optimization_policy"]["exploration_method"] == "discounted_sliding_window_thompson_sampling"
    assert report.payload["optimization_policy"]["attribution_window_days"] == 3
    assert report.payload["external_actions"] == []

    decisions = {row["ad_group_id"]: row for row in report.payload["media_plan"]["ad_group_decisions"]}
    assert decisions["creative-a"]["decision"] == "protect_learning_phase"
    assert decisions["creative-a"]["can_pause_now"] is False
    assert decisions["creative-b"]["decision"] == "scale_with_guardrails"
    assert decisions["creative-b"]["proposed_budget"] > decisions["creative-b"]["current_spend"]


def test_m7_uses_sequential_testing_and_stop_loss_only_after_attribution_matures():
    source = Tagged(
        data_class=DataClass.C2_SENSITIVE,
        payload={
            "objective": {"budget_cap": 2000.0, "roas_floor": 2.5, "cpa_ceiling": 80.0},
            "ad_groups": [
                {
                    "id": "new-learning",
                    "stage": "learning",
                    "learning_day": 1,
                    "spend": 300.0,
                    "gmv": 100.0,
                    "orders": 1,
                    "impressions": 8000,
                    "clicks": 320,
                    "attribution_mature": False,
                },
                {
                    "id": "mature-loss",
                    "stage": "active",
                    "learning_day": 10,
                    "spend": 500.0,
                    "gmv": 900.0,
                    "orders": 4,
                    "impressions": 9000,
                    "clicks": 270,
                    "attribution_mature": True,
                },
            ],
            "experiments": [
                {"id": "hook-ab", "variant_a": {"orders": 18, "spend": 800}, "variant_b": {"orders": 21, "spend": 820}}
            ],
        },
    )

    report = build_m7_ads_report(source)

    decisions = {row["ad_group_id"]: row for row in report.payload["media_plan"]["ad_group_decisions"]}
    assert decisions["new-learning"]["decision"] == "protect_learning_phase"
    assert "attribution_not_mature" in decisions["new-learning"]["reasons"]
    assert decisions["mature-loss"]["decision"] == "pause_requires_approval"
    assert decisions["mature-loss"]["can_pause_now"] is True

    testing = report.payload["sequential_testing"]
    assert testing["method"] == "bayesian_sequential_with_predeclared_mde"
    assert testing["peek_policy"] == "no_continuous_peeking_decision_without_guardrails"
    assert testing["experiments"][0]["decision"] == "continue_collecting"
    assert report.payload["anomaly_alerts"][0]["requires_human_review"] is True


def test_m7_xingtu_quote_uses_expected_value_risk_discount_and_script_guardrails():
    source = Tagged(
        data_class=DataClass.C2_SENSITIVE,
        payload={
            "xingtu_offer": {
                "order_id": "xt-001",
                "brand": "理性护肤品牌",
                "fee": 18000.0,
                "production_cost": 3500.0,
                "opportunity_cost": 2500.0,
                "audience_match": 0.86,
                "brand_safety": 0.92,
                "reputation_risk": 0.12,
                "compliance_risk": 0.08,
                "brief": "敏感肌精华合作，不能承诺医疗效果。",
            },
            "persona_descriptor": "口语、证据先行，不夸大功效。",
        },
    )

    report = build_m7_ads_report(source)
    xingtu = report.payload["xingtu_guidance"]

    assert xingtu["method"] == "expected_value_minus_costs_risk_discounted"
    assert xingtu["order_id"] == "xt-001"
    assert xingtu["recommendation"] in {"accept_with_review", "negotiate", "reject"}
    assert xingtu["risk_discount"] > 0
    assert xingtu["quote_range"]["floor"] >= 6000
    assert validate_ad_script(xingtu["script_draft"]) == []
    assert "医疗诊断" in xingtu["script_draft"]


def test_m7_external_money_and_xingtu_commitments_are_idempotent_approval_actions():
    campaign = build_campaign_approval_action(plan_id="m7-live-20260615", budget=3000.0)
    xingtu = build_xingtu_accept_order_action(order_id="xt-001", quoted_fee=18000.0)

    assert isinstance(campaign, Action)
    assert campaign.kind == "create_campaign"
    assert campaign.idempotency_key == "create-campaign-m7-live-20260615"
    assert campaign.reversible is False
    assert campaign.data_class == DataClass.C2_SENSITIVE
    assert campaign.payload["requires_approval"] is True
    assert campaign.payload["official_api_status"] == "pending_context7_verification"

    assert isinstance(xingtu, Action)
    assert xingtu.kind == "accept_xingtu_order"
    assert xingtu.idempotency_key == "accept-xingtu-order-xt-001"
    assert xingtu.reversible is False
    assert xingtu.data_class == DataClass.C2_SENSITIVE
    assert xingtu.payload["requires_approval"] is True


def test_m7_rejects_c3_or_pii_ad_payloads():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"ad_groups": [{"id": "private-user", "phone": "13800138000"}]},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m7_ads_report(source)


def test_m8_builds_creator_matrix_with_percentiles_trends_and_source_boundaries():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "data_source": {"name": "licensed-panel", "tier": "B", "authorized": True},
            "polling": {"base_interval_minutes": 360, "burst_interval_minutes": 60},
            "creators": [
                {
                    "creator_id": "creator-a",
                    "handle": "屏障修护研究所",
                    "style_tags": ["evidence", "calm"],
                    "metrics": {"engagement_rate": 0.091, "avg_views": 82000, "ad_post_ratio": 0.18},
                    "previous_metrics": {"engagement_rate": 0.065, "avg_views": 56000},
                    "videos": [
                        {"id": "v-a1", "views": 91000, "completion_rate": 0.43, "ad": False},
                        {"id": "v-a2", "views": 73000, "completion_rate": 0.38, "ad": True},
                    ],
                    "live": {"sessions": 3, "avg_gpm": 6800, "peak_online": 2400},
                },
                {
                    "creator_id": "creator-b",
                    "handle": "成分党日记",
                    "style_tags": ["fast", "ingredient"],
                    "metrics": {"engagement_rate": 0.043, "avg_views": 36000, "ad_post_ratio": 0.42},
                    "previous_metrics": {"engagement_rate": 0.041, "avg_views": 34000},
                    "videos": [{"id": "v-b1", "views": 38000, "completion_rate": 0.31, "ad": True}],
                    "live": {"sessions": 1, "avg_gpm": 2100, "peak_online": 600},
                },
                {
                    "creator_id": "creator-c",
                    "handle": "敏感肌避坑站",
                    "style_tags": ["story", "review"],
                    "metrics": {"engagement_rate": 0.066, "avg_views": 59000, "ad_post_ratio": 0.09},
                    "previous_metrics": {"engagement_rate": 0.071, "avg_views": 62000},
                    "videos": [{"id": "v-c1", "views": 61000, "completion_rate": 0.36, "ad": False}],
                    "live": {"sessions": 0, "avg_gpm": 0, "peak_online": 0},
                },
            ],
        },
    )

    report = build_m8_benchmark_report(source)
    rows = report.payload["benchmark_matrix"]["creators"]
    row_a = next(row for row in rows if row["creator_id"] == "creator-a")

    assert report.data_class == DataClass.C1_INTERNAL
    assert report.pii is False
    assert report.payload["module"] == "m8_benchmark"
    assert report.payload["source_boundary"]["allowed_tiers"] == ["tier_a_official_products", "tier_b_licensed_provider"]
    assert report.payload["source_boundary"]["tier_c_blocked"] is True
    assert report.payload["polling_policy"]["mode"] == "near_real_time_configurable"
    assert report.payload["external_actions"] == []

    assert row_a["engagement_percentile"] == 100.0
    assert row_a["view_percentile"] == 100.0
    assert row_a["trend"] == "rising"
    assert row_a["ad_analysis"]["ad_post_count"] == 1
    assert row_a["live_analysis"]["sessions"] == 3
    assert report.payload["timeseries_sink"]["table"] == "venus_metric_timeseries"
    assert report.payload["timeseries_sink"]["records"][0]["data_class"] == "C1_INTERNAL"


def test_m8_detects_anomalies_and_outputs_non_defamatory_recommendations():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "data_source": {"name": "official-data-product", "tier": "A", "authorized": True},
            "creators": [
                {
                    "creator_id": "spike",
                    "handle": "直播爆发样本",
                    "metrics": {"engagement_rate": 0.07, "avg_views": 160000, "ad_post_ratio": 0.12},
                    "previous_metrics": {"engagement_rate": 0.05, "avg_views": 60000},
                    "videos": [{"id": "v1", "views": 190000, "completion_rate": 0.49, "ad": False}],
                    "live": {"sessions": 5, "avg_gpm": 9800, "peak_online": 5200},
                },
                {
                    "creator_id": "heavy-ad",
                    "handle": "高广告占比样本",
                    "metrics": {"engagement_rate": 0.035, "avg_views": 42000, "ad_post_ratio": 0.71},
                    "previous_metrics": {"engagement_rate": 0.055, "avg_views": 52000},
                    "videos": [{"id": "v2", "views": 41000, "completion_rate": 0.28, "ad": True}],
                    "live": {"sessions": 1, "avg_gpm": 1500, "peak_online": 500},
                },
            ],
        },
    )

    report = build_m8_benchmark_report(source)

    alerts = report.payload["anomaly_alerts"]
    assert any(alert["creator_id"] == "spike" and alert["kind"] == "view_velocity_spike" for alert in alerts)
    assert any(alert["creator_id"] == "heavy-ad" and alert["kind"] == "ad_load_risk" for alert in alerts)
    assert all(alert["requires_review"] is True for alert in alerts)
    assert validate_benchmark_commentary(report.payload["recommendations"][0]) == []
    assert "诽谤" in report.payload["safety_boundary"]["commentary_policy"]


def test_m8_supports_provider_switching_and_tracks_style_live_video_dimensions():
    source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "data_source": {"name": "灰豚授权版", "tier": "B", "authorized": True},
            "fallback_sources": ["official-data-product", "licensed-panel-b"],
            "creators": [
                {
                    "creator_id": "creator-style",
                    "handle": "风格矩阵样本",
                    "style_tags": ["lab", "comparison", "soft-selling"],
                    "metrics": {"engagement_rate": 0.052, "avg_views": 48000, "ad_post_ratio": 0.24},
                    "previous_metrics": {"engagement_rate": 0.048, "avg_views": 47000},
                    "videos": [
                        {"id": "style-1", "views": 50000, "completion_rate": 0.35, "ad": False},
                        {"id": "style-2", "views": 46000, "completion_rate": 0.33, "ad": True},
                    ],
                    "live": {"sessions": 2, "avg_gpm": 3600, "peak_online": 1200},
                }
            ],
        },
    )

    report = build_m8_benchmark_report(source)
    creator = report.payload["benchmark_matrix"]["creators"][0]

    assert report.payload["provider_switching"]["primary"] == "灰豚授权版"
    assert report.payload["provider_switching"]["fallbacks"] == ["official-data-product", "licensed-panel-b"]
    assert creator["style_analysis"]["tags"] == ["lab", "comparison", "soft-selling"]
    assert creator["video_analysis"]["video_count"] == 2
    assert creator["live_analysis"]["avg_gpm"] == 3600.0


def test_m8_rejects_tier_c_sources_and_c3_or_pii_payloads():
    tier_c_source = Tagged(
        data_class=DataClass.C1_INTERNAL,
        payload={
            "data_source": {"name": "unlicensed-export", "tier": "C", "authorized": False},
            "creators": [],
        },
    )
    private_source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"creators": [{"creator_id": "private", "phone": "13800138000"}]},
    )

    with pytest.raises(ValueError, match="Tier C"):
        build_m8_benchmark_report(tier_c_source)
    with pytest.raises(ValueError, match="C3"):
        build_m8_benchmark_report(private_source)


def test_m9_builds_system_health_eval_runs_and_controlled_improvement_loop():
    source = Tagged(
        data_class=DataClass.C2_SENSITIVE,
        payload={
            "eval_runs": [
                {"module": "m1", "kpi": "script_quality", "score": 0.82, "threshold": 0.75},
                {"module": "m4", "kpi": "reply_safety", "score": 0.62, "threshold": 0.8},
                {"module": "m7", "kpi": "roas_guardrail", "score": 0.71, "threshold": 0.85},
            ],
            "incidents": [
                {"module": "m4", "kind": "compliance_alert", "count": 2},
                {"module": "m7", "kind": "cost_anomaly", "count": 1},
            ],
            "candidate_changes": [
                {
                    "change_id": "prompt-m4-001",
                    "category": "prompt_parameter",
                    "summary": "降低回复草稿医疗化表达",
                    "expected_gain": 0.08,
                    "rollback_ref": "prompt-m4-v1",
                },
                {
                    "change_id": "core-identity-001",
                    "category": "core_identity",
                    "summary": "修改人设核心身份",
                    "expected_gain": 0.2,
                },
            ],
        },
    )

    report = build_m9_evolution_report(source)

    assert report.data_class == DataClass.C2_SENSITIVE
    assert report.pii is False
    assert report.payload["module"] == "m9_evolution"
    assert report.payload["system_health"]["status"] == "needs_attention"
    assert report.payload["eval_runs_sink"]["table"] == "venus_eval_runs"
    assert report.payload["eval_runs_sink"]["records"][1]["module"] == "m4"
    assert report.payload["weaknesses"][0]["module"] in {"m4", "m7"}
    assert (
        report.payload["improvement_loop"]["allowed_scope"]
        == "authorized_and_privacy_matrix_compliant_only"
    )
    assert report.payload["improvement_loop"]["auto_candidates"][0]["rollout"] == "canary_with_rollback"
    assert report.payload["improvement_loop"]["approval_required_changes"][0]["category"] == "core_identity"
    assert report.payload["external_actions"] == []


def test_m9_backup_plan_uses_321_encryption_checksums_and_restore_drill():
    source = Tagged(
        data_class=DataClass.C2_SENSITIVE,
        payload={
            "backup": {
                "backup_id": "backup-20260615",
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
                "schedule": {"incremental": "daily", "full": "weekly"},
                "restore_drill": {"status": "passed", "checksum_match": True, "sampled_restore_count": 3},
                "contains_personal_info": True,
                "data_residency": "cn",
            }
        },
    )

    report = build_m9_evolution_report(source)
    backup = report.payload["backup_plan"]

    assert backup["strategy"] == "3-2-1"
    assert backup["status"] == "restore_verified"
    assert backup["encrypted_copies"] == 3
    assert backup["media_count"] >= 2
    assert backup["offsite_or_offline_copy"] is True
    assert backup["schedule"] == {"incremental": "daily", "full": "weekly"}
    assert backup["restore_drill"]["status"] == "passed"
    assert backup["venus_backups_record"]["table"] == "venus_backups"
    assert backup["data_residency_policy"] == "personal_info_cn_or_assessed_before_cross_border"


def test_m9_high_risk_policy_and_delete_actions_are_idempotent_approval_actions():
    policy = build_policy_change_action(change_id="core-identity-001", category="core_identity")
    delete = build_data_delete_action(subject_ref="lead-hash-002", reason="user_requested_erasure")

    assert isinstance(policy, Action)
    assert policy.kind == "change_governed_policy"
    assert policy.idempotency_key == "policy-change-core-identity-001"
    assert policy.payload["requires_approval"] is True
    assert policy.payload["rollback_required"] is True
    assert policy.data_class == DataClass.C1_INTERNAL

    assert isinstance(delete, Action)
    assert delete.kind == "delete_data"
    assert delete.idempotency_key == "delete-data-lead-hash-002"
    assert delete.reversible is False
    assert delete.payload["subject_ref"] == "lead-hash-002"
    assert "phone" not in str(delete.payload)
    assert delete.payload["requires_approval"] is True


def test_m9_rejects_c3_or_pii_and_blocks_cloud_training_proposals():
    source = Tagged(
        data_class=DataClass.C3_SECRET,
        pii=True,
        payload={"eval_runs": [{"module": "m3", "raw_persona": "私有语料"}]},
    )

    with pytest.raises(ValueError, match="C3"):
        build_m9_evolution_report(source)

    issues = validate_evolution_proposal(
        {
            "change_id": "bad-training",
            "category": "model_training",
            "data_class": "C3_SECRET",
            "destination": "cloud_llm",
            "summary": "把我的语料上传云端训练",
        }
    )
    assert any("C3" in issue and "云" in issue for issue in issues)
