from __future__ import annotations

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
