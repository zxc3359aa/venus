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
        config.default_input_paths["airtable-sync"]
        == tmp_workspace / "data" / "samples" / "airtable_sync_plan.json"
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
        config.default_input_paths["ecommerce"]
        == tmp_workspace / "data" / "samples" / "ecommerce.json"
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
        config.default_input_paths["memory"]
        == tmp_workspace / "data" / "samples" / "memory.json"
    )
    assert (
        config.default_input_paths["scheduler"]
        == tmp_workspace / "data" / "samples" / "scheduler.json"
    )
    assert (
        config.default_input_paths["connectors"]
        == tmp_workspace / "data" / "samples" / "connectors.json"
    )
    assert (
        config.default_input_paths["production"]
        == tmp_workspace / "data" / "samples" / "video_production.json"
    )
    assert (
        config.default_input_paths["content-eval"]
        == tmp_workspace / "data" / "samples" / "content_eval.json"
    )
    assert (
        config.default_input_paths["performance"]
        == tmp_workspace / "data" / "samples" / "performance.json"
    )
    assert (
        config.default_input_paths["evals"]
        == tmp_workspace / "data" / "samples" / "evals.json"
    )
    assert (
        config.default_input_paths["approvals"]
        == tmp_workspace / "data" / "samples" / "approvals.json"
    )
    assert (
        config.default_input_paths["approval-ledger"]
        == tmp_workspace / "data" / "samples" / "approval_ledger.json"
    )
    assert (
        config.default_input_paths["approval-archive"]
        == tmp_workspace / "data" / "samples" / "approval_archive.json"
    )
    assert (
        config.default_input_paths["action-outbox"]
        == tmp_workspace / "data" / "samples" / "action_outbox.json"
    )
    assert (
        config.default_input_paths["delivery-drafts"]
        == tmp_workspace / "data" / "samples" / "delivery_drafts.json"
    )
    assert (
        config.default_input_paths["delivery-status"]
        == tmp_workspace / "data" / "samples" / "delivery_status.json"
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
    assert "/venus airtable-sync" in result["card"]["summary"]
    assert "/venus agent-run" in result["card"]["summary"]
    assert "/venus douyin" in result["card"]["summary"]
    assert "/venus ecommerce" in result["card"]["summary"]
    assert "/venus wechat" in result["card"]["summary"]
    assert "/venus commercial" in result["card"]["summary"]
    assert "/venus improvement" in result["card"]["summary"]
    assert "/venus memory" in result["card"]["summary"]
    assert "/venus scheduler" in result["card"]["summary"]
    assert "/venus connectors" in result["card"]["summary"]
    assert "/venus production" in result["card"]["summary"]
    assert "/venus content-eval" in result["card"]["summary"]
    assert "/venus performance" in result["card"]["summary"]
    assert "/venus evals" in result["card"]["summary"]
    assert "/venus approvals" in result["card"]["summary"]
    assert "/venus approval-ledger" in result["card"]["summary"]
    assert "/venus approval-archive" in result["card"]["summary"]
    assert "/venus action-outbox" in result["card"]["summary"]
    assert "/venus delivery-drafts" in result["card"]["summary"]
    assert "/venus delivery-status" in result["card"]["summary"]
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
    (samples / "airtable_sync_plan.json").write_text(
        json.dumps(
            {
                "source": "manual_airtable_sync_plan",
                "workspace_root": str(root),
                "planned_at": "2026-06-15T11:20:00+08:00",
                "sync_requested": False,
                "approved_sync_review": False,
                "airtable_package": {
                    "base": {"name": "Venus Ops", "namespace": "venus_airtable"},
                    "tables": [
                        {
                            "name": "Hotspots",
                            "fields": [
                                {"name": "Name", "type": "singleLineText"},
                                {"name": "Topic", "type": "singleLineText"},
                            ],
                            "records": [
                                {"fields": {"Name": "早C晚A翻车", "Topic": "早C晚A翻车"}}
                            ],
                        }
                    ],
                },
                "connector_reviews": [
                    {
                        "connector_id": "airtable-ops",
                        "surface": "airtable",
                        "status": "ready",
                        "permissions_granted": ["base_read", "record_write"],
                        "audit_ready": True,
                        "rollback_ready": True,
                        "external_action_enabled": False,
                    }
                ],
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
    (samples / "ecommerce.json").write_text(
        json.dumps(
            {
                "source": "manual_douyin_shop_export",
                "retrieved_at": "2026-06-14T17:00:00+08:00",
                "live_connector_requested": True,
                "shop": {"shop_id": "shop-001", "name": "维纳斯护肤小店", "channel": "douyin_shop"},
                "products": [
                    {
                        "product_id": "sku-001",
                        "title": "屏障修护精华",
                        "price": 199,
                        "sale_price": 169,
                        "stock": 36,
                        "target_stock": 120,
                        "margin_rate": 0.42,
                        "commission_rate": 0.18,
                        "conversion_rate": 0.032,
                        "return_rate": 0.06,
                        "claim_risk": "high",
                        "evidence": ["shop-product-001"],
                    },
                    {
                        "product_id": "sku-002",
                        "title": "温和洁面",
                        "price": 89,
                        "sale_price": 79,
                        "stock": 320,
                        "target_stock": 80,
                        "margin_rate": 0.35,
                        "commission_rate": 0.12,
                        "conversion_rate": 0.018,
                        "return_rate": 0.18,
                        "claim_risk": "medium",
                        "evidence": ["shop-product-002"],
                    },
                ],
                "live_rooms": [
                    {
                        "session_id": "live-001",
                        "title": "屏障护理专场",
                        "planned_products": ["sku-001", "sku-002"],
                        "viewers": 18000,
                        "gmv": 128000,
                        "product_card_click_rate": 0.21,
                        "conversion_rate": 0.026,
                    }
                ],
                "promotions": [
                    {"promotion_id": "promo-001", "product_id": "sku-001", "type": "coupon", "discount": 30, "budget": 3000}
                ],
                "after_sales": [
                    {"product_id": "sku-001", "issue": "敏感肌刺痛咨询", "severity": "medium"},
                    {"product_id": "sku-002", "issue": "退货率偏高", "severity": "high"},
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
    (samples / "memory.json").write_text(
        json.dumps(
            {
                "source": "manual_memory_review",
                "retrieved_at": "2026-06-14T18:00:00+08:00",
                "current_memory": {
                    "version": "v3",
                    "principles": ["先看屏障状态"],
                    "style_phrases": ["姐妹们"],
                    "product_beliefs": ["成分要看浓度、配方和肤质"],
                    "content_rules": ["先抛出用户真实问题，再给专业判断"],
                    "banned_claims": ["100%修复屏障"],
                    "privacy_boundaries": ["不记录手机号、地址、订单号等直接个人信息"],
                },
                "learning_candidates": [
                    {
                        "candidate_id": "mem-001",
                        "category": "principles",
                        "proposed_rule": "先判断屏障状态，再谈功效、搭配和频率。",
                        "evidence": ["fb-001"],
                    },
                    {
                        "candidate_id": "mem-002",
                        "category": "style_phrases",
                        "proposed_rule": "姐妹们，先别急着跟风。",
                        "evidence": ["script-001"],
                    },
                    {
                        "candidate_id": "mem-003",
                        "category": "privacy_boundaries",
                        "proposed_rule": "用户联系方式 contact-token-001 不进入任何记忆。",
                        "evidence": ["privacy-001"],
                        "contains_personal_data": True,
                    },
                ],
                "approval_decisions": [
                    {"candidate_id": "mem-001", "decision": "approved", "reviewer": "owner"},
                    {"candidate_id": "mem-002", "decision": "pending", "reviewer": "owner"},
                    {"candidate_id": "mem-003", "decision": "approved", "reviewer": "owner"},
                ],
                "backup": {
                    "target": "local-memory-ledger",
                    "last_snapshot_version": "v3",
                    "last_backup_at": "2026-06-14T07:00:00+08:00",
                    "last_verified_at": "",
                    "status": "missing_verification",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "scheduler.json").write_text(
        json.dumps(
            {
                "source": "manual_scheduler_plan",
                "generated_at": "2026-06-14T18:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "live_scheduler_requested": True,
                "jobs": [
                    {
                        "job_id": "job-trend",
                        "workflow": "trend_scan",
                        "cadence_minutes": 15,
                        "last_run_at": "2026-06-14T18:00:00+08:00",
                        "priority": "high",
                        "connector_state": "ready",
                        "approval_level": 1,
                        "evidence": ["trend-schedule-001"],
                    },
                    {
                        "job_id": "job-monitoring",
                        "workflow": "monitoring",
                        "cadence_minutes": 60,
                        "last_run_at": "2026-06-14T17:00:00+08:00",
                        "priority": "medium",
                        "connector_state": "ready",
                        "approval_level": 1,
                        "evidence": ["monitoring-schedule-001"],
                    },
                    {
                        "job_id": "job-douyin",
                        "workflow": "douyin",
                        "cadence_minutes": 10,
                        "last_run_at": "2026-06-14T18:25:00+08:00",
                        "priority": "high",
                        "connector_state": "ready",
                        "approval_level": 3,
                        "evidence": ["douyin-schedule-001"],
                    },
                    {
                        "job_id": "job-ecommerce",
                        "workflow": "ecommerce",
                        "cadence_minutes": 30,
                        "last_run_at": "2026-06-14T17:40:00+08:00",
                        "priority": "high",
                        "connector_state": "missing_permission",
                        "approval_level": 3,
                        "evidence": ["shop-schedule-001"],
                    },
                    {
                        "job_id": "job-backup",
                        "workflow": "backup_verification",
                        "cadence_minutes": 1440,
                        "last_run_at": "2026-06-13T08:00:00+08:00",
                        "priority": "high",
                        "connector_state": "ready",
                        "approval_level": 2,
                        "evidence": ["backup-schedule-001"],
                    },
                    {
                        "job_id": "job-memory",
                        "workflow": "memory",
                        "cadence_minutes": 1440,
                        "last_run_at": "2026-06-14T08:00:00+08:00",
                        "priority": "medium",
                        "connector_state": "paused",
                        "approval_level": 3,
                        "evidence": ["memory-schedule-001"],
                    },
                ],
                "operator_channels": ["feishu_private"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "connectors.json").write_text(
        json.dumps(
            {
                "source": "manual_connector_review",
                "reviewed_at": "2026-06-14T19:00:00+08:00",
                "live_connector_requested": True,
                "connectors": [
                    {
                        "connector_id": "douyin-open",
                        "surface": "douyin",
                        "connector_type": "douyin_open_api",
                        "desired_workflows": ["trend_scan", "douyin"],
                        "status": "missing_permission",
                        "permissions_required": ["video_comment_read", "live_message_read"],
                        "permissions_granted": ["basic_profile"],
                        "secret_refs": ["VENUS_DOUYIN_CLIENT_ID"],
                        "audit_log": "missing",
                        "rollback": "not_configured",
                        "data_classes": ["public_comments", "creator_metrics"],
                        "approval_level": 3,
                        "evidence": ["douyin-app-001"],
                    },
                    {
                        "connector_id": "feishu-bot",
                        "surface": "feishu",
                        "connector_type": "feishu_bot",
                        "desired_workflows": ["feishu"],
                        "status": "ready",
                        "permissions_required": ["receive_message", "send_private_card"],
                        "permissions_granted": ["receive_message", "send_private_card"],
                        "secret_refs": ["VENUS_FEISHU_APP_ID"],
                        "audit_log": "ready",
                        "rollback": "configured",
                        "data_classes": ["private_operator_reports"],
                        "approval_level": 2,
                        "evidence": ["feishu-app-001"],
                    },
                    {
                        "connector_id": "qianchuan-ads",
                        "surface": "qianchuan",
                        "connector_type": "oceanengine_marketing_api",
                        "desired_workflows": ["commercial"],
                        "status": "missing_permission",
                        "permissions_required": ["ad_account_read", "budget_write"],
                        "permissions_granted": ["ad_account_read"],
                        "secret_refs": ["VENUS_QIANCHUAN_APP_ID"],
                        "audit_log": "ready",
                        "rollback": "not_configured",
                        "data_classes": ["ad_budget", "audience_segments"],
                        "approval_level": 4,
                        "evidence": ["qianchuan-app-001"],
                    },
                    {
                        "connector_id": "airtable-ops",
                        "surface": "airtable",
                        "connector_type": "airtable_api",
                        "desired_workflows": ["airtable"],
                        "status": "ready",
                        "permissions_required": ["base_read", "record_write"],
                        "permissions_granted": ["base_read", "record_write"],
                        "secret_refs": ["VENUS_AIRTABLE_BASE_ID"],
                        "audit_log": "ready",
                        "rollback": "configured",
                        "data_classes": ["operations_records"],
                        "approval_level": 2,
                        "evidence": ["airtable-base-001"],
                    },
                    {
                        "connector_id": "backup-store",
                        "surface": "backup",
                        "connector_type": "local_backup",
                        "desired_workflows": ["improvement", "memory"],
                        "status": "missing_verification",
                        "permissions_required": ["local_write", "restore_read"],
                        "permissions_granted": ["local_write", "restore_read"],
                        "secret_refs": [],
                        "audit_log": "ready",
                        "rollback": "configured",
                        "data_classes": ["local_memory_snapshots"],
                        "approval_level": 2,
                        "evidence": ["backup-store-001"],
                    },
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
    (samples / "content_eval.json").write_text(
        json.dumps(
            {
                "source": "manual_pre_publish_review",
                "evaluated_at": "2026-06-14T20:00:00+08:00",
                "topic": "早C晚A翻车自查",
                "objective": "提升完播、评论和关注",
                "live_publish_requested": True,
                "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
                "script_package": {
                    "hook": "姐妹们，早C晚A翻车自查，先别急着跟风，3秒看懂你是不是高风险。",
                    "opening": "今天不制造焦虑，直接用早C晚A翻车自查做自查。",
                    "body_segments": [
                        {"segment_id": "point-1", "spoken_line": "先判断屏障状态", "purpose": "risk_filter"},
                        {
                            "segment_id": "point-2",
                            "spoken_line": "再看成分刺激叠加，证据比情绪重要。",
                            "purpose": "evidence_check",
                        },
                        {
                            "segment_id": "point-3",
                            "spoken_line": "这个搭配能100%修复屏障。",
                            "purpose": "comment_trigger",
                        },
                    ],
                    "cta": "了解了吧",
                    "comment_prompt": "评论区留下肤质+产品名+使用频率，我按屏障、刺激叠加和证据帮你拆。",
                    "title_options": ["早C晚A翻车自查", "敏感肌先看这3点", "别再盲跟早C晚A"],
                },
                "shot_list": [
                    {"scene_id": "scene-1", "scene_type": "hook", "retention_goal": "first_three_seconds"},
                    {"scene_id": "scene-2", "scene_type": "problem_frame"},
                    {"scene_id": "scene-3", "scene_type": "evidence_check"},
                    {"scene_id": "scene-4", "scene_type": "decision_framework"},
                    {"scene_id": "scene-5", "scene_type": "comment_cta"},
                ],
                "publish_package": {
                    "caption": "早C晚A不是让你跟风，是先看肤质、耐受和证据。",
                    "hashtags": ["#早C晚A", "#护肤", "#屏障护理"],
                    "pinned_comment_draft": "评论区留下肤质+产品名+使用频率，我帮你拆风险。",
                },
                "evidence_ids": [],
                "risk_notes": ["避免100%修复屏障这类绝对功效承诺"],
                "forbidden_claims": ["100%修复屏障"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "performance.json").write_text(
        json.dumps(
            {
                "source": "manual_douyin_video_metrics",
                "analyzed_at": "2026-06-14T21:00:00+08:00",
                "live_metrics_requested": True,
                "targets": {
                    "completion_rate": 0.65,
                    "comment_rate": 0.03,
                    "follow_rate": 0.008,
                    "negative_feedback_rate": 0.015,
                },
                "videos": [
                    {
                        "video_id": "video-001",
                        "title": "早C晚A翻车自查",
                        "topic": "早C晚A翻车",
                        "published_at": "2026-06-14T10:00:00+08:00",
                        "views": 120000,
                        "completion_rate": 0.72,
                        "comment_rate": 0.042,
                        "follow_rate": 0.011,
                        "share_rate": 0.018,
                        "negative_feedback_rate": 0.006,
                        "content_eval_score": 87,
                        "content_eval_status": "blocked_by_claim_risk",
                        "hook_type": "controversy_self_check",
                        "cta_type": "skin_product_frequency_comment",
                        "persona_fit": 0.92,
                        "claim_risk": "medium",
                        "evidence": ["video-metric-001"],
                    },
                    {
                        "video_id": "video-002",
                        "title": "温和洁面怎么选",
                        "topic": "温和洁面",
                        "published_at": "2026-06-13T10:00:00+08:00",
                        "views": 68000,
                        "completion_rate": 0.54,
                        "comment_rate": 0.017,
                        "follow_rate": 0.004,
                        "share_rate": 0.006,
                        "negative_feedback_rate": 0.021,
                        "content_eval_score": 76,
                        "content_eval_status": "needs_revision",
                        "hook_type": "generic_tips",
                        "cta_type": "generic",
                        "persona_fit": 0.71,
                        "claim_risk": "low",
                        "evidence": ["video-metric-002"],
                    },
                    {
                        "video_id": "video-003",
                        "title": "屏障修护精华备案拆解",
                        "topic": "屏障修护精华",
                        "published_at": "2026-06-12T10:00:00+08:00",
                        "views": 92000,
                        "completion_rate": 0.68,
                        "comment_rate": 0.036,
                        "follow_rate": 0.009,
                        "share_rate": 0.014,
                        "negative_feedback_rate": 0.011,
                        "content_eval_score": 83,
                        "content_eval_status": "ready_for_manual_publish_review",
                        "hook_type": "evidence_breakdown",
                        "cta_type": "product_name_comment",
                        "persona_fit": 0.88,
                        "claim_risk": "low",
                        "evidence": ["video-metric-003"],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "evals.json").write_text(
        json.dumps(
            {
                "source": "manual_agent_run_eval",
                "evaluated_at": "2026-06-14T22:00:00+08:00",
                "live_autopilot_requested": True,
                "agent_run": {
                    "run_id": "venus-run-eval-001",
                    "executed_workflows": [
                        "trend_scan",
                        "hotspot",
                        "product_intel",
                        "comments",
                        "production",
                        "content_eval",
                        "performance",
                        "douyin",
                        "ecommerce",
                        "wechat",
                        "commercial",
                        "improvement",
                        "memory",
                        "scheduler",
                        "connectors",
                        "monitoring",
                        "airtable",
                    ],
                    "workflow_summaries": {
                        "content_eval": {
                            "publish_readiness_status": "blocked_by_claim_risk",
                            "blocking_issue_count": 1,
                            "approval_record_count": 2,
                        },
                        "performance": {
                            "winner_count": 2,
                            "underperformer_count": 1,
                            "calibration_rule_count": 3,
                            "approval_record_count": 2,
                        },
                        "connectors": {
                            "ready_connector_count": 2,
                            "blocked_connector_count": 3,
                            "high_risk_connector_count": 1,
                            "approval_record_count": 2,
                        },
                        "scheduler": {
                            "due_job_count": 3,
                            "blocked_job_count": 2,
                            "approval_gated_job_count": 1,
                            "approval_record_count": 2,
                        },
                        "memory": {
                            "blocked_sensitive_candidate_count": 1,
                            "approval_gated_action_count": 2,
                        },
                        "improvement": {
                            "backup_issue_count": 1,
                            "approval_gated_action_count": 4,
                        },
                    },
                    "action_plan": [
                        {
                            "action_type": "draft_short_video",
                            "approval_level": 1,
                            "execution_state": "ready_for_internal_review",
                            "external_action_enabled": False,
                        },
                        {
                            "action_type": "feishu_mobile_report",
                            "approval_level": 2,
                            "execution_state": "blocked_until_approved",
                            "external_action_enabled": False,
                        },
                        {
                            "action_type": "qianchuan_budget_review",
                            "approval_level": 4,
                            "execution_state": "blocked_until_approved",
                            "external_action_enabled": False,
                        },
                    ],
                    "approval_records": [
                        {"action_type": "feishu_mobile_report", "status": "pending"},
                        {"action_type": "qianchuan_budget_review", "status": "pending"},
                    ],
                    "external_actions": [],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "approvals.json").write_text(
        json.dumps(
            {
                "source": "manual_approval_export",
                "reviewed_at": "2026-06-14T22:30:00+08:00",
                "approval_records": [
                    {
                        "action_type": "venus_autopilot_enablement_review",
                        "approval_level": 4,
                        "draft": "Review autopilot before enabling live surfaces.",
                        "evidence_ids": ["connector_readiness"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T22:00:00+08:00",
                    },
                    {
                        "action_type": "qianchuan_budget_review",
                        "approval_level": 4,
                        "draft": "Review budget before changing spend.",
                        "evidence_ids": ["qianchuan-app-001"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T21:30:00+08:00",
                    },
                    {
                        "action_type": "douyin_comment_reply_queue",
                        "approval_level": 3,
                        "draft": "Review high-risk Douyin reply drafts.",
                        "evidence_ids": ["comment-001"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T21:10:00+08:00",
                    },
                    {
                        "action_type": "venus_content_publish_review",
                        "approval_level": 3,
                        "draft": "Review content publish package.",
                        "evidence_ids": ["content-001"],
                        "status": "rejected",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T20:40:00+08:00",
                    },
                    {
                        "action_type": "wechat_private_domain_handoff",
                        "approval_level": 2,
                        "draft": "Review Enterprise WeChat handoff.",
                        "evidence_ids": ["wechat-001"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T20:20:00+08:00",
                    },
                    {
                        "action_type": "feishu_mobile_report",
                        "approval_level": 2,
                        "draft": "Send private Feishu summary.",
                        "evidence_ids": ["run-001"],
                        "status": "approved",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T20:00:00+08:00",
                    },
                ],
                "requested_decisions": [
                    {
                        "action_type": "qianchuan_budget_review",
                        "decision": "approve",
                        "reason": "预算建议合理，但仍需二次确认。",
                        "reviewer": "owner",
                    },
                    {
                        "action_type": "feishu_mobile_report",
                        "decision": "needs_changes",
                        "reason": "摘要需要更短。",
                        "reviewer": "owner",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "approval_ledger.json").write_text(
        json.dumps(
            {
                "source": "manual_approval_ledger",
                "recorded_at": "2026-06-14T23:00:00+08:00",
                "write_requested": True,
                "approval_records": [
                    {
                        "action_type": "qianchuan_budget_review",
                        "approval_level": 4,
                        "draft": "Review budget before changing spend.",
                        "evidence_ids": ["qianchuan-app-001"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T21:30:00+08:00",
                    },
                    {
                        "action_type": "douyin_comment_reply_queue",
                        "approval_level": 3,
                        "draft": "Review high-risk Douyin reply drafts.",
                        "evidence_ids": ["comment-001"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T21:10:00+08:00",
                    },
                    {
                        "action_type": "feishu_mobile_report",
                        "approval_level": 2,
                        "draft": "Send private Feishu summary.",
                        "evidence_ids": ["run-001"],
                        "status": "approved",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T20:00:00+08:00",
                    },
                ],
                "requested_decisions": [
                    {
                        "action_type": "qianchuan_budget_review",
                        "decision": "approve",
                        "reason": "预算建议合理，但仍需二次确认。",
                        "reviewer": "owner",
                    },
                    {
                        "action_type": "douyin_comment_reply_queue",
                        "decision": "reject",
                        "reason": "回复语气还需要更克制。",
                        "reviewer": "owner",
                    },
                    {
                        "action_type": "feishu_mobile_report",
                        "decision": "needs_changes",
                        "reason": "摘要需要更短。",
                        "reviewer": "owner",
                    },
                ],
                "existing_ledger_entries": [
                    {
                        "decision_id": "feishu_mobile_report-needs_changes-owner-feishu_mobile_report-20260614-2000000800",
                        "action_type": "feishu_mobile_report",
                        "decision": "needs_changes",
                        "reviewer": "owner",
                        "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "approval_archive.json").write_text(
        json.dumps(
            {
                "source": "manual_approval_archive",
                "recorded_at": "2026-06-14T23:20:00+08:00",
                "workspace_root": str(root),
                "archive_requested": False,
                "approved_ledger_write_review": False,
                "write_requested": True,
                "approval_records": [
                    {
                        "action_type": "douyin_comment_reply_queue",
                        "approval_level": 3,
                        "draft": "Review high-risk Douyin reply drafts.",
                        "evidence_ids": ["comment-001"],
                        "status": "pending",
                        "reviewer": "owner",
                        "created_at": "2026-06-14T21:10:00+08:00",
                    }
                ],
                "requested_decisions": [
                    {
                        "action_type": "douyin_comment_reply_queue",
                        "decision": "reject",
                        "reason": "回复语气还需要更克制。",
                        "reviewer": "owner",
                    }
                ],
                "existing_ledger_entries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "action_outbox.json").write_text(
        json.dumps(
            {
                "source": "manual_action_outbox",
                "workspace_root": str(root),
                "queued_at": "2026-06-14T23:40:00+08:00",
                "execution_requested": False,
                "approved_execution_review": False,
                "action_plan": [
                    {
                        "action_id": "feishu-report-001",
                        "action_type": "feishu_mobile_report",
                        "surface": "feishu",
                        "approval_level": 2,
                        "draft": "Prepare a private Feishu card summary.",
                        "external_action_enabled": False,
                    }
                ],
                "archived_decisions": [
                    {
                        "decision_id": "feishu_mobile_report-approve-owner-feishu_mobile_report-20260614-2000000800",
                        "action_type": "feishu_mobile_report",
                        "decision": "approve",
                        "reviewer": "owner",
                        "approval_level": 2,
                        "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                        "archive_state": "archived",
                        "record_state": "ready_for_local_ledger_review",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "delivery_drafts.json").write_text(
        json.dumps(
            {
                "source": "manual_delivery_drafts",
                "workspace_root": str(root),
                "drafted_at": "2026-06-15T09:10:00+08:00",
                "delivery_requested": False,
                "approved_delivery_review": False,
                "outbox_items": [
                    {
                        "outbox_id": "outbox-feishu_mobile_report-feishu-report-001-decision-001",
                        "action_id": "feishu-report-001",
                        "action_type": "feishu_mobile_report",
                        "surface": "feishu",
                        "approval_level": 2,
                        "decision_id": "decision-001",
                        "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                        "reviewer": "owner",
                        "draft": "Prepare a private Feishu card summary.",
                        "queued_at": "2026-06-14T23:40:00+08:00",
                        "execution_state": "queued_local_outbox",
                        "delivery_state": "local_manual_dispatch_required",
                        "external_action_enabled": False,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (samples / "delivery_status.json").write_text(
        json.dumps(
            {
                "source": "manual_delivery_status",
                "workspace_root": str(root),
                "recorded_at": "2026-06-15T10:20:00+08:00",
                "status_update_requested": False,
                "approved_status_review": False,
                "draft_records": [
                    {
                        "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                        "outbox_id": "outbox-feishu_mobile_report-feishu-report-001-decision-001",
                        "action_id": "feishu-report-001",
                        "action_type": "feishu_mobile_report",
                        "artifact_type": "feishu_card_draft",
                        "target_surface": "feishu",
                        "dispatch_state": "local_review_required",
                        "external_action_enabled": False,
                    }
                ],
                "status_events": [
                    {
                        "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                        "delivery_status": "manual_dispatch_completed",
                        "reviewer": "owner",
                        "event_time": "2026-06-15T10:00:00+08:00",
                        "notes": "Copied the private Feishu card manually.",
                        "evidence_ids": ["manual-feishu-001"],
                        "external_action_enabled": False,
                    }
                ],
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


def test_run_feishu_entry_airtable_sync_routes_to_local_sync_plan(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-airtable-sync",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-15T11:21:00+08:00",
            "text": "/venus airtable-sync",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "airtable-sync"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "airtable_sync_plan"
    assert result["card"]["result"]["result"]["summary"]["planned_count"] == 0
    assert (
        result["card"]["result"]["result"]["sync_state"]
        == "blocked_sync_not_requested"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []
    assert not (tmp_workspace / "data" / "venus" / "airtable_sync_plans.json").exists()


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


def test_run_feishu_entry_ecommerce_routes_to_shop_operations_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-ecommerce",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:10+08:00",
            "text": "/venus ecommerce",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "ecommerce"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "ecommerce"
    assert result["card"]["result"]["result"]["summary"]["product_count"] == 2
    assert result["card"]["result"]["result"]["summary"]["approval_gated_action_count"] == 3
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


def test_run_feishu_entry_memory_routes_to_versioned_memory_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-memory",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:40+08:00",
            "text": "/venus memory",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "memory"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "memory"
    assert result["card"]["result"]["result"]["summary"]["proposed_version"] == "v4"
    assert result["card"]["result"]["result"]["summary"]["proposed_change_count"] == 1
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_scheduler_routes_to_24h_run_plan(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-scheduler",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:45+08:00",
            "text": "/venus scheduler",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "scheduler"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "scheduler"
    assert result["card"]["result"]["result"]["summary"]["due_job_count"] == 3
    assert result["card"]["result"]["result"]["summary"]["blocked_job_count"] == 2
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_connectors_routes_to_connector_audit_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-connectors",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:39:50+08:00",
            "text": "/venus connectors",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "connectors"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "connectors"
    assert result["card"]["result"]["result"]["summary"]["ready_connector_count"] == 2
    assert result["card"]["result"]["result"]["summary"]["blocked_connector_count"] == 3
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


def test_run_feishu_entry_content_eval_routes_to_growth_and_safety_gate(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-content-eval",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:40:10+08:00",
            "text": "/venus content-eval",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "content-eval"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "content_eval"
    assert result["card"]["result"]["result"]["summary"]["overall_score"] == 87
    assert result["card"]["result"]["result"]["publish_readiness"]["status"] == "blocked_by_claim_risk"
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_performance_routes_to_content_calibration_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-performance",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:40:30+08:00",
            "text": "/venus performance",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "performance"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "performance"
    assert result["card"]["result"]["result"]["summary"]["winner_count"] == 2
    assert result["card"]["result"]["result"]["leaderboard"][0]["video_id"] == "video-001"
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_evals_routes_to_agent_gate_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-evals",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:40:45+08:00",
            "text": "/venus evals",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "evals"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "evals"
    assert (
        result["card"]["result"]["result"]["summary"]["readiness_status"]
        == "blocked_by_connector_readiness"
    )
    assert result["card"]["result"]["result"]["failed_gates"][0]["gate_id"] == "connector_readiness"
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_approvals_routes_to_manual_review_inbox(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-approvals",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:41:00+08:00",
            "text": "/venus approvals",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "approvals"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "approvals"
    assert result["card"]["result"]["result"]["summary"]["pending_count"] == 4
    assert (
        result["card"]["result"]["result"]["priority_queue"][0]["action_type"]
        == "venus_autopilot_enablement_review"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_approval_ledger_routes_to_decision_ledger_draft(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-approval-ledger",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:41:15+08:00",
            "text": "/venus approval-ledger",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "approval-ledger"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "approval_ledger"
    assert result["card"]["result"]["result"]["summary"]["new_entry_count"] == 2
    assert (
        result["card"]["result"]["result"]["duplicate_intents"][0]["action_type"]
        == "feishu_mobile_report"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []


def test_run_feishu_entry_approval_archive_routes_to_local_archive_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-approval-archive",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:41:25+08:00",
            "text": "/venus approval-archive",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "approval-archive"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "approval_archive"
    assert result["card"]["result"]["result"]["summary"]["archived_count"] == 0
    assert (
        result["card"]["result"]["result"]["archive_state"]
        == "blocked_archive_not_requested"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []
    assert not (tmp_workspace / "data" / "venus" / "approval_decision_ledger.json").exists()


def test_run_feishu_entry_action_outbox_routes_to_local_outbox_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-action-outbox",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-14T13:41:35+08:00",
            "text": "/venus action-outbox",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "action-outbox"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "action_outbox"
    assert result["card"]["result"]["result"]["summary"]["queued_count"] == 0
    assert (
        result["card"]["result"]["result"]["outbox_state"]
        == "blocked_execution_not_requested"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []
    assert not (tmp_workspace / "data" / "venus" / "action_outbox.json").exists()


def test_run_feishu_entry_delivery_drafts_routes_to_local_delivery_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-delivery-drafts",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-15T09:11:00+08:00",
            "text": "/venus delivery-drafts",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "delivery-drafts"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "delivery_drafts"
    assert result["card"]["result"]["result"]["summary"]["drafted_count"] == 0
    assert (
        result["card"]["result"]["result"]["delivery_state"]
        == "blocked_delivery_not_requested"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []
    assert not (tmp_workspace / "data" / "venus" / "delivery_drafts.json").exists()


def test_run_feishu_entry_delivery_status_routes_to_local_status_report(tmp_workspace):
    _write_sample_inputs(tmp_workspace)

    result = run_feishu_entry(
        {
            "message_id": "msg-delivery-status",
            "chat_id": "chat-001",
            "sender_id": "owner-001",
            "timestamp": "2026-06-15T10:21:00+08:00",
            "text": "/venus delivery-status",
        },
        workspace_root=tmp_workspace,
    )

    assert result["command"]["name"] == "delivery-status"
    assert result["card"]["type"] == "report"
    assert result["card"]["result"]["workflow"] == "delivery_status"
    assert result["card"]["result"]["result"]["summary"]["recorded_count"] == 0
    assert (
        result["card"]["result"]["result"]["status_state"]
        == "blocked_status_not_requested"
    )
    assert result["card"]["result"]["result"]["external_actions"] == []
    assert result["external_actions"] == []
    assert not (tmp_workspace / "data" / "venus" / "delivery_status.json").exists()


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
