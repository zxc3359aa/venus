from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from venus.dashboard import build_dashboard_html
from venus.feishu_entry import run_feishu_entry
from venus.orchestrator import VenusOrchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="venus")
    parser.add_argument(
        "workflow",
        choices=[
            "hotspot",
            "product",
            "comments",
            "monitoring",
            "airtable",
            "douyin",
            "wechat",
            "commercial",
            "improvement",
            "production",
            "agent-run",
            "dashboard",
            "feishu",
        ],
    )
    parser.add_argument("input", help="Path to a JSON input file")
    parser.add_argument("output", nargs="?", help="Optional output path for dashboard HTML")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    records = json.loads(input_path.read_text(encoding="utf-8"))
    if args.workflow == "feishu":
        result = run_feishu_entry(records, workspace_root=Path.cwd())
    elif args.workflow == "dashboard":
        result = _run_dashboard(records, args.output)
    else:
        payload = _payload_for(args.workflow, records)
        orchestrator_workflow = "agent_run" if args.workflow == "agent-run" else args.workflow
        result = VenusOrchestrator().run(orchestrator_workflow, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _payload_for(workflow: str, records: Any) -> dict[str, Any]:
    if workflow == "hotspot":
        return {"hotspots": records}
    if workflow == "product":
        return {"products": records}
    if workflow == "comments":
        return {"comments": records}
    if workflow == "monitoring":
        return records
    if workflow == "airtable":
        return records
    if workflow == "douyin":
        return records
    if workflow == "wechat":
        return records
    if workflow == "commercial":
        return records
    if workflow == "improvement":
        return records
    if workflow == "production":
        return records
    if workflow == "agent-run":
        return records
    raise ValueError(f"Unsupported Venus workflow: {workflow}")


def _run_dashboard(records: dict[str, Any], output: str | None) -> dict[str, Any]:
    dashboard = build_dashboard_html(records)
    result: dict[str, Any] = {
        "summary": dashboard["summary"],
        "external_actions": dashboard["external_actions"],
    }
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dashboard["html"], encoding="utf-8")
        result["output_path"] = str(output_path)
    else:
        result["html"] = dashboard["html"]
    return {
        "workflow": "dashboard",
        "approval_mode": "manual",
        "external_actions": [],
        "result": result,
    }


if __name__ == "__main__":
    raise SystemExit(main())
