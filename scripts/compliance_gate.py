"""维纳斯合规门：提交前检查 Tier、隐私、审批、机密红线。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from venus.contracts import DataClass, Destination, Tagged
from venus.modules.m1_hotspot import build_publish_action
from venus.privacy import DefaultPrivacyFirewall, PrivacyError


ROOT = Path(__file__).resolve().parents[1]
SCAN_PATHS = [ROOT / "src", ROOT / "scripts", ROOT / "Makefile", ROOT / "pyproject.toml"]
TIER_C_PATTERNS = [
    ("selenium", "疑似浏览器自动化抓取"),
    ("undetected_chromedriver", "疑似绕过检测"),
    ("模拟登录", "Tier C 模拟登录"),
    ("绕验证码", "Tier C 绕验证码"),
    ("刷量", "Tier C 刷量"),
]
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api_key|app_secret|access_token|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
]


def main() -> int:
    failures: list[str] = []
    failures.extend(_scan_tier_c())
    failures.extend(_scan_secrets())
    failures.extend(_check_privacy_firewall())
    failures.extend(_check_approval_boundary())

    if failures:
        print("compliance-gate: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("compliance-gate: PASS")
    return 0


def _iter_files() -> list[Path]:
    files: list[Path] = []
    self_path = Path(__file__).resolve()
    for path in SCAN_PATHS:
        if path.is_file():
            if path.resolve() != self_path:
                files.append(path)
            continue
        if path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file()
                and item.resolve() != self_path
                and item.suffix in {".py", ".toml", ".md", ""}
                and ".venv" not in item.parts
            )
    return files


def _scan_tier_c() -> list[str]:
    failures = []
    for path in _iter_files():
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for needle, reason in TIER_C_PATTERNS:
            if needle.lower() in text:
                failures.append(f"{path.relative_to(ROOT)}: {reason} ({needle})")
    return failures


def _scan_secrets() -> list[str]:
    failures = []
    for path in _iter_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"{path.relative_to(ROOT)}: 疑似硬编码机密 {pattern.pattern}")
    return failures


def _check_privacy_firewall() -> list[str]:
    fw = DefaultPrivacyFirewall()
    c3 = Tagged(payload={"语料": "private"}, data_class=DataClass.C3_SECRET, pii=True)
    if fw.allow_egress(Destination.CLOUD_LLM, c3):
        return ["C3 被允许外发云 LLM"]
    try:
        fw.redact(c3, Destination.CLOUD_LLM)
    except PrivacyError:
        return []
    return ["C3 可被自动脱敏外发云 LLM，违反规格 §3"]


def _check_approval_boundary() -> list[str]:
    action = build_publish_action("早C晚A热点简报")
    failures = []
    if action.reversible:
        failures.append("发布视频动作必须标记为不可逆")
    if not action.idempotency_key:
        failures.append("不可逆动作缺少 idempotency_key")
    if action.data_class.value > DataClass.C1_INTERNAL.value:
        failures.append("M1 发布草稿动作不应携带 C2/C3")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
