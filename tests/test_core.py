"""核心单元测试：接口契约一致性、隐私矩阵、审批幂等、日志脱敏、文案校验。"""
from __future__ import annotations

import io
import logging

import pytest

from venus.approval import IdempotentExecutor, InMemoryApprovalGate
from venus.contracts import (
    Action,
    ApprovalStatus,
    DataClass,
    Destination,
    LLMMessage,
    LLMProvider,
    Tagged,
)
from venus.llm import FakeLLMProvider
from venus.logging_setup import RedactingFormatter
from venus.modules.m1_hotspot import build_m1_hotspot_package, validate_copy
from venus.modules.m2_product_diligence import build_m2_product_diligence_report
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
