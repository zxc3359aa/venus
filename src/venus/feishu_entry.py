from __future__ import annotations

import json
import shlex
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from venus.approvals import create_approval_record
from venus.orchestrator import VenusOrchestrator


COMMAND_APPROVAL_LEVELS = {
    "help": 0,
    "status": 0,
    "hotspot": 1,
    "product": 1,
    "comments": 1,
    "monitoring": 1,
    "airtable": 1,
    "douyin": 1,
    "agent-run": 1,
    "approve": 2,
}

SECRET_KEYS = {"secret", "token", "password", "app_secret", "authorization"}


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
                "monitoring": root / "data" / "samples" / "competitors.json",
                "airtable": root / "data" / "samples" / "airtable_export.json",
                "douyin": root / "data" / "samples" / "douyin_engagement.json",
                "agent-run": root / "data" / "samples" / "agent_run.json",
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


def run_feishu_entry(
    payload: dict[str, Any],
    workspace_root: Path | str | None = None,
    config: FeishuConfig | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path.cwd()
    active_config = config or FeishuConfig(workspace_root=root)
    message = normalize_feishu_message(_redact_payload(payload))
    command = parse_feishu_command(message, active_config)

    if command.name == "help":
        card = _status_card(
            "Venus command help",
            "Available commands: /venus help, /venus status, /venus hotspot, /venus product, /venus comments, /venus monitoring, /venus airtable, /venus douyin, /venus agent-run, /venus approve <id> <decision>",
            active_config,
        )
    elif command.name == "status":
        card = _status_card(
            "Venus Feishu status",
            f"{active_config.agent_name} is running in dry-run mode with {active_config.env_prefix} config.",
            active_config,
        )
    elif command.name == "unknown":
        card = _error_card(
            "Unsupported Venus command",
            "Unsupported Venus command. Send /venus help to see available commands.",
        )
    elif command.name in {"hotspot", "product", "comments", "monitoring", "airtable", "douyin", "agent-run"}:
        card = _workflow_report_card(command, active_config)
    elif command.name == "approve":
        approval = create_approval_record(
            action_type="feishu_approval_intent",
            approval_level=2,
            draft=" ".join(command.args) or "approval intent from Feishu",
            evidence_ids=[command.source_message_id],
            reviewer=message.sender_id,
            created_at=message.timestamp,
        )
        card = {
            "type": "approval_request",
            "title": "Approval intent recorded",
            "summary": "Venus recorded this approval intent locally. No external action was executed.",
            "approval_level": 2,
            "risk_notes": [
                "Dry-run mode is active.",
                "Live Feishu sending and public platform actions remain disabled.",
            ],
        }
        return _base_response(command, active_config, card, approval_records=[approval])
    else:
        card = _error_card(
            "Workflow unavailable",
            f"The {command.name} command is parsed but unavailable in this dry-run adapter shell.",
        )

    return _base_response(command, active_config, card, approval_records=[])


def _base_response(
    command: FeishuCommand,
    config: FeishuConfig,
    card: dict[str, Any],
    approval_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "workflow": "feishu",
        "dry_run": config.dry_run,
        "command": command.to_dict(),
        "card": card,
        "approval_records": approval_records,
        "external_actions": [],
    }


def _status_card(title: str, summary: str, config: FeishuConfig) -> dict[str, Any]:
    return {
        "type": "status",
        "title": title,
        "summary": summary,
        "facts": {
            "agent_name": config.agent_name,
            "env_prefix": config.env_prefix,
            "command_prefix": config.command_prefix,
            "dry_run": config.dry_run,
            "storage_namespace": config.storage_namespace,
        },
    }


def _error_card(title: str, summary: str) -> dict[str, Any]:
    return {
        "type": "error",
        "title": title,
        "summary": summary,
        "suggested_command": "/venus help",
    }


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in SECRET_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = _redact_payload(value)
        else:
            redacted[key] = value
    return redacted


def _workflow_report_card(command: FeishuCommand, config: FeishuConfig) -> dict[str, Any]:
    input_path = _resolve_input_path(command, config)
    records = json.loads(input_path.read_text(encoding="utf-8"))
    payload_key = {
        "hotspot": "hotspots",
        "product": "products",
        "comments": "comments",
        "monitoring": "competitors",
        "airtable": "airtable",
        "douyin": "douyin",
        "agent-run": "agent_run",
    }[command.name]
    payload = records if command.name in {"monitoring", "airtable", "douyin", "agent-run"} else {payload_key: records}
    workflow = "agent_run" if command.name == "agent-run" else command.name
    result = VenusOrchestrator().run(workflow, payload)
    result = _normalize_report_result(command.name, result)
    return {
        "type": "report",
        "title": f"Venus {command.name} report",
        "summary": _report_summary(command.name, result),
        "result": result,
        "source_path": str(input_path),
    }


def _resolve_input_path(command: FeishuCommand, config: FeishuConfig) -> Path:
    if command.args:
        candidate = Path(command.args[0])
        if not candidate.is_absolute():
            candidate = config.workspace_root / candidate
        return candidate
    return config.default_input_paths[command.name]


def _normalize_report_result(command_name: str, result: dict[str, Any]) -> dict[str, Any]:
    if command_name != "comments":
        return result
    data = dict(result["result"])
    summary = data.get("summary", {})
    if "approval_gated" not in data and isinstance(summary, dict):
        data["approval_gated"] = summary.get("approval_gated", 0)
    normalized = dict(result)
    normalized["result"] = data
    return normalized


def _report_summary(command_name: str, result: dict[str, Any]) -> str:
    data = result["result"]
    if command_name == "hotspot":
        return f"Top topic: {data['top_topic']}"
    if command_name == "product":
        return f"Product risk level: {data['risk_level']}"
    if command_name == "comments":
        return f"Approval-gated replies: {data['approval_gated']}"
    if command_name == "monitoring":
        return f"Top monitored account: {data['summary']['top_account']}"
    if command_name == "airtable":
        return f"Airtable-ready tables: {data['summary']['table_count']}"
    if command_name == "douyin":
        return f"Douyin approval-gated replies: {data['summary']['approval_gated_reply_count']}"
    if command_name == "agent-run":
        return f"Agent run approval records: {len(data['approval_records'])}"
    return "Venus report generated."


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
