# Venus Feishu Mobile Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dry-run Feishu mobile entry layer that parses `/venus` commands, routes safe workflows into the existing Venus orchestrator, returns Feishu-card-ready drafts, and proves Venus/Xiaolongxia isolation.

**Architecture:** Add one focused module, `src/venus/feishu_entry.py`, for Feishu-like message normalization, command parsing, response rendering, and dry-run adapter orchestration. Extend the existing CLI with a `feishu` workflow while keeping domain logic inside the current orchestrator modules. Keep all Feishu settings under `VENUS_FEISHU_`, never call live Feishu APIs, and return `external_actions: []` for every response.

**Tech Stack:** Python 3.11+, standard library dataclasses/json/pathlib/shlex, pytest, existing Venus orchestrator and approval helpers.

---

## Scope Check

The design is focused enough for one implementation plan. It covers only a local Feishu-like dry-run entry layer. Live Feishu callbacks, app secrets, token refresh, public Douyin actions, WeChat, Enterprise WeChat, Qianchuan, Xingtu, and ad spend remain outside this plan.

## File Structure

- Create: `src/venus/feishu_entry.py`
  - Owns Feishu config, normalized message and command dataclasses, command parsing, card draft rendering, dry-run entry orchestration, secret redaction, and local path resolution.
- Create: `tests/test_feishu_entry.py`
  - Covers config defaults, Xiaolongxia isolation, parsing, help/status, workflow routing, approval intent, structured errors, and dry-run external action guarantees.
- Create: `data/samples/feishu_message.json`
  - A deterministic `/venus hotspot` sample payload for CLI smoke tests.
- Modify: `src/venus/cli.py`
  - Adds the `feishu` workflow and delegates to `run_feishu_entry`.
- Modify: `.env.example`
  - Adds Venus-only Feishu variables.
- Modify: `README.md`
  - Adds the local Feishu dry-run command.
- Modify: `task_plan.md`
  - Marks Phase 7 complete after verification.
- Modify: `progress.md`
  - Records the Phase 7 implementation and test evidence.
- Modify: `tests/test_cli_smoke.py`
  - Adds CLI smoke coverage for `venus feishu`.

---

### Task 1: Feishu Config, Message, And Command Parsing

**Files:**
- Create: `src/venus/feishu_entry.py`
- Create: `tests/test_feishu_entry.py`

- [ ] **Step 1: Write failing tests for config isolation and command parsing**

Create `tests/test_feishu_entry.py`:

```python
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
    assert config.default_input_paths["hotspot"] == tmp_workspace / "data" / "samples" / "hotspots.json"
    assert config.default_input_paths["product"] == tmp_workspace / "data" / "samples" / "products.json"
    assert config.default_input_paths["comments"] == tmp_workspace / "data" / "samples" / "comments.json"


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
```

- [ ] **Step 2: Run tests and verify they fail for the missing module**

Run:

```bash
pytest tests/test_feishu_entry.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'venus.feishu_entry'`.

- [ ] **Step 3: Add minimal Feishu config, message, and parser implementation**

Create `src/venus/feishu_entry.py`:

```python
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
        message_id=str(payload.get("message_id") or payload.get("message", {}).get("message_id") or "local-message"),
        chat_id=str(payload.get("chat_id") or payload.get("message", {}).get("chat_id") or "local-chat"),
        sender_id=str(payload.get("sender_id") or payload.get("sender", {}).get("sender_id", {}).get("open_id") or "local-sender"),
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
```

- [ ] **Step 4: Run parsing tests and verify they pass**

Run:

```bash
pytest tests/test_feishu_entry.py -v
```

Expected: PASS with 4 tests.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add src/venus/feishu_entry.py tests/test_feishu_entry.py
git commit -m "feat: add Feishu entry command parsing"
```

---

### Task 2: Feishu Response Rendering And Dry-Run Adapter

**Files:**
- Modify: `src/venus/feishu_entry.py`
- Modify: `tests/test_feishu_entry.py`

- [ ] **Step 1: Add failing tests for help, status, and unknown command responses**

Append to `tests/test_feishu_entry.py`:

```python
from venus.feishu_entry import run_feishu_entry


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
```

- [ ] **Step 2: Run targeted tests and verify they fail for missing `run_feishu_entry`**

Run:

```bash
pytest tests/test_feishu_entry.py::test_run_feishu_entry_help_returns_card_draft tests/test_feishu_entry.py::test_run_feishu_entry_status_redacts_secret_like_values tests/test_feishu_entry.py::test_run_feishu_entry_unknown_command_returns_safe_error -v
```

Expected: FAIL with `ImportError` or `AttributeError` showing `run_feishu_entry` is missing.

- [ ] **Step 3: Add renderer and dry-run adapter shell**

Append these functions to `src/venus/feishu_entry.py`:

```python
SECRET_KEYS = {"secret", "token", "password", "app_secret", "authorization"}


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
            "Available commands: /venus help, /venus status, /venus hotspot, /venus product, /venus comments, /venus approve <id> <decision>",
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
```

- [ ] **Step 4: Run targeted response tests and verify they pass**

Run:

```bash
pytest tests/test_feishu_entry.py::test_run_feishu_entry_help_returns_card_draft tests/test_feishu_entry.py::test_run_feishu_entry_status_redacts_secret_like_values tests/test_feishu_entry.py::test_run_feishu_entry_unknown_command_returns_safe_error -v
```

Expected: PASS with 3 tests.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add src/venus/feishu_entry.py tests/test_feishu_entry.py
git commit -m "feat: add Feishu dry-run response drafts"
```

---

### Task 3: Route Feishu Commands Into Existing Venus Workflows

**Files:**
- Modify: `src/venus/feishu_entry.py`
- Modify: `tests/test_feishu_entry.py`

- [ ] **Step 1: Add failing tests for hotspot, product, comments, and approve routing**

Append to `tests/test_feishu_entry.py`:

```python
import json


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
                {"user": "a", "text": "敏感肌能用吗", "likes": 5},
                {"user": "b", "text": "是不是智商税", "likes": 7},
            ],
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
```

- [ ] **Step 2: Run routing tests and verify they fail because workflows are not connected**

Run:

```bash
pytest tests/test_feishu_entry.py::test_run_feishu_entry_hotspot_routes_to_orchestrator tests/test_feishu_entry.py::test_run_feishu_entry_product_routes_to_orchestrator tests/test_feishu_entry.py::test_run_feishu_entry_comments_keeps_reply_drafts_approval_gated tests/test_feishu_entry.py::test_run_feishu_entry_approve_records_intent_without_external_action -v
```

Expected: FAIL because `run_feishu_entry` returns `Workflow unavailable` for these commands before Task 3 wires them to the orchestrator.

- [ ] **Step 3: Connect dry-run workflows to the orchestrator and approval helper**

Modify imports at the top of `src/venus/feishu_entry.py`:

```python
import json
import shlex
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from venus.approvals import create_approval_record
from venus.orchestrator import VenusOrchestrator
```

Replace the non-help branches inside `run_feishu_entry` with:

```python
    elif command.name == "unknown":
        card = _error_card(
            "Unsupported Venus command",
            "Unsupported Venus command. Send /venus help to see available commands.",
        )
    elif command.name in {"hotspot", "product", "comments"}:
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
```

Append these helper functions to `src/venus/feishu_entry.py`:

```python
def _workflow_report_card(command: FeishuCommand, config: FeishuConfig) -> dict[str, Any]:
    input_path = _resolve_input_path(command, config)
    records = json.loads(input_path.read_text(encoding="utf-8"))
    payload_key = {
        "hotspot": "hotspots",
        "product": "products",
        "comments": "comments",
    }[command.name]
    result = VenusOrchestrator().run(command.name, {payload_key: records})
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


def _report_summary(command_name: str, result: dict[str, Any]) -> str:
    data = result["result"]
    if command_name == "hotspot":
        return f"Top topic: {data['top_topic']}"
    if command_name == "product":
        return f"Product risk score: {data['risk_score']}"
    if command_name == "comments":
        return f"Approval-gated replies: {data['approval_gated']}"
    return "Venus report generated."
```

- [ ] **Step 4: Run routing tests and verify they pass**

Run:

```bash
pytest tests/test_feishu_entry.py::test_run_feishu_entry_hotspot_routes_to_orchestrator tests/test_feishu_entry.py::test_run_feishu_entry_product_routes_to_orchestrator tests/test_feishu_entry.py::test_run_feishu_entry_comments_keeps_reply_drafts_approval_gated tests/test_feishu_entry.py::test_run_feishu_entry_approve_records_intent_without_external_action -v
```

Expected: PASS with 4 tests.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add src/venus/feishu_entry.py tests/test_feishu_entry.py
git commit -m "feat: route Feishu commands through Venus workflows"
```

---

### Task 4: CLI, Sample Payload, Docs, And Acceptance Verification

**Files:**
- Modify: `src/venus/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Create: `data/samples/feishu_message.json`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `task_plan.md`
- Modify: `progress.md`

- [ ] **Step 1: Add failing CLI smoke test for `venus feishu`**

Append to `tests/test_cli_smoke.py`:

```python

def test_cli_feishu_outputs_dry_run_card():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "feishu",
            "data/samples/feishu_message.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "feishu"
    assert output["dry_run"] is True
    assert output["command"]["name"] == "hotspot"
    assert output["external_actions"] == []
    assert output["card"]["type"] == "report"
```

- [ ] **Step 2: Run CLI smoke test and verify it fails because `feishu` is not a workflow choice**

Run:

```bash
pytest tests/test_cli_smoke.py::test_cli_feishu_outputs_dry_run_card -v
```

Expected: FAIL because `argparse` rejects `feishu` or because the sample file is missing.

- [ ] **Step 3: Create deterministic Feishu sample payload**

Create `data/samples/feishu_message.json`:

```json
{
  "message_id": "msg-venus-local-001",
  "chat_id": "chat-venus-local",
  "sender_id": "owner-local",
  "timestamp": "2026-06-14T13:40:00+08:00",
  "text": "/venus hotspot"
}
```

- [ ] **Step 4: Extend CLI with the Feishu workflow**

Modify `src/venus/cli.py` imports:

```python
from venus.feishu_entry import run_feishu_entry
from venus.orchestrator import VenusOrchestrator
```

Modify the parser workflow choices:

```python
    parser.add_argument("workflow", choices=["hotspot", "product", "comments", "feishu"])
```

Replace the main execution block after reading `records` with:

```python
    if args.workflow == "feishu":
        result = run_feishu_entry(records, workspace_root=Path.cwd())
    else:
        payload = _payload_for(args.workflow, records)
        result = VenusOrchestrator().run(args.workflow, payload)
```

- [ ] **Step 5: Update environment example and README**

Append to `.env.example`:

```bash
VENUS_FEISHU_AGENT_NAME=venus
VENUS_FEISHU_COMMAND_PREFIX=/venus
VENUS_FEISHU_DRY_RUN=true
```

Add this section to `README.md` after the comments smoke command:

````markdown

Run the local Feishu dry-run entry:

```bash
venus feishu data/samples/feishu_message.json
```

This command parses a Feishu-like `/venus` message and returns a card-ready JSON draft. It does not send Feishu messages or perform external actions.
````

- [ ] **Step 6: Update planning status files**

In `task_plan.md`, change Phase 7 status from `Pending` to `Complete` and update the exit criteria sentence to:

```markdown
| 7. Feishu mobile entry | Complete | Add a Feishu interface isolated from the existing "Xiaolongxia" agent. | Local dry-run Feishu entry parses `/venus` commands, routes safe workflows, and returns card-ready drafts with no external actions. |
```

Append to `progress.md`:

```markdown

## Feishu Entry Progress

- Added a local dry-run Feishu entry layer for Phase 7.
- Added Venus-only `VENUS_FEISHU_` configuration defaults and Xiaolongxia isolation checks.
- Added `/venus` command parsing for help, status, hotspot, product, comments, and approval intent.
- Routed hotspot, product, and comments commands through the existing Venus orchestrator.
- Added card-ready response drafts with `external_actions: []` for every Feishu entry output.
- Added CLI smoke command: `venus feishu data/samples/feishu_message.json`.
```

- [ ] **Step 7: Run CLI smoke test and full test suite**

Run:

```bash
pytest tests/test_cli_smoke.py::test_cli_feishu_outputs_dry_run_card -v
pytest -v
```

Expected: first command passes, then full suite passes with the original 14 tests plus new Feishu tests.

- [ ] **Step 8: Run manual CLI smoke command**

Run:

```bash
venus feishu data/samples/feishu_message.json
```

Expected: JSON output contains:

```json
{
  "workflow": "feishu",
  "dry_run": true,
  "external_actions": []
}
```

- [ ] **Step 9: Commit Task 4**

Run:

```bash
git add src/venus/cli.py tests/test_cli_smoke.py data/samples/feishu_message.json .env.example README.md task_plan.md progress.md
git commit -m "feat: add Feishu dry-run CLI entry"
```

---

## Final Verification

- [ ] Run the full test suite:

```bash
pytest -v
```

Expected: all tests pass.

- [ ] Run CLI smoke commands:

```bash
venus hotspot data/samples/hotspots.json
venus product data/samples/products.json
venus comments data/samples/comments.json
venus feishu data/samples/feishu_message.json
```

Expected: each command prints valid JSON with `external_actions: []`.

- [ ] Inspect git status:

```bash
git status -sb
```

Expected: clean working tree on `codex/venus-feishu-entry`.

- [ ] Push branch:

```bash
git push -u origin codex/venus-feishu-entry
```

Expected: branch pushes successfully. If a GitHub credential prompt appears, use the same authorized token that successfully pushed `master:main`.

## Self-Review Notes

- Spec coverage: config namespace, dry-run entry, command parser, workflow routing, response drafts, approval intent, error output, CLI smoke, README, and Venus/Xiaolongxia isolation are all mapped to tasks.
- Scope guard: live Feishu callbacks and live message sending are intentionally absent.
- Type consistency: `FeishuConfig`, `FeishuMessage`, `FeishuCommand`, and `run_feishu_entry` are defined before tests or CLI code use them.
- Side-effect guarantee: every response includes `external_actions: []`, and no plan step calls a live Feishu, Douyin, WeChat, Qianchuan, or Xingtu API.
