from pathlib import Path

import pytest


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "venus-workspace"
    workspace.mkdir()
    return workspace
