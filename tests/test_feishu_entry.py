from pathlib import Path

import pytest

from venus.feishu_entry import (
    FeishuConfig,
    normalize_feishu_message,
    parse_feishu_command,
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
