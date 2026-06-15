import os
import sys
import shutil
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = str(PROJECT_ROOT / "src")
pytest_pythonpath = os.environ.get("PYTHONPATH", "")
if SRC_ROOT not in pytest_pythonpath.split(os.pathsep):
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [p for p in [SRC_ROOT, pytest_pythonpath] if p]
    )


@pytest.fixture
def tmp_workspace(tmp_path):
    src_samples = PROJECT_ROOT / "data" / "samples"
    if src_samples.exists():
        shutil.copytree(
            src_samples,
            tmp_path / "data" / "samples",
            dirs_exist_ok=True,
        )
    return tmp_path
