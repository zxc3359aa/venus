from __future__ import annotations

import shlex
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


COMMAND_APPROVAL_LEVELS = {
    "help": 0,
    "status": 0,
    "hotspot": 1,
    "product": 1,
    "comments": 1,
    "approve": 2,
}


@dataclass(frozen=True)
class FeishuConfig:
    workspace_root: Path
    env_prefix: str = "VENUS_FEISHU_"
    agent_name: str = "venus"
    command_prefix: str = "/venus"
    dry_run: bool = True
    allowed_sender_ids: tuple[str, ...] = ()
    storage_namespace: str = "venus_feishu"
    default_input_paths: dict[str, Path] = field(init=False)

    def __post_init__(self) -> None:
        root = Path(self.workspace_root)
        object.__setattr__(self, "workspace_root", root)
        object.__setattr__(
            self,
            "default_input_paths",
            {
                "hotspot": root / "data" / "samples" / "hotspots.json",
                "product": root / "data" / "samples" / "products.json",
                "comments": root / "data" / "samples" / "comments.json",
            },
        )
        self.validate_isolation()

    def validate_isolation(self) -> None:
        values = [
            self.env_prefix,
            self.agent_name,
            self.command_prefix,
            self.storage_namespace,
            str(self.workspace_root),
        ]
        lowered = " ".join(values).lower()
        if "xiaolongxia" in lowered or "小龙虾" in lowered:
            raise ValueError("Venus Feishu config must not reference Xiaolongxia")
        if not self.env_prefix.startswith("VENUS_FEISHU_"):
            raise ValueError("Venus Feishu env_prefix must start with VENUS_FEISHU_")
        if self.command_prefix != "/venus":
            raise ValueError("Venus Feishu command_prefix must be /venus")
        if not self.dry_run:
            raise ValueError("Venus Feishu entry must run in dry-run mode")


@dataclass(frozen=True)
class FeishuMessage:
    message_id: str
    chat_id: str
    sender_id: str
    text: str
    timestamp: str
    raw_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeishuCommand:
    name: str
    args: list[str]
    requires_approval: bool
    approval_level: int
    source_message_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_feishu_message(payload: dict[str, Any]) -> FeishuMessage:
    text = _extract_text(payload)
    return FeishuMessage(
        message_id=str(
            payload.get("message_id")
            or payload.get("message", {}).get("message_id")
            or "local-message"
        ),
        chat_id=str(
            payload.get("chat_id")
            or payload.get("message", {}).get("chat_id")
            or "local-chat"
        ),
        sender_id=str(
            payload.get("sender_id")
            or payload.get("sender", {}).get("sender_id", {}).get("open_id")
            or "local-sender"
        ),
        text=text,
        timestamp=str(payload.get("timestamp") or payload.get("event_time") or "local-time"),
        raw_payload=payload,
    )


def parse_feishu_command(message: FeishuMessage, config: FeishuConfig) -> FeishuCommand:
    if not message.text.strip().startswith(config.command_prefix):
        raise ValueError("Message does not start with /venus")
    parts = shlex.split(message.text.strip())
    if len(parts) == 1:
        name = "help"
        args: list[str] = []
    else:
        name = parts[1].lower()
        args = parts[2:]
    if name not in COMMAND_APPROVAL_LEVELS:
        name = "unknown"
    approval_level = COMMAND_APPROVAL_LEVELS.get(name, 0)
    return FeishuCommand(
        name=name,
        args=args,
        requires_approval=approval_level >= 2,
        approval_level=approval_level,
        source_message_id=message.message_id,
    )


def _extract_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("text"), str):
        return payload["text"]
    message = payload.get("message")
    if isinstance(message, dict):
        if isinstance(message.get("text"), str):
            return message["text"]
        content = message.get("content")
        if isinstance(content, dict) and isinstance(content.get("text"), str):
            return content["text"]
    raise ValueError("Feishu message payload is missing text")
