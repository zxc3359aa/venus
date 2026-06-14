from venus.storage import VenusPaths


def test_venus_paths_use_isolated_namespace(tmp_workspace):
    paths = VenusPaths(root=tmp_workspace)

    assert paths.root == tmp_workspace
    assert paths.data_dir == tmp_workspace / "data" / "venus"
    assert paths.logs_dir == tmp_workspace / "logs" / "venus"
    assert paths.env_prefix == "VENUS_"
