"""维纳斯系统接口契约（唯一锚点）。

对应规格 §5。Codex 必须以本文件为准实现所有抽象，禁止各模块自行发明不一致的接口。
本文件只用 Python 标准库，保证可离线导入与测试。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Protocol, Sequence, runtime_checkable


# ---------------------------------------------------------------------------
# 数据分级与目的地（见规格 §3）
# ---------------------------------------------------------------------------
class DataClass(int, Enum):
    C0_PUBLIC = 0      # 公开
    C1_INTERNAL = 1    # 内部非敏感
    C2_SENSITIVE = 2   # 敏感（商业）
    C3_SECRET = 3      # 绝密（个人画像/语料/私域 PII）


class Destination(str, Enum):
    CLOUD_LLM = "cloud_llm"
    PRIVATE_LLM = "private_llm"
    PLATFORM_API = "platform_api"
    THIRD_PARTY_DATA = "third_party_data"
    FEISHU = "feishu"
    BACKUP = "backup"
    LOG = "log"


@dataclass
class Tagged:
    """带数据分级标签的载荷。任何流转/外发的数据都应被包裹为 Tagged。"""
    payload: Any
    data_class: DataClass
    pii: bool = False


# ---------------------------------------------------------------------------
# LLM 抽象（云/私有双拓扑，见 §3.3）
# ---------------------------------------------------------------------------
@dataclass
class LLMMessage:
    role: str   # system | user | assistant | tool
    content: str


@dataclass
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    is_private: bool  # True=自托管/私有，方可处理 C2/C3

    def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        max_tokens: int,
        tools: list[dict] | None = None,
    ) -> LLMResult: ...


@runtime_checkable
class Embedder(Protocol):
    is_private: bool

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


# ---------------------------------------------------------------------------
# 记忆（见 §7）
# ---------------------------------------------------------------------------
class MemoryKind(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class MemoryItem:
    id: str
    kind: MemoryKind
    content: str
    data_class: DataClass
    confidence: float
    source: str
    created_at: datetime
    last_used_at: datetime | None = None
    weight: float = 1.0  # 用于衰减/巩固


@dataclass
class ConsolidationReport:
    since: datetime
    candidate_items: list[MemoryItem] = field(default_factory=list)
    requires_approval: list[dict] = field(default_factory=list)
    rejected_feedback_loops: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class MemoryStore(ABC):
    @abstractmethod
    def write(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def retrieve(self, query: str, *, kind: MemoryKind | None = None, k: int = 8) -> list[MemoryItem]: ...

    @abstractmethod
    def consolidate(self, since: datetime) -> ConsolidationReport: ...  # §7 受控巩固（批量·可人审）

    @abstractmethod
    def decay(self) -> None: ...  # §7 衰减/遗忘


# ---------------------------------------------------------------------------
# 数据源（Tier B 可插拔）与工具
# ---------------------------------------------------------------------------
class DataSourceProvider(ABC):
    name: str

    @abstractmethod
    def search_hotspots(self, query: dict) -> list[dict]: ...

    @abstractmethod
    def fetch_creator(self, creator_id: str) -> dict: ...


class Tool(ABC):
    name: str
    data_class_out: DataClass
    reversible: bool

    @abstractmethod
    def run(self, **kwargs: Any) -> Tagged: ...


# ---------------------------------------------------------------------------
# 连接器与 OAuth 生命周期（见 §5 / 修订 B3）
# ---------------------------------------------------------------------------
@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str | None
    expires_at: datetime
    scopes: tuple[str, ...] = ()


class TokenStore(ABC):
    @abstractmethod
    def load(self, connector: str, account_id: str) -> OAuthToken | None: ...

    @abstractmethod
    def save(self, connector: str, account_id: str, token: OAuthToken) -> None: ...


class Connector(ABC):
    name: str

    @abstractmethod
    def refresh_if_needed(self, account_id: str) -> OAuthToken: ...
    # 必须并发安全（分布式锁）；临期（剩余<10%）主动刷新；刷新失败告警并触发重新授权。


# ---------------------------------------------------------------------------
# 隐私防火墙三位一体（见 §9）
# ---------------------------------------------------------------------------
class PrivacyFirewall(ABC):
    @abstractmethod
    def assert_destination_allowlisted(self, url: str) -> None: ...      # 目的地白名单

    @abstractmethod
    def allow_egress(self, dest: Destination, data: Tagged) -> bool: ... # 数据流向矩阵

    @abstractmethod
    def redact(self, data: Tagged, dest: Destination) -> Tagged: ...     # 内容脱敏/降级


# ---------------------------------------------------------------------------
# 人在回路审批（挂起/恢复/幂等/超时，修订 B2）
# ---------------------------------------------------------------------------
@dataclass
class Action:
    kind: str            # publish_video | reply_comment | create_campaign | add_contact | delete | ...
    summary: str         # 给飞书审批卡片的人类可读摘要
    payload: dict
    idempotency_key: str # 同键重放只执行一次
    data_class: DataClass
    reversible: bool = False


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    id: str
    action: Action
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    decided_by: str | None = None
    edited_payload: dict | None = None  # 用户可改后批准


class ApprovalGate(ABC):
    @abstractmethod
    def submit(self, action: Action) -> ApprovalRequest: ...  # 持久化 pending + 推飞书卡片

    @abstractmethod
    def resolve(
        self,
        approval_id: str,
        status: ApprovalStatus,
        decided_by: str,
        edited_payload: dict | None = None,
    ) -> ApprovalRequest: ...  # 必须幂等

    @abstractmethod
    def get(self, approval_id: str) -> ApprovalRequest | None: ...


# ---------------------------------------------------------------------------
# 频控 / 审计 / 成本
# ---------------------------------------------------------------------------
class RateLimiter(ABC):
    @abstractmethod
    def acquire(self, key: str) -> bool: ...  # 令牌桶；按平台/端点维度；429 退避在调用层


class AuditSink(ABC):
    @abstractmethod
    def record(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        reason: str,
        payload_digest: str,
        approval_id: str | None = None,
    ) -> None: ...


class CostMeter(ABC):
    @abstractmethod
    def add(self, *, category: str, amount: float, meta: dict) -> None: ...  # token/接口/第三方数据/投放


# ---------------------------------------------------------------------------
# 编排共享状态
# ---------------------------------------------------------------------------
@dataclass
class GraphState:
    task_id: str
    intent: str
    inputs: dict
    scratch: dict = field(default_factory=dict)      # 工作记忆
    pending_approval_id: str | None = None           # 非空=挂起等待人审
    outputs: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    cost: float = 0.0


# ---------------------------------------------------------------------------
# 智能体基类
# ---------------------------------------------------------------------------
class BaseAgent(ABC):
    name: str
    system_prompt: str
    tools: list[Tool]

    @abstractmethod
    def run(self, state: GraphState) -> GraphState: ...
