"""LLMProvider 实现：云/私有双拓扑（规格 §3.3）。

- FakeLLMProvider：确定性、离线，供测试与 M0 演示使用。
- OpenAICompatibleProvider：云/私有 OpenAI 兼容端点的占位适配（接入时用 httpx 实现）。
"""
from __future__ import annotations

from typing import Sequence

from venus.contracts import LLMMessage, LLMResult


def _count(text: str) -> int:
    return max(1, len(text.split()))


class FakeLLMProvider:
    """确定性 LLM，满足 contracts.LLMProvider 协议。默认标记为私有（可处理 C2/C3）。"""

    name = "fake"
    is_private = True

    def __init__(self, scripted: dict[str, str] | None = None):
        self.scripted = scripted or {}
        self.calls: list[list[LLMMessage]] = []

    def complete(self, messages: Sequence[LLMMessage], *, max_tokens: int, tools=None) -> LLMResult:
        self.calls.append(list(messages))
        # 取最后一条 system+user 文本用于规则匹配，保证确定性
        joined = " ".join(m.content for m in messages)
        for key, val in self.scripted.items():
            if key in joined:
                return LLMResult(
                    text=val,
                    tokens_in=sum(_count(m.content) for m in messages),
                    tokens_out=_count(val),
                    model=self.name,
                )
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        text = f"[BRIEF] 确定性占位：{user[:40]}"
        return LLMResult(
            text=text,
            tokens_in=sum(_count(m.content) for m in messages),
            tokens_out=_count(text),
            model=self.name,
        )


class OpenAICompatibleProvider:
    """云/私有 OpenAI 兼容端点适配（M0 占位）。

    真实实现：用 httpx 调 /v1/chat/completions；私有侧用 vLLM/Ollama 暴露 OpenAI 兼容 API。
    所有出网调用前必须经 PrivacyFirewall.assert_destination_allowlisted + 数据流向矩阵校验。
    // VERIFY-DOC: 目标厂商的 OpenAI 兼容端点与鉴权
    """

    def __init__(self, *, name: str, base_url: str, api_key: str, is_private: bool):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.is_private = is_private

    def complete(self, messages, *, max_tokens: int, tools=None) -> LLMResult:
        raise NotImplementedError(
            "M0 占位：接入时用 httpx 调用 OpenAI 兼容端点；私有侧用 vLLM/Ollama。"
        )
