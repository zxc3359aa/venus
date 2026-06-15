"""确定性内容评测器（规格 §0/§12：LLM 相关逻辑需 golden 评测）。

运行： python eval/scorer.py
对 golden_set.jsonl 逐条用 validate_copy 评判，统计通过率。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from venus.modules.m1_hotspot import validate_copy  # noqa: E402


def run(path: str) -> bool:
    total = passed = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            total += 1
            issues = validate_copy(case["text"])
            ok = (len(issues) == 0) == bool(case["should_pass"])
            passed += 1 if ok else 0
            print(("OK  " if ok else "FAIL"), case.get("name"), "->", issues or "通过")
    print(f"score: {passed}/{total}")
    return passed == total


if __name__ == "__main__":
    ok = run(os.path.join(os.path.dirname(__file__), "golden_set.jsonl"))
    sys.exit(0 if ok else 1)
