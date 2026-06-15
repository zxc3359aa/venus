from __future__ import annotations

import pytest

from venus.connectors_feishu import (
    PlatformInterfaceNotVerified,
    real_start,
)


def test_real_start_requires_context7_and_live_flags(monkeypatch):
    monkeypatch.delenv("VENUS_FEISHU_CONTEXT7_VERIFIED", raising=False)
    monkeypatch.delenv("VENUS_FEISHU_LIVE_ENABLED", raising=False)

    with pytest.raises(PlatformInterfaceNotVerified, match="文档"):
        real_start("app-id", "app-secret", lambda _: None)


def test_real_start_rejects_without_credentials(monkeypatch):
    monkeypatch.setenv("VENUS_FEISHU_CONTEXT7_VERIFIED", "true")
    monkeypatch.setenv("VENUS_FEISHU_LIVE_ENABLED", "true")

    with pytest.raises(ValueError, match="不能为空"):
        real_start("", "app-secret", lambda _: None)


def test_real_start_launches_ws_client_when_enabled(monkeypatch):
    monkeypatch.setenv("VENUS_FEISHU_CONTEXT7_VERIFIED", "true")
    monkeypatch.setenv("VENUS_FEISHU_LIVE_ENABLED", "true")

    events = {"started": False, "imported": False, "connected": False}

    class DummyClient:
        def __init__(self, *_args, **_kwargs):
            events["connected"] = True

        def start(self):
            events["started"] = True

    class DummyModule:
        EventDispatcherHandler = lambda: object()

    class DummyWs:
        Client = DummyClient

    def fake_import():
        events["imported"] = True
        module = DummyModule()
        module.ws = DummyWs
        return module

    monkeypatch.setattr("venus.connectors_feishu._import_lark_oapi", fake_import)
    monkeypatch.setattr(
        "venus.connectors_feishu._build_event_handler",
        lambda *_args: object(),
    )
    monkeypatch.setattr("venus.connectors_feishu._build_ws_client", lambda *_, **__: DummyClient())

    real_start("app-id", "app-secret", lambda _: None)

    assert events["imported"]
    assert events["connected"]
    assert events["started"]
