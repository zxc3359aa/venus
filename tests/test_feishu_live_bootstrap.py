from __future__ import annotations

from pathlib import Path

import pytest
from scripts import feishu_live_bootstrap as script


def test_live_bootstrap_rejects_without_credentials(monkeypatch):
    monkeypatch.delenv("VENUS_FEISHU_APP_ID", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_APP_SECRET", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_CONTEXT7_VERIFIED", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_LIVE_ENABLED", raising=False)
    assert script.main() == 1


def test_live_bootstrap_blocks_when_not_verified(monkeypatch):
    monkeypatch.setenv("VENUS_FEISHU_APP_ID", "app-id")
    monkeypatch.setenv("VENUS_FEISHU_APP_SECRET", "app-secret")
    monkeypatch.delenv("VENUS_FEISHU_CONTEXT7_VERIFIED", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_LIVE_ENABLED", raising=False)
    assert script.main() == 2


def test_live_bootstrap_returns_zero_when_real_start_succeeds(monkeypatch):
    monkeypatch.setenv("VENUS_FEISHU_APP_ID", "app-id")
    monkeypatch.setenv("VENUS_FEISHU_APP_SECRET", "app-secret")
    monkeypatch.setenv("VENUS_FEISHU_CONTEXT7_VERIFIED", "true")
    monkeypatch.setenv("VENUS_FEISHU_LIVE_ENABLED", "true")

    started = {"value": 0}
    def fake_real_start(app_id, app_secret, handler):  # pragma: no cover - mocked path
        started["value"] += 1
        assert app_id == "app-id"
        assert app_secret == "app-secret"
        assert callable(handler)
        # 在真实环境 real_start 通常会阻塞；测试场景这里改为返回以完成主流程。

    monkeypatch.setattr(script, "real_start", fake_real_start)
    assert script.main() == 0
    assert started["value"] == 1


def test_live_bootstrap_loads_from_dotenv_if_present(monkeypatch, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "VENUS_FEISHU_APP_ID=from-file-id\n"
        "VENUS_FEISHU_APP_SECRET=from-file-secret\n"
        "VENUS_FEISHU_CONTEXT7_VERIFIED=true\n"
        "VENUS_FEISHU_LIVE_ENABLED=true\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("VENUS_FEISHU_APP_ID", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_APP_SECRET", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_CONTEXT7_VERIFIED", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_LIVE_ENABLED", raising=False)
    monkeypatch.setattr(script, "ROOT", tmp_path)

    started = {"value": 0}

    def fake_real_start(app_id, app_secret, handler):  # pragma: no cover - mocked path
        started["value"] += 1
        assert app_id == "from-file-id"
        assert app_secret == "from-file-secret"
        assert callable(handler)

    monkeypatch.setattr(script, "real_start", fake_real_start)
    assert script.main() == 0
    assert started["value"] == 1


def test_live_message_is_routed_to_feishu_entry(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_entry(payload, workspace_root=None):
        calls.append({"payload": payload, "workspace_root": str(workspace_root or "none")})
        return {"workflow": "feishu", "dry_run": True, "command": {"name": "help"}, "card": {"type": "status"}}

    monkeypatch.setattr(script, "run_feishu_entry", fake_entry)

    payload = {
        "text": "/venus status",
        "message_id": "msg-001",
        "chat_id": "chat-001",
        "sender_id": "sender-001",
        "timestamp": "2026-06-16T00:00:00Z",
    }

    script._on_message(payload)

    assert len(calls) == 1
    assert calls[0]["payload"] == payload
    assert calls[0]["workspace_root"].endswith("维纳斯")
