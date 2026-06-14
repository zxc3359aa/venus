from __future__ import annotations

from typing import Any

from venus.comments import analyze_comments
from venus.content import generate_hotspot_brief
from venus.monitoring import build_monitoring_report
from venus.persona import build_persona_profile
from venus.product_research import build_product_research_card


class VenusOrchestrator:
    def run(self, workflow: str, payload: dict[str, Any]) -> dict[str, Any]:
        persona_samples = payload.get(
            "persona_samples",
            ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        )
        profile = build_persona_profile(list(persona_samples))

        if workflow == "hotspot":
            result = generate_hotspot_brief(list(payload["hotspots"]), profile)
        elif workflow == "product":
            products = list(payload["products"])
            result = build_product_research_card(products[0])
        elif workflow == "comments":
            result = analyze_comments(list(payload["comments"]), profile)
        elif workflow == "monitoring":
            result = build_monitoring_report(payload)
        else:
            raise ValueError(f"Unsupported Venus workflow: {workflow}")

        return {
            "workflow": workflow,
            "approval_mode": "manual",
            "external_actions": [],
            "result": result,
        }
