from __future__ import annotations

import pytest

from venus.connectors_feishu import (
    _build_event_handler,
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


def test_build_event_handler_prefers_builder_api():
    captured = []

    class DummyBuilder:
        def __init__(self):
            self.callback = None

        def register_p2_im_message_receive_v1(self, callback):
            self.callback = callback
            return self

        def build(self):
            return self

    class DummyHandler:
        @staticmethod
        def builder(_encrypt_key: str, _verification_token: str):
            return DummyBuilder()

    class DummyModule:
        EventDispatcherHandler = DummyHandler

    handler = _build_event_handler(DummyModule, lambda payload: captured.append(payload))
    assert isinstance(handler, DummyBuilder)
    assert handler.callback is not None

    handler.callback({"event": {"text": "hello", "tag": "unit"}})
    assert captured == [{"text": "hello", "tag": "unit"}]


def test_build_event_handler_falls_back_to_direct_handler_api():
    captured = []

    class DummyHandler:
        def __init__(self):
            self.callback = None

        def register_im_message_receive_v1(self, callback):
            self.callback = callback
            return self

    class DummyModule:
        EventDispatcherHandler = DummyHandler

    handler = _build_event_handler(DummyModule, lambda payload: captured.append(payload))
    assert isinstance(handler, DummyHandler)
    assert handler.callback is not None

    handler.callback({"event": {"text": "fallback"}})
    assert captured == [{"text": "fallback"}]


def test_build_event_handler_raises_when_registration_missing():
    class DummyHandler:
        pass

    class DummyModule:
        EventDispatcherHandler = DummyHandler

    with pytest.raises(PlatformInterfaceNotVerified, match="注册方式"):
        _build_event_handler(DummyModule, lambda payload: None)
