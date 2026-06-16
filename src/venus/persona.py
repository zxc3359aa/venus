from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PersonaProfile:
    principles: list[str]
    preferred_phrases: list[str]
    banned_claims: list[str]
    tone: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_persona_profile(samples: list[str]) -> PersonaProfile:
    joined = "\n".join(samples)
    principles: list[str] = []
    preferred_phrases: list[str] = []

    if "屏障" in joined:
        principles.append("先看屏障状态")
    if "证据" in joined or "体验" in joined:
        principles.append("证据和体验都要说清楚")
    if "姐妹们" in joined:
        preferred_phrases.append("姐妹们")

    if not principles:
        principles.append("先判断肤质和使用场景")
    if not preferred_phrases:
        preferred_phrases.append("姐妹们")

    return PersonaProfile(
        principles=principles,
        preferred_phrases=preferred_phrases,
        banned_claims=["包治", "根治", "100%有效", "永久解决"],
        tone="专业、口语化、克制",
    )


def rewrite_in_persona(draft: str, profile: PersonaProfile) -> str:
    cleaned = draft
    for claim in profile.banned_claims:
        cleaned = cleaned.replace(claim, "")

    opener = profile.preferred_phrases[0] if profile.preferred_phrases else "姐妹们"
    principle = profile.principles[0] if profile.principles else "先判断肤质和使用场景"
    return f"{opener}，{cleaned}但我会先提醒一句：{principle}，再看证据和自己的耐受。"
