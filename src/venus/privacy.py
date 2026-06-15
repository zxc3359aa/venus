"""隐私防火墙三位一体（目的地白名单 + 数据流向矩阵 + 内容脱敏/降级）。

对应规格 §3.2 / §9。这是 v2.0 修订 A1（隐私红线与云 LLM 矛盾）的运行期闭环：
即使云 LLM / 第三方数据在白名单上，C3（个人画像/语料/私域 PII）内容仍被矩阵拦截。
"""
from __future__ import annotations

from enum import Enum
from urllib.parse import urlparse

from venus.contracts import DataClass, Destination, Tagged


class Policy(str, Enum):
    ALLOW = "allow"
    REDACT = "redact"
    DENY = "deny"


class PrivacyError(RuntimeError):
    """违反数据流向矩阵或白名单时抛出。"""


# 数据流向矩阵（规格 §3.2）。键 = (数据类, 目的地)。
_A, _R, _D = Policy.ALLOW, Policy.REDACT, Policy.DENY
DESTS = [
    Destination.PRIVATE_LLM,
    Destination.CLOUD_LLM,
    Destination.PLATFORM_API,
    Destination.THIRD_PARTY_DATA,
    Destination.FEISHU,
    Destination.BACKUP,
    Destination.LOG,
]
# 行顺序与 DESTS 对齐
_ROWS: dict[DataClass, list[Policy]] = {
    DataClass.C0_PUBLIC:    [_A, _A, _A, _A, _A, _A, _A],
    DataClass.C1_INTERNAL:  [_A, _A, _A, _D, _A, _A, _A],
    DataClass.C2_SENSITIVE: [_A, _R, _A, _R, _R, _A, _D],
    DataClass.C3_SECRET:    [_A, _D, _R, _D, _R, _A, _D],
}
MATRIX: dict[tuple[DataClass, Destination], Policy] = {
    (dc, dest): _ROWS[dc][i] for dc in _ROWS for i, dest in enumerate(DESTS)
}

# 示例白名单（生产应从配置文件加载，见 .env: EGRESS_ALLOWLIST_FILE）。
DEFAULT_ALLOWLIST: set[str] = {
    "api.openai.com",
    "open.feishu.cn",
    "open.oceanengine.com",
    "open.douyin.com",
    "qyapi.weixin.qq.com",
}

# 视为 PII 的字段名（脱敏时剥离）。
_PII_KEYS = {"phone", "mobile", "wechat", "name", "id_card", "address", "email", "openid", "unionid", "语料"}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _strip_pii(payload):
    if isinstance(payload, dict):
        return {k: v for k, v in payload.items() if k.lower() not in {p.lower() for p in _PII_KEYS}}
    return payload


class DefaultPrivacyFirewall:
    """PrivacyFirewall 的默认实现（满足 contracts.PrivacyFirewall 协议）。"""

    def __init__(self, allowlist: set[str] | None = None, matrix=None):
        self.allowlist = set(allowlist) if allowlist is not None else set(DEFAULT_ALLOWLIST)
        self.matrix = matrix or MATRIX

    def policy(self, dest: Destination, dc: DataClass) -> Policy:
        return self.matrix.get((dc, dest), Policy.DENY)

    def assert_destination_allowlisted(self, url: str) -> None:
        host = _host(url)
        if host not in self.allowlist:
            raise PrivacyError(f"目的地未在白名单: {host or url}")

    def allow_egress(self, dest: Destination, data: Tagged) -> bool:
        return self.policy(dest, data.data_class) == Policy.ALLOW

    def redact(self, data: Tagged, dest: Destination) -> Tagged:
        p = self.policy(dest, data.data_class)
        if p == Policy.ALLOW:
            return data
        if p == Policy.DENY:
            raise PrivacyError(f"数据类 {data.data_class.name} 禁止发往 {dest.value}")
        # REDACT
        if data.data_class == DataClass.C3_SECRET:
            # C3 身份级数据不可自动去标识为可外发；
            # 如需借云 LLM 能力，须由 PersonaAgent 显式蒸馏为不可识别身份的“风格描述符”(C1)。
            raise PrivacyError("C3 不可自动脱敏外发；需显式蒸馏为 C1 风格描述符（见 §3.3）")
        # C2 → 剥离 PII 字段，降为可外发摘要(C1)
        return Tagged(payload=_strip_pii(data.payload), data_class=DataClass.C1_INTERNAL, pii=False)
