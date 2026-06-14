from venus.models import Evidence
from venus.storage import JsonStore, VenusPaths


def test_venus_paths_use_isolated_namespace(tmp_workspace):
    paths = VenusPaths(root=tmp_workspace)

    assert paths.root == tmp_workspace
    assert paths.data_dir == tmp_workspace / "data" / "venus"
    assert paths.logs_dir == tmp_workspace / "logs" / "venus"
    assert paths.env_prefix == "VENUS_"


def test_json_store_round_trips_records(tmp_workspace):
    store = JsonStore(tmp_workspace)
    evidence = Evidence(
        source_id="nmpa-001",
        source_type="regulator",
        title="NMPA cosmetics filing lookup",
        url="https://www.nmpa.gov.cn/datasearch/home-index.html",
        retrieved_at="2026-06-14T00:00:00+08:00",
        confidence="high",
        notes=["Official regulator source"],
    )

    store.write_collection("sources", [evidence.to_dict()])

    records = store.read_collection("sources")
    assert records == [evidence.to_dict()]
    assert (tmp_workspace / "data" / "venus" / "sources.json").exists()


def test_json_store_rejects_xiaolongxia_collection_name(tmp_workspace):
    store = JsonStore(tmp_workspace)

    try:
        store.write_collection("xiaolongxia_secrets", [])
    except ValueError as exc:
        assert "Xiaolongxia" in str(exc)
    else:
        raise AssertionError("Expected Xiaolongxia isolation guard to reject collection")
