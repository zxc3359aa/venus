"""M3 人设/风格学习模块的离线最小切片（规格 §8 M3 / §7）。

M3 只做本地记忆、风格描述符蒸馏和受控巩固报告；不调用云 LLM、
第三方数据源或平台接口。C3 原始画像/语料只留在私有侧，输出给下游
生成链路时必须先降级为不可识别个人身份的 C1 风格描述符。
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from venus.contracts import ConsolidationReport, DataClass, MemoryItem, MemoryKind, MemoryStore, Tagged

_PII_KEYS = {"raw_corpus", "phone", "mobile", "email", "wechat", "wecom", "name", "customer", "lead"}
_SELF_REINFORCING_SOURCES = {"model_output_accepted", "draft_accepted", "self_generated"}


class InMemoryPersonaMemoryStore(MemoryStore):
    """面向 M3 验收的内存版 MemoryStore。

    生产版会替换为加密持久化存储；这里保留相同契约，便于离线测试快/慢层、
    巩固和衰减行为。
    """

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def write(self, item: MemoryItem) -> None:
        self._items[item.id] = item

    def retrieve(self, query: str, *, kind: MemoryKind | None = None, k: int = 8) -> list[MemoryItem]:
        needle = query.strip().casefold()
        matches = []
        for item in self._items.values():
            if kind is not None and item.kind != kind:
                continue
            haystack = f"{item.content} {item.source}".casefold()
            if needle and needle not in haystack:
                continue
            matches.append(item)
        matches.sort(key=lambda item: (item.weight * item.confidence, item.created_at), reverse=True)
        return matches[:k]

    def consolidate(self, since: datetime) -> ConsolidationReport:
        candidates: list[MemoryItem] = []
        approvals: list[dict[str, Any]] = []
        rejected_feedback_loops: list[str] = []
        processed = 0

        for item in sorted(self._items.values(), key=lambda value: value.created_at):
            if item.kind != MemoryKind.EPISODIC or item.created_at < since:
                continue
            processed += 1
            if _is_self_reinforcing(item):
                rejected_feedback_loops.append(item.id)
                continue
            if _requires_slow_layer_approval(item):
                approvals.append(
                    {
                        "item_id": item.id,
                        "reason": "core_identity_slow_layer_change",
                        "proposed_summary": _sanitize_text(item.content),
                    }
                )
                continue
            if _has_learning_signal(item):
                candidate = _candidate_from_episode(item)
                candidates.append(candidate)
                self.write(candidate)

        return ConsolidationReport(
            since=since,
            candidate_items=candidates,
            requires_approval=approvals,
            rejected_feedback_loops=rejected_feedback_loops,
            metrics={
                "processed": processed,
                "accepted_candidates": len(candidates),
                "requires_approval": len(approvals),
                "rejected_feedback_loops": len(rejected_feedback_loops),
            },
        )

    def decay(self) -> None:
        now = datetime.now(timezone.utc)
        for item in list(self._items.values()):
            last_signal = item.last_used_at or item.created_at
            age_days = max(0, (now - last_signal).days)
            if age_days < 30:
                continue
            decay_factor = 0.85 if item.confidence >= 0.6 else 0.5
            item.weight = round(max(0.05, item.weight * decay_factor), 4)


def distill_persona_descriptor(source: Tagged) -> Tagged:
    """把 C3 原始画像/语料在私有侧蒸馏为可外发云 LLM 的 C1 风格描述符。

    该函数不读取 raw_corpus，不复制可识别个人或私域线索，只保留显式给出的
    风格、价值观和禁忌词等非识别性描述。
    """
    payload = dict(source.payload or {})
    values = _string_list(payload.get("values") or payload.get("principles") or [])
    tone = _string_list(payload.get("tone") or payload.get("style") or [])
    taboo_words = _string_list(payload.get("taboo_words") or payload.get("avoid_words") or [])
    topic_preferences = _string_list(payload.get("topic_preferences") or [])

    descriptor = {
        "values": values,
        "tone": tone,
        "taboo_words": taboo_words,
        "topic_preferences": topic_preferences,
        "style_descriptor": _descriptor_text(values, tone, taboo_words, topic_preferences),
        "source_data_class": source.data_class.name,
        "cloud_llm_safe": True,
        "pii_removed": bool(source.pii or source.data_class == DataClass.C3_SECRET),
        "external_actions": [],
    }
    return Tagged(payload=descriptor, data_class=DataClass.C1_INTERNAL, pii=False)


def build_m3_persona_learning_report(source: Tagged, store: InMemoryPersonaMemoryStore) -> Tagged:
    """构建 M3 风格学习报告。

    输入可含 C3 画像与本地事件，但输出只能是 C1 汇总报告。核心身份变更只进入
    requires_approval，不直接写慢层。
    """
    descriptor = distill_persona_descriptor(source)
    payload = dict(source.payload or {})
    now = datetime.now(timezone.utc)
    for raw in list(payload.get("events") or []):
        event = dict(raw)
        item = MemoryItem(
            id=str(event.get("id") or f"event-{len(store.retrieve('', k=10_000)) + 1}"),
            kind=_memory_kind(event.get("kind")),
            content=str(event.get("content") or ""),
            data_class=_data_class(event.get("data_class"), default=source.data_class),
            confidence=_bounded(_number(event.get("confidence"), default=0.5)),
            source=str(event.get("source") or "manual_event"),
            created_at=_datetime(event.get("created_at"), default=now),
        )
        store.write(item)

    consolidation = store.consolidate(now.replace(microsecond=0))
    if consolidation.metrics.get("processed") == 0 and payload.get("events"):
        consolidation = store.consolidate(datetime.min.replace(tzinfo=timezone.utc))

    return Tagged(
        payload={
            "module": "m3_persona_memory",
            "descriptor": descriptor.payload,
            "consolidation": _report_payload(consolidation),
            "fast_layer_policy": "recent_trend_and_temporary_preference_only",
            "slow_layer_policy": "core_identity_changes_require_approval",
            "anti_echo_chamber": {
                "self_generated_acceptance_is_not_truth": True,
                "external_signal_or_explicit_owner_confirmation_required": True,
            },
            "privacy_boundary": {
                "raw_c3_retained_private": True,
                "cloud_payload_data_class": "C1_INTERNAL",
                "cloud_llm_safe_descriptor_only": True,
            },
            "external_actions": [],
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def _candidate_from_episode(item: MemoryItem) -> MemoryItem:
    kind = MemoryKind.SEMANTIC if item.source.startswith("explicit_owner_override") else MemoryKind.PROCEDURAL
    confidence = item.confidence
    if item.source.startswith("external_metric"):
        confidence = min(1.0, confidence + 0.08)
    if item.source.startswith("explicit_owner_override"):
        confidence = min(1.0, confidence + 0.12)
    return MemoryItem(
        id=f"{item.id}:consolidated",
        kind=kind,
        content=_sanitize_text(item.content),
        data_class=DataClass.C1_INTERNAL,
        confidence=round(confidence, 4),
        source=f"consolidated:{item.source}",
        created_at=datetime.now(timezone.utc),
        weight=round(min(1.0, max(0.1, item.weight)), 4),
    )


def _report_payload(report: ConsolidationReport) -> dict[str, Any]:
    return {
        "since": report.since.isoformat(),
        "candidate_items": [_memory_payload(item) for item in report.candidate_items],
        "requires_approval": report.requires_approval,
        "rejected_feedback_loops": report.rejected_feedback_loops,
        "metrics": report.metrics,
    }


def _memory_payload(item: MemoryItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "kind": item.kind.value,
        "content": item.content,
        "data_class": item.data_class.name,
        "confidence": item.confidence,
        "source": item.source,
        "weight": item.weight,
    }


def _descriptor_text(values: list[str], tone: list[str], taboo_words: list[str], topics: list[str]) -> str:
    parts = []
    if values:
        parts.append("价值观：" + "；".join(values[:6]))
    if tone:
        parts.append("语气：" + "；".join(tone[:6]))
    if taboo_words:
        parts.append("禁忌：" + "、".join(taboo_words[:12]))
    if topics:
        parts.append("偏好选题：" + "；".join(topics[:6]))
    return "；".join(parts) or "专业、克制、先证据后建议，避免医疗化和绝对化表达。"


def _has_learning_signal(item: MemoryItem) -> bool:
    return item.source.startswith("external_metric") or item.source.startswith("explicit_owner_override")


def _is_self_reinforcing(item: MemoryItem) -> bool:
    return item.source in _SELF_REINFORCING_SOURCES or item.source.startswith("model_output")


def _requires_slow_layer_approval(item: MemoryItem) -> bool:
    text = item.content
    return "core_identity" in item.source or "核心身份" in text or "人设" in text and "变更" in text


def _sanitize_text(text: str) -> str:
    sanitized = text
    sanitized = re.sub(r"\d{7,}", "[已脱敏数字]", sanitized)
    for marker in ("手机号", "手机", "微信", "客户"):
        if marker in sanitized:
            sanitized = sanitized.replace(marker, "[已脱敏]")
    return sanitized


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    else:
        values = list(value or [])
    safe_values = []
    for raw in values:
        rendered = str(raw).strip()
        if not rendered:
            continue
        if _looks_like_pii(rendered):
            continue
        safe_values.append(rendered)
    return safe_values


def _looks_like_pii(text: str) -> bool:
    digits = sum(ch.isdigit() for ch in text)
    return digits >= 7 or any(key in text.casefold() for key in _PII_KEYS)


def _memory_kind(value: Any) -> MemoryKind:
    try:
        return MemoryKind(str(value or MemoryKind.EPISODIC.value))
    except ValueError:
        return MemoryKind.EPISODIC


def _data_class(value: Any, *, default: DataClass) -> DataClass:
    if isinstance(value, DataClass):
        return value
    if isinstance(value, str):
        if value in DataClass.__members__:
            return DataClass[value]
        try:
            return DataClass(int(value))
        except (ValueError, TypeError):
            return default
    return default


def _datetime(value: Any, *, default: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return default
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    return default


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _number(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
