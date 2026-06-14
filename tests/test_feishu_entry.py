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
