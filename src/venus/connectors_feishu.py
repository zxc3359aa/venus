"""飞书接入适配（规格 §10）。

- FakeFeishuGateway：离线模拟“收消息→回审批卡片”，供测试/演示。
- real_start：真实长连接，使用官方 SDK lark-oapi（pip install lark-oapi）。

隔离要点（与“小龙虾”互不干扰）：维纳斯是独立飞书自建应用——独立 App ID/Secret、
独立长连接进程、独立事件订阅、独立存储前缀 venus_。
长连接高可用：单活动实例持有连接（或多实例时按 event_id 去重），断线指数退避重连，事件幂等。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from venus.contracts import ApprovalRequest


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


def real_start(app_id: str, app_secret: str, on_message: Callable[[object], None]) -> None:
    """真实长连接（需 pip install lark-oapi）。在独立线程/进程中运行；单活动实例。

    // VERIFY-DOC: 飞书 事件订阅(im.message.receive_v1) 与 交互卡片 接口
    """
    import lark_oapi as lark  # 延迟导入：离线测试无需安装

    def _handler(data) -> None:
        on_message(data)

    event_handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(_handler)
        .build()
    )
    cli = lark.ws.Client(app_id, app_secret, event_handler=event_handler, log_level=lark.LogLevel.INFO)
    cli.start()  # 阻塞调用；生产中放独立线程/进程，配合断线重连与事件去重
