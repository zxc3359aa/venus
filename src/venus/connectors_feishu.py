"""飞书接入适配（规格 §10）。

- FakeFeishuGateway：离线模拟“收消息→回审批卡片”，供测试/演示。
- real_start：真实长连接占位。Context7/官方文档核验前禁止执行真实平台连接。

隔离要点（与“小龙虾”互不干扰）：维纳斯是独立飞书自建应用——独立 App ID/Secret、
独立长连接进程、独立事件订阅、独立存储前缀 venus_。
长连接高可用：单活动实例持有连接（或多实例时按 event_id 去重），断线指数退避重连，事件幂等。
"""
from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from venus.contracts import ApprovalRequest


class PlatformInterfaceNotVerified(RuntimeError):
    """平台真实接口尚未完成 Context7/官方文档核验。"""


@dataclass
class FakeFeishuGateway:
    """离线网关：记录收到的消息与已发送的审批卡片。"""
    received: list = field(default_factory=list)
    sent_cards: list = field(default_factory=list)

    def on_message(self, text: str) -> str:
        self.received.append(text)
        return text

    def send_approval_card(self, req: ApprovalRequest) -> None:
        # 真实：调 lark_oapi 发交互卡片（同意/修改/驳回按钮 + 卡片状态机）
        self.sent_cards.append(req)


def _env_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _is_context7_verified() -> bool:
    if _env_bool(os.getenv("VENUS_FEISHU_CONTEXT7_VERIFIED")):
        return True
    marker = os.getenv("VENUS_FEISHU_CONTEXT7_MARKER")
    if marker:
        return Path(marker).expanduser().exists()
    return False


def _is_live_enabled() -> bool:
    return _env_bool(os.getenv("VENUS_FEISHU_LIVE_ENABLED"))


def _import_lark_oapi():
    try:
        return importlib.import_module("lark_oapi")
    except ModuleNotFoundError as exc:
        raise PlatformInterfaceNotVerified(
            "未发现 lark_oapi 依赖。请先安装 `venus[feishu]`（或 `pip install lark-oapi`）后再启用实时接入。"
        ) from exc


def _extract_event_payload(message: Any) -> Mapping[str, Any]:
    if isinstance(message, Mapping):
        if "event" in message and isinstance(message["event"], Mapping):
            return message["event"]
        return message
    if hasattr(message, "dict") and callable(message.dict):
        return _extract_event_payload(message.dict())
    if hasattr(message, "__dict__"):
        return _extract_event_payload(message.__dict__)
    return {}


def _build_event_handler(lark_oapi_module, on_message: Callable[[Mapping[str, Any]], None]):
    """Build a minimal event handler for message events and keep registration compatibility."""

    def _attempt_register(target: Any, method_names: Iterable[str]) -> Any:
        candidate = None
        for name in method_names:
            candidate = getattr(target, name, None)
            if callable(candidate):
                break
        if candidate is None:
            return None

        register_attempts = (
            (_on_message,),
            ("im.message.receive_v1", _on_message),
            ("p2:im.message.receive_v1", _on_message),
        )
        for args in register_attempts:
            try:
                candidate(*args)
                return target
            except TypeError:
                continue
        return None

    event_handler_cls = getattr(lark_oapi_module, "EventDispatcherHandler", None)
    if event_handler_cls is None:
        raise PlatformInterfaceNotVerified(
            "Context7 已核验接口，但当前 lark_oapi 缺少 EventDispatcherHandler。"
        )

    # lark-oapi 1.6+ 推荐先通过 builder 注册事件回调，再 build 生成可消费事件的 handler。
    # 兼容历史实现：直接实例化 EventDispatcherHandler，并尝试直接注册回调。
    builder = getattr(event_handler_cls, "builder", None)

    def _on_message(event: Any):
        on_message(_extract_event_payload(event))

    register_names = (
        "register_p2_im_message_receive_v1",
        "register_im_message_receive_v1",
        "register_message_receive",
    )

    if callable(builder):
        try:
            handler = builder("", "")
        except Exception as exc:  # noqa: BLE001
            raise PlatformInterfaceNotVerified(
                "Context7 已核验接口，但当前 lark_oapi EventDispatcherHandler.builder 调用失败。"
            ) from exc

        if _attempt_register(handler, register_names) is not None:
            if hasattr(handler, "build"):
                return handler.build()
            return handler

        raise PlatformInterfaceNotVerified(
            "Context7 已核验接口，但当前 lark_oapi 无可用的消息事件回调注册方法。"
        )

    handler = event_handler_cls()

    if _attempt_register(handler, register_names) is not None:
        return handler

    raise PlatformInterfaceNotVerified(
        "Context7 已核验接口，但当前 lark_oapi 事件处理器注册方式与预期不匹配。"
    )


def _build_ws_client(lark_oapi_module, app_id: str, app_secret: str, handler):
    factory = None
    if hasattr(lark_oapi_module, "ws"):
        factory = getattr(lark_oapi_module.ws, "Client", None)
    if factory is None:
        factory = getattr(lark_oapi_module, "Client", None)
    if factory is None:
        raise PlatformInterfaceNotVerified(
            "Context7 已核验接口，但当前 lark_oapi 缺少可用的长连接 Client。"
        )

    candidate_inits = (
        ((app_id, app_secret, handler), {}),
        ((app_id, app_secret), {"handler": handler}),
        ((app_id, app_secret), {"event_handler": handler}),
    )
    last_exc: Exception | None = None
    for args, kwargs in candidate_inits:
        try:
            return factory(*args, **kwargs)
        except TypeError as exc:
            last_exc = exc
    raise PlatformInterfaceNotVerified(
        "Context7 已核验接口，但 lark-oapi Client 参构造方式与预期不匹配。"
    ) from last_exc


def real_start(app_id: str, app_secret: str, on_message: Callable[[Mapping[str, Any]], None]) -> None:
    """真实长连接启动。默认严格阻断，必须显式开启后才会执行。

    // VERIFY-DOC: 飞书 事件订阅(im.message.receive_v1) 与 交互卡片 接口
    // VERIFY-DOC: 飞书 长连接回调签名与验签、事件去重、重连退避策略
    """
    if not _is_context7_verified():
        raise PlatformInterfaceNotVerified(
            "飞书真实长连接必须先完成 Context7/官方文档核验（VENUS_FEISHU_CONTEXT7_VERIFIED 或标记文件）。"
        )
    if not _is_live_enabled():
        raise PlatformInterfaceNotVerified(
            "文档核验已完成，但尚未开启实时接入。请设置 VENUS_FEISHU_LIVE_ENABLED=true 并通过审批确认。"
        )
    if not app_id or not app_secret:
        raise ValueError("app_id 与 app_secret 均不能为空。")

    lark_oapi = _import_lark_oapi()
    handler = _build_event_handler(lark_oapi, on_message)
    ws_client = _build_ws_client(lark_oapi, app_id, app_secret, handler)

    if not hasattr(ws_client, "start"):
        raise PlatformInterfaceNotVerified("lark-oapi 长连接对象不支持 start()，请核对官方文档。")

    # 真实环境下保持阻塞运行；无网/无凭证场景应由调用方异常治理重试。
    ws_client.start()
