"""项目级合规门与契约核对脚本。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts import contract_conformance


ROOT = Path(__file__).resolve().parents[1]


def _run(script: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_compliance_gate_script_passes_current_m0_tree():
    result = _run("compliance_gate.py")

    assert result.returncode == 0, result.stdout + result.stderr


def test_contract_conformance_script_passes_current_m0_tree():
    result = _run("contract_conformance.py")

    assert result.returncode == 0, result.stdout + result.stderr


def test_contract_conformance_checks_m2_output_shape():
    assert contract_conformance._check_m2_contracts() == []


def test_contract_conformance_checks_m3_memory_shape():
    assert contract_conformance._check_m3_contracts() == []


def test_contract_conformance_checks_m4_community_shape():
    assert contract_conformance._check_m4_contracts() == []


def test_contract_conformance_checks_m5_video_shape():
    assert contract_conformance._check_m5_contracts() == []


def test_contract_conformance_checks_m6_private_domain_shape():
    assert contract_conformance._check_m6_contracts() == []


def test_contract_conformance_checks_m7_ads_shape():
    assert contract_conformance._check_m7_contracts() == []


def test_contract_conformance_checks_m8_benchmark_shape():
    assert contract_conformance._check_m8_contracts() == []


def test_contract_conformance_checks_m9_evolution_shape():
    assert contract_conformance._check_m9_contracts() == []
