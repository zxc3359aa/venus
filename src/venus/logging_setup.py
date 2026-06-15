"""结构化日志 + 强制脱敏处理器（规格 §9 / 修订 C4）。

任何日志输出都经脱敏：密钥/Token/口令、长数字串（手机号等）一律打码。
生产建议换 structlog + OpenTelemetry；M0 用标准库保证零三方依赖可跑。
"""
from __future__ import annotations

import logging
import re

_PATTERNS = [
    (re.compile(r"(?i)(app[_-]?secret|secret|access[_-]?token|token|password|api[_-]?key)\s*[=:]\s*\S+"),
     r"\1=***"),
    (re.compile(r"\b\d{11,}\b"), "***"),  # 手机号/长数字串
]


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pat, repl in _PATTERNS:
            msg = pat.sub(repl, msg)
        return msg


def get_logger(name: str = "venus") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactingFormatter("%(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
