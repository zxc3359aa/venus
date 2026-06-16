"""启动飞书长连接监听（需通过环境守门后才会执行）。

注意：
1. 先确保 `VENUS_FEISHU_CONTEXT7_VERIFIED=true`（或设置标记文件）；
2. 再确认 `VENUS_FEISHU_LIVE_ENABLED=true` 且通过审批；
3. 运行前先在隔离环境验证。
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from venus.connectors_feishu import PlatformInterfaceNotVerified, real_start
from venus.feishu_entry import run_feishu_entry


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key or key in os.environ:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        os.environ[key] = value


def _extract_message_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    if isinstance(payload.get("text"), str):
        return payload["text"]
    message = payload.get("message")
    if isinstance(message, dict):
        if isinstance(message.get("text"), str):
            return message["text"]
        if isinstance(message.get("content"), dict) and isinstance(message["content"].get("text"), str):
            return message["content"]["text"]
    return ""


def _on_message(payload: dict[str, Any]) -> None:
    text = _extract_message_text(payload)
    preview = text if text else "<empty message>"
    if len(preview) > 200:
        preview = preview[:200] + "..."
    print(f"[{datetime.now(timezone.utc).isoformat()}] Received message: {preview}")

    card_payload = run_feishu_entry(payload, workspace_root=ROOT)
    print(json.dumps(card_payload, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    _load_dotenv(ROOT / ".env")

    app_id = os.getenv("VENUS_FEISHU_APP_ID", "").strip()
    app_secret = os.getenv("VENUS_FEISHU_APP_SECRET", "").strip()
    print("启动飞书接入前置检查...")
    if not app_id or not app_secret:
        print("缺少 VENUS_FEISHU_APP_ID / VENUS_FEISHU_APP_SECRET，先配置后再试。")
        return 1

    print("开始尝试调用 real_start（默认必须通过 Context7 与 LIVE 两道闸门）...")
    try:
        real_start(app_id, app_secret, _on_message)
    except PlatformInterfaceNotVerified as exc:
        print(f"未能启动实时接入：{exc}")
        print("请确认：")
        print("- .env 已写入 VENUS_FEISHU_CONTEXT7_VERIFIED 或 VENUS_FEISHU_CONTEXT7_MARKER")
        print("- .env 已写入 VENUS_FEISHU_LIVE_ENABLED=true")
        print("- 已完成飞书事件验签与回调核验，且通过审批后执行。")
        return 2
    except Exception as exc:  # pragma: no cover - 真实环境异常透明传递
        print(f"实时接入启动失败：{exc!s}")
        return 3

    # real_start 成功时应为阻塞运行；若返回，说明回调链路异常终止
    print("real_start 已返回，说明连接流程提前退出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
