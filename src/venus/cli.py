from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from venus.feishu_entry import run_feishu_entry
from venus.orchestrator import VenusOrchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="venus")
    parser.add_argument("workflow", choices=["hotspot", "product", "comments", "monitoring", "feishu"])
    parser.add_argument("input", help="Path to a JSON input file")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    records = json.loads(input_path.read_text(encoding="utf-8"))
    if args.workflow == "feishu":
        result = run_feishu_entry(records, workspace_root=Path.cwd())
    else:
        payload = _payload_for(args.workflow, records)
        result = VenusOrchestrator().run(args.workflow, payload)
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
    raise ValueError(f"Unsupported Venus workflow: {workflow}")


if __name__ == "__main__":
    raise SystemExit(main())
