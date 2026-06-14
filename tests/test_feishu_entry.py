import json
from pathlib import Path

import pytest

from venus.feishu_entry import (
    FeishuConfig,
    normalize_feishu_message,
    parse_feishu_command,
    run_feishu_entry,
)


def test_feishu_config_defaults_are_venus_only(tmp_workspace):
    config = FeishuConfig(workspace_root=tmp_workspace)

    assert config.env_prefix == "VENUS_FEISHU_"
    assert config.agent_name == "venus"
    assert config.command_prefix == "/venus"
    assert config.dry_run is True
    assert config.storage_namespace == "venus_feishu"
    assert (
        config.default_input_paths["hotspot"]
        == tmp_workspace / "data" / "samples" / "hotspots.json"
    )
    assert (
        config.default_input_paths["product"]
        == tmp_workspace / "data" / "samples" / "products.json"
    )
    assert (
        config.default_input_paths["product-intel"]
        == tmp_workspace / "data" / "samples" / "product_intelligence.json"
    )
    assert (
        config.default_input_paths["comments"]
        == tmp_workspace / "data" / "samples" / "comments.json"
    )
    assert (
        config.default_input_paths["monitoring"]
        == tmp_workspace / "data" / "samples" / "competitors.json"
    )
    assert (
        config.default_input_paths["airtable"]
        == tmp_workspace / "data" / "samples" / "airtable_export.json"
    )
    assert (
        config.default_input_paths["agent-run"]
        == tmp_workspace / "data" / "samples" / "agent_run.json"
    )
    assert (
        config.default_input_paths["douyin"]
        == tmp_workspace / "data" / "samples" / "douyin_engagement.json"
    )
    assert (
        config.default_input_paths["wechat"]
        == tmp_workspace / "data" / "samples" / "wechat_private_domain.json"
    )
    assert (
        config.default_input_paths["commercial"]
        == tmp_workspace / "data" / "samples" / "commercial_strategy.json"
    )
    assert (
        config.default_input_paths["improvement"]
        == tmp_workspace / "data" / "samples" / "self_improvement.json"
    )
    assert (
        config.default_input_paths["production"]
        == tmp_workspace / "data" / "samples" / "video_production.json"
    )
    assert (
        config.default_input_paths["trend-scan"]
        == tmp_workspace / "data" / "samples" / "trend_scan.json"
    )


def test_feishu_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        FeishuConfig(
            workspace_root=tmp_workspace,
            env_prefix="XIAOLONGXIA_FEISHU_",
            storage_namespace="xiaolongxia_feishu",
        )


def test_normalize_feishu_message_accepts_top_level_text():
    payload = {
        "message_id": "msg-001",
        "chat_id": "chat-001",
        "sender_id": "owner-001",
        "timestamp": "2026-06-14T13:30:00+08:00",
        "text": "/venus hotspot",
    }

    message = normalize_feishu_message(payload)

    assert message.message_id == "msg-001"
    assert message.chat_id == "chat-001"
    assert message.sender_id == "owner-001"
    assert message.text == "/venus hotspot"
    assert message.raw_payload == payload


def test_parse_feishu_command_extracts_name_args_and_approval_level(tmp_workspace):
    config = FeishuConfig(workspace_root=tmp_workspace)
    message = normalize_feishu_message(
        {
            "message_id": "msg-002",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:31:00+08:00",
            "text": "/venus approve reply-123 yes",
        }
    )

    command = parse_feishu_command(message, config)

    assert command.name == "approve"
    assert command.args == ["reply-123", "yes"]
    assert command.requires_approval is True
    assert command.approval_level == 2
    assert command.source_message_id == "msg-002"


def test_run_feishu_entry_help_returns_card_draft(tmp_workspace):
    result = run_feishu_entry(
        {
            "message_id": "msg-help",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:32:00+08:00",
            "text": "/venus help",
        },
        workspace_root=tmp_workspace,
    )

    assert result["workflow"] == "feishu"
    assert result["command"]["name"] == "help"
    assert result["dry_run"] is True
    assert result["external_actions"] == []
    assert result["card"]["type"] == "status"
    assert "/venus hotspot" in result["card"]["summary"]
    assert "/venus monitoring" in result["card"]["summary"]
    assert "/venus airtable" in result["card"]["summary"]
    assert "/venus agent-run" in result["card"]["summary"]
    assert "/venus douyin" in result["card"]["summary"]
    assert "/venus wechat" in result["card"]["summary"]
    assert "/venus commercial" in result["card"]["summary"]
    assert "/venus improvement" in result["card"]["summary"]
    assert "/venus production" in result["card"]["summary"]
    assert "/venus trend-scan" in result["card"]["summary"]
    assert "/venus product-intel" in result["card"]["summary"]


def test_run_feishu_entry_status_redacts_secret_like_values(tmp_workspace):
    result = run_feishu_entry(
        {
            "message_id": "msg-status",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:33:00+08:00",
            "text": "/venus status",
            "app_secret": "secret-value",
        },
        workspace_root=tmp_workspace,
    )

    rendered = str(result)
    assert result["card"]["type"] == "status"
    assert "secret-value" not in rendered
    assert "VENUS_FEISHU_" in rendered
    assert result["external_actions"] == []


def test_run_feishu_entry_unknown_command_returns_safe_error(tmp_workspace):
    result = run_feishu_entry(
        {
            "message_id": "msg-unknown",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:34:00+08:00",
            "text": "/venus dance",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "unknown"
    assert result["card"]["type"] == "error"
    assert "Unsupported Venus command" in result["card"]["summary"]
    assert result["external_actions"] == []


def _write_sample_inputs(root: Path) -> None:
    samples = root / "data" / "samples"
    samples.mkdir(parents=True, exist_ok=True)
    (samples / "hotspots.json").write_text(
        json.dumps(
            [
                {
                    "topic": "早C晚A翻车",
                    "type": "controversy",
                    "freshness": 9,
                    "relevance": 10,
                    "controversy": 8,
                    "evidence": ["douyin-export-001"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "products.json").write_text(
        json.dumps(
            [
                {
                    "brand": "Example Skin",
                    "name": "Barrier Serum",
                    "filing_id": "粤G妆网备字20260001",
                    "category": "essence",
                    "claims": ["舒缓", "100%修复屏障"],
                    "ingredients": ["panthenol", "centella asiatica extract"],
                    "evidence": ["nmpa-sample-001"],
                    "controversies": ["达人质疑夸大修复"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "product_intelligence.json").write_text(
        json.dumps(
            {
                "source": "manual_product_dossier",
                "retrieved_at": "2026-06-14T16:00:00+08:00",
                "live_connector_requested": True,
                "product": {
                    "brand": "示例品牌",
                    "name": "屏障修护精华",
                    "filing_id": "国妆网备字20260001",
                    "manufacturer": "示例化妆品有限公司",
                    "claims": ["舒缓", "100%修复屏障"],
                    "brand_backing": [
                        {"type": "dermatologist_quote", "source": "品牌手册", "status": "unverified"},
                        {"type": "lab_collaboration", "source": "品牌发布会", "status": "verified"},
                    ],
                    "ingredients": [
                        {
                            "name": "烟酰胺",
                            "role": "brightening",
                            "risk": "medium",
                            "supplier": "原料商A",
                            "coa": "coa-niacinamide-001",
                            "test_report": "test-niacinamide-001",
                        },
                        {
                            "name": "视黄醇",
                            "role": "renewal",
                            "risk": "high",
                            "supplier": "原料商B",
                            "coa": "",
                            "test_report": "",
                        },
                    ],
                    "supplier_documents": [
                        {"supplier": "原料商A", "document": "coa-niacinamide-001", "status": "provided"},
                        {"supplier": "原料商B", "document": "", "status": "missing"},
                    ],
                    "test_reports": [
                        {"report_id": "test-niacinamide-001", "scope": "烟酰胺纯度", "status": "provided"},
                        {"report_id": "", "scope": "视黄醇稳定性", "status": "missing"},
                    ],
                    "controversies": [
                        {"source": "douyin_comment", "issue": "用户反馈刺痛", "severity": "medium"},
                        {"source": "creator_video", "issue": "达人质疑夸大修复", "severity": "high"},
                    ],
                    "evidence": [{"id": "nmpa-001", "type": "filing", "title": "备案查询"}],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "comments.json").write_text(
        json.dumps(
            [
                {"user": "a", "text": "敏感肌用了会不会烂脸？", "likes": 5},
                {"user": "b", "text": "是不是智商税", "likes": 7},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "competitors.json").write_text(
        json.dumps(
            {
                "competitors": [
                    {
                        "handle": "成分党A",
                        "videos": [
                            {
                                "title": "早C晚A翻车自查",
                                "topic": "早C晚A翻车",
                                "views": 120000,
                                "likes": 9800,
                                "comments": 1680,
                                "shares": 2400,
                                "completion_rate": 0.72,
                                "is_ad": False,
                            }
                        ],
                        "live_sessions": [{"duration_minutes": 60}],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "airtable_export.json").write_text(
        json.dumps(
            {
                "hotspots": [
                    {
                        "topic": "早C晚A翻车",
                        "type": "controversy",
                        "freshness": 9,
                        "relevance": 10,
                        "controversy": 8,
                        "evidence": ["douyin-export-001"],
                    }
                ],
                "products": [],
                "comments": [],
                "competitors": {"competitors": []},
                "approvals": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "agent_run.json").write_text(
        json.dumps(
            {
                "run_id": "venus-run-sample-001",
                "trigger": "feishu_dry_run",
                "requested_at": "2026-06-14T09:00:00+08:00",
                "requested_surfaces": [
                    "feishu_mobile_report",
                    "airtable_sync_review",
                    "douyin_comment_reply_queue",
                ],
                "hotspots": [
                    {
                        "topic": "早C晚A翻车",
                        "type": "controversy",
                        "freshness": 9,
                        "relevance": 10,
                        "controversy": 8,
                        "evidence": ["douyin-export-001"],
                    }
                ],
                "products": [],
                "comments": [{"id": "c1", "text": "敏感肌用了会不会烂脸？"}],
                "competitors": {"competitors": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "douyin_engagement.json").write_text(
        json.dumps(
            {
                "source": "manual_douyin_export",
                "retrieved_at": "2026-06-14T10:00:00+08:00",
                "videos": [
                    {
                        "video_id": "video-001",
                        "title": "早C晚A翻车自查",
                        "comments": [
                            {
                                "comment_id": "c1",
                                "text": "敏感肌用了会不会烂脸？",
                                "likes": 18,
                            },
                            {
                                "comment_id": "c2",
                                "text": "求平价替代",
                                "likes": 9,
                            },
                        ],
                    }
                ],
                "live_sessions": [
                    {
                        "session_id": "live-001",
                        "messages": [
                            {
                                "message_id": "l1",
                                "text": "刷酸爆皮了还能叠加这个吗？",
                                "likes": 3,
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "wechat_private_domain.json").write_text(
        json.dumps(
            {
                "source": "mini_program_export",
                "retrieved_at": "2026-06-14T11:00:00+08:00",
                "mini_program_sessions": [
                    {
                        "session_id": "mp-001",
                        "nickname": "敏敏",
                        "questions": [
                            {"question_id": "q1", "text": "屏障受损泛红，早C晚A还能继续吗？"},
                            {"question_id": "q2", "text": "我想加企业微信进群，让你帮我看产品搭配"},
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "commercial_strategy.json").write_text(
        json.dumps(
            {
                "source": "manual_commercial_brief",
                "retrieved_at": "2026-06-14T12:00:00+08:00",
                "qianchuan": {
                    "campaign_id": "qc-001",
                    "objective": "直播间成交",
                    "daily_budget": 3000,
                    "spent_today": 1800,
                    "roi": 1.4,
                    "target_roi": 2.0,
                    "audiences": ["敏感肌", "屏障修护"],
                    "creatives": [
                        {
                            "creative_id": "ad-001",
                            "title": "早C晚A翻车自查",
                            "completion_rate": 0.72,
                            "ctr": 0.035,
                            "conversion_rate": 0.018,
                        }
                    ],
                },
                "xingtu": {
                    "brief_id": "xt-001",
                    "brand": "示例品牌",
                    "product": "屏障修护精华",
                    "budget": 50000,
                    "requirements": ["突出100%修复屏障"],
                    "forbidden_claims": ["100%修复屏障"],
                    "deliverables": ["60秒短视频"],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "self_improvement.json").write_text(
        json.dumps(
            {
                "source": "manual_learning_export",
                "retrieved_at": "2026-06-14T13:00:00+08:00",
                "feedback_events": [
                    {
                        "event_id": "fb-001",
                        "workflow": "comments",
                        "decision": "edited",
                        "original": "这个产品一定能修复屏障",
                        "final": "这个产品可以作为屏障护理参考，但要看肤质和耐受。",
                        "reason": "去掉绝对功效承诺",
                    },
                    {
                        "event_id": "fb-002",
                        "workflow": "content",
                        "decision": "approved",
                        "original": "早C晚A翻车自查",
                        "final": "姐妹们，先看屏障状态，再谈早C晚A。",
                        "reason": "开头更像我的口语",
                        "metric": {"completion_rate": 0.74},
                    },
                ],
                "defect_reports": [
                    {
                        "defect_id": "bug-001",
                        "workflow": "douyin",
                        "severity": "high",
                        "description": "直播弹幕回复没有强调先停刺激组合",
                        "expected_guardrail": "高风险直播弹幕必须提醒暂停叠加刺激组合",
                    }
                ],
                "backup_checks": [
                    {
                        "target": "local-json-store",
                        "schedule": "daily",
                        "last_backup_at": "2026-06-14T08:00:00+08:00",
                        "last_verified_at": "",
                        "status": "missing_verification",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "video_production.json").write_text(
        json.dumps(
            {
                "source": "manual_content_brief",
                "retrieved_at": "2026-06-14T14:00:00+08:00",
                "topic": "早C晚A翻车自查",
                "format": "douyin_short_video",
                "duration_seconds": 45,
                "objective": "提升完播、评论和关注",
                "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
                "key_points": ["先判断屏障状态", "再看成分刺激叠加", "最后给评论区肤质自查问题"],
                "risk_notes": ["避免100%修复屏障这类绝对功效承诺"],
                "broll_assets": ["评论截图", "成分表特写", "备案截图"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "trend_scan.json").write_text(
        json.dumps(
            {
                "source": "manual_douyin_beauty_scan",
                "retrieved_at": "2026-06-14T15:00:00+08:00",
                "refresh_interval_minutes": 15,
                "live_connector_requested": True,
                "topics": [
                    {
                        "id": "topic-001",
                        "label": "早C晚A翻车",
                        "mentions": 320000,
                        "growth": 0.82,
                        "controversy": 0.78,
                        "evidence": ["douyin-hot-001"],
                    }
                ],
                "products": [
                    {"id": "prod-001", "label": "屏障修护精华", "mentions": 98000, "growth": 0.64, "controversy": 0.7}
                ],
                "creators": [
                    {"id": "creator-001", "handle": "成分党A", "mentions": 65000, "growth": 0.55, "controversy": 0.4}
                ],
                "comments": [
                    {"id": "comment-001", "text": "敏感肌用了会不会烂脸？", "likes": 1800, "growth": 0.8, "controversy": 0.9}
                ],
                "ingredients": [
                    {"id": "ing-001", "label": "视黄醇", "mentions": 120000, "growth": 0.7, "controversy": 0.85}
                ],
                "tags": [
                    {"id": "tag-001", "label": "早C晚A", "mentions": 260000, "growth": 0.74, "controversy": 0.6}
                ],
                "controversies": [
                    {"id": "risk-001", "label": "A醇叠加刷酸爆皮", "mentions": 88000, "growth": 0.71, "controversy": 0.92}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_run_feishu_entry_hotspot_routes_to_orchestrator(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-hotspot",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:35:00+08:00",
            "text": "/venus hotspot",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "hotspot"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "hotspot"
    assert result["card"]["result"]["result"]["top_topic"] == "早C晚A翻车"
    assert result["external_actions"] == []


def test_run_feishu_entry_product_routes_to_orchestrator(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-product",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:36:00+08:00",
            "text": "/venus product",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "product"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "product"
    assert "100%修复屏障" in result["card"]["result"]["result"]["forbidden_claims"]
    assert result["external_actions"] == []


def test_run_feishu_entry_product_intel_routes_to_precise_research_dossier(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-product-intel",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:36:30+08:00",
            "text": "/venus product-intel",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "product-intel"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "product_intel"
    assert result["card"]["result"]["result"]["summary"]["retrieval_task_count"] == 5
    assert result["card"]["result"]["result"]["claim_risk"]["risk_level"] == "high"
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_comments_keeps_reply_drafts_approval_gated(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-comments",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:37:00+08:00",
            "text": "/venus comments",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "comments"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "comments"
    assert result["card"]["result"]["result"]["approval_gated"] >= 1
    assert result["external_actions"] == []


def test_run_feishu_entry_monitoring_routes_to_orchestrator(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-monitoring",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:37:30+08:00",
            "text": "/venus monitoring",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "monitoring"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "monitoring"
    assert result["card"]["result"]["result"]["summary"]["top_account"] == "成分党A"
    assert result["external_actions"] == []


def test_run_feishu_entry_airtable_routes_to_orchestrator(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-airtable",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:37:45+08:00",
            "text": "/venus airtable",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "airtable"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "airtable"
    assert result["card"]["result"]["result"]["base"]["name"] == "Venus Ops"
    assert result["external_actions"] == []


def test_run_feishu_entry_douyin_routes_to_engagement_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-douyin",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:00+08:00",
            "text": "/venus douyin",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "douyin"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "douyin"
    assert result["card"]["result"]["result"]["summary"]["comment_count"] == 2
    assert result["card"]["result"]["result"]["summary"]["live_message_count"] == 1
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_wechat_routes_to_private_domain_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-wechat",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:30+08:00",
            "text": "/venus wechat",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "wechat"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "wechat"
    assert result["card"]["result"]["result"]["summary"]["question_count"] == 2
    assert result["card"]["result"]["result"]["summary"]["enterprise_wechat_handoff_count"] == 1
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_commercial_routes_to_ad_strategy_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-commercial",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:45+08:00",
            "text": "/venus commercial",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "commercial"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "commercial"
    assert result["card"]["result"]["result"]["summary"]["approval_gated_action_count"] == 3
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_improvement_routes_to_self_improvement_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-improvement",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:50+08:00",
            "text": "/venus improvement",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "improvement"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "improvement"
    assert result["card"]["result"]["result"]["summary"]["learning_candidate_count"] == 2
    assert result["card"]["result"]["result"]["summary"]["backup_issue_count"] == 1
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_production_routes_to_video_production_package(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-production",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:55+08:00",
            "text": "/venus production",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "production"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "production"
    assert result["card"]["result"]["result"]["summary"]["scene_count"] == 5
    assert result["card"]["result"]["result"]["summary"]["approval_gated_action_count"] == 2
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_trend_scan_routes_to_douyin_signal_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-trend-scan",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:57+08:00",
            "text": "/venus trend-scan",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "trend-scan"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "trend_scan"
    assert result["card"]["result"]["result"]["summary"]["signal_count"] == 7
    assert result["card"]["result"]["result"]["leaderboard"][0]["label"] == "早C晚A翻车"
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_agent_run_returns_approval_gated_plan(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-agent-run",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:40:00+08:00",
            "text": "/venus agent-run",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "agent-run"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "agent_run"
    assert result["card"]["result"]["result"]["run_id"] == "venus-run-sample-001"
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["card"]["result"]["result"]["approval_records"]
    assert result["external_actions"] == []


def test_run_feishu_entry_approve_records_intent_without_external_action(tmp_workspace):
    result = run_feishu_entry(
        {
            "message_id": "msg-approve",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:38:00+08:00",
            "text": "/venus approve reply-123 yes",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "approve"
    assert result["card"]["type"] == "approval_request"
    assert result["approval_records"][0]["action_type"] == "feishu_approval_intent"
    assert result["approval_records"][0]["approval_level"] == 2
    assert result["external_actions"] == []
