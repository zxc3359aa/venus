"""M1 热点/文案模块的可运行最小切片（规格 §8 M1，修订 B5）。

- map_reduce_summarize：大输入分块汇总（map）再归并（reduce），防超 LLM 上下文窗口。
- validate_copy：中文文案质量/合规校验器（示例规则集；广告法风险词拦截）。
- build_publish_action：构造“发布视频”这一不可逆动作（须走审批）。
"""
from __future__ import annotations

from typing import Any

from venus.contracts import Action, DataClass, LLMMessage, Tagged

# 广告法/医疗宣称风险词（示例；生产应扩展为可配置词库 + 模型判别）
BANNED_WORDS = ["全网最", "最有效", "第一", "100%", "根治", "治愈", "纯天然无添加"]

# 3 秒钩子线索（示例）
HOOK_CUES = ["你知道", "千万别", "其实", "为什么", "我后悔", "三秒", "别再"]


def validate_copy(text: str) -> list[str]:
    """返回问题列表；空列表=通过。"""
    issues: list[str] = []
    if not any(cue in text for cue in HOOK_CUES):
        issues.append("缺少3秒钩子")
    if ("评论" not in text) and ("扣" not in text):
        issues.append("缺少评论诱饵")
    if "关注" not in text:
        issues.append("缺少关注理由")
    for w in BANNED_WORDS:
        if w in text:
            issues.append(f"广告法风险词: {w}")
    return issues


def map_reduce_summarize(llm, chunks: list[str], *, max_tokens: int = 256) -> str:
    """对海量热点/评论先分块提炼（map），再归并成简报（reduce）。"""
    partials: list[str] = []
    for chunk in chunks:
        r = llm.complete(
            [LLMMessage("system", "提炼要点"), LLMMessage("user", chunk)],
            max_tokens=max_tokens,
        )
        partials.append(r.text)
    joined = "\n".join(partials)
    r = llm.complete(
        [LLMMessage("system", "汇总要点成简报"), LLMMessage("user", joined)],
        max_tokens=max_tokens,
    )
    return r.text


def build_publish_action(brief: str) -> Action:
    return Action(
        kind="publish_video",
        summary=f"发布基于简报的视频：{brief[:30]}",
        payload={"brief": brief},
        idempotency_key=f"pub-{abs(hash(brief)) % 10**8}",
        data_class=DataClass.C1_INTERNAL,
        reversible=False,  # 发布到平台 = 不可逆 → 必须经审批
    )


def build_m1_hotspot_package(source: Tagged, llm, *, max_tokens: int = 256) -> Tagged:
    """构建 M1 热点雷达 + 文案建议包。

    M1 只处理 C0/C1 数据；任何 C2/C3 个性化或私域数据必须先在私有侧降级为 C1
    风格描述符后再进入本模块。
    """
    if source.data_class.value > DataClass.C1_INTERNAL.value:
        raise ValueError("M1 hotspot package only accepts C0/C1 inputs; C2/C3 must be reduced first")

    payload = dict(source.payload or {})
    raw_hotspots = [dict(item) for item in list(payload.get("hotspots") or [])]
    comments = [str(item) for item in list(payload.get("comments") or [])]
    persona_descriptor = str(payload.get("persona_descriptor") or "先看屏障状态，证据和体验都要说清楚。")

    signals = [_normalize_signal(item) for item in raw_hotspots]
    signals.sort(key=lambda item: item["score"], reverse=True)
    top = signals[0] if signals else _empty_signal()

    brief = map_reduce_summarize(
        llm,
        _summary_chunks(signals, comments),
        max_tokens=max_tokens,
    )
    script = _script_package(top["topic"], persona_descriptor)
    shooting_advice = _shooting_advice(top)

    return Tagged(
        payload={
            "module": "m1_hotspot",
            "brief": brief,
            "top_signal": top,
            "signals": signals,
            "script": script,
            "shooting_advice": shooting_advice,
            "copy_issues": validate_copy(script["full_text"]),
            "external_actions": [],
            "safety_boundary": {
                "data_source_tier": "tier_a_or_b_only",
                "tier_c_blocked": True,
                "irreversible_actions_require_approval": True,
            },
        },
        data_class=DataClass.C1_INTERNAL,
        pii=False,
    )


def _normalize_signal(item: dict[str, Any]) -> dict[str, Any]:
    topic = str(item.get("topic") or item.get("label") or "未命名热点")
    mentions = int(_number(item.get("mentions")))
    growth = _bounded(_number(item.get("growth")))
    controversy = _bounded(_number(item.get("controversy")))
    relevance = _bounded(_number(item.get("relevance"), default=0.75))
    evidence = _unique_strings(item.get("evidence") or item.get("sources") or [])
    score = round(
        min(1.0, mentions / 100_000) * 0.35
        + growth * 0.3
        + controversy * 0.2
        + relevance * 0.15,
        4,
    )
    controversy_verified = controversy < 0.6 or len(evidence) >= 2
    return {
        "topic": topic,
        "mentions": mentions,
        "growth": growth,
        "controversy": controversy,
        "relevance": relevance,
        "score": score,
        "evidence": evidence,
        "controversy_verified": controversy_verified,
        "manual_cross_check_required": not controversy_verified,
    }


def _summary_chunks(signals: list[dict[str, Any]], comments: list[str]) -> list[str]:
    if not signals and not comments:
        return ["暂无热点输入，请等待合规数据源回填。"]
    chunks = []
    for signal in signals:
        chunks.append(
            " | ".join(
                [
                    f"topic={signal['topic']}",
                    f"mentions={signal['mentions']}",
                    f"growth={signal['growth']}",
                    f"controversy={signal['controversy']}",
                    f"evidence_count={len(signal['evidence'])}",
                ]
            )
        )
    if comments:
        chunks.append("评论关注点：" + "；".join(comments[:12]))
    return chunks


def _script_package(topic: str, persona_descriptor: str) -> dict[str, str]:
    hook = f"千万别急着跟风{topic}，三秒先看你是不是高风险。"
    body = (
        f"{persona_descriptor} 今天用一个简单顺序拆：先看屏障状态，"
        "再看刺激叠加，最后看证据来源。敏感、爆皮、刺痛的人先暂停叠加，"
        "把产品名和使用频率写清楚。"
    )
    cta = "评论区留下肤质+产品名+频率，我按屏障、成分叠加和证据帮你拆；关注我，少踩一次护肤坑。"
    return {
        "topic": topic,
        "hook": hook,
        "body": body,
        "comment_prompt": "评论区留下肤质+产品名+频率。",
        "follow_reason": "关注我，少踩一次护肤坑。",
        "full_text": f"{hook}{body}{cta}",
    }


def _shooting_advice(signal: dict[str, Any]) -> list[str]:
    topic = str(signal.get("topic") or "热点")
    advice = [
        f"开头 3 秒直接展示“{topic}”相关评论截图或标题卡。",
        "中段用成分表/使用频率/屏障状态三连镜头做证据化解释。",
        "结尾放评论区问题模板，引导用户留下肤质、产品名和频率。",
    ]
    if signal.get("manual_cross_check_required"):
        advice.append("争议证据不足，发布前先补第二来源或改为“待核实讨论”。")
    return advice


def _empty_signal() -> dict[str, Any]:
    return {
        "topic": "暂无热点",
        "mentions": 0,
        "growth": 0.0,
        "controversy": 0.0,
        "relevance": 0.0,
        "score": 0.0,
        "evidence": [],
        "controversy_verified": True,
        "manual_cross_check_required": False,
    }


def _unique_strings(values: Any) -> list[str]:
    unique = []
    for value in list(values or []):
        rendered = str(value)
        if rendered and rendered not in unique:
            unique.append(rendered)
    return unique


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _number(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
