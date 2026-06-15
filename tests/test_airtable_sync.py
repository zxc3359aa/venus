import pytest

from venus.airtable_sync import AirtableSyncPlanConfig, build_airtable_sync_plan
from venus.storage import JsonStore


def _airtable_sync_payload(tmp_workspace, approved=True):
    return {
        "source": "manual_airtable_sync_plan",
        "workspace_root": str(tmp_workspace),
        "planned_at": "2026-06-15T11:20:00+08:00",
        "sync_requested": True,
        "approved_sync_review": approved,
        "access_token": "secret-airtable-token",
        "airtable_package": {
            "base": {
                "name": "Venus Ops",
                "namespace": "venus_airtable",
                "description": "Venus beauty and skincare operations base package.",
            },
            "tables": [
                {
                    "name": "Hotspots",
                    "fields": [
                        {"name": "Name", "type": "singleLineText"},
                        {"name": "Topic", "type": "singleLineText"},
                    ],
                    "records": [
                        {"fields": {"Name": "早C晚A翻车", "Topic": "早C晚A翻车"}},
                        {"fields": {"Name": "夏季防晒补涂", "Topic": "夏季防晒补涂"}},
                    ],
                },
                {
                    "name": "Approvals",
                    "fields": [
                        {"name": "Name", "type": "singleLineText"},
                        {"name": "Status", "type": "singleSelect"},
                    ],
                    "records": [
                        {"fields": {"Name": "airtable_sync_review", "Status": "approved"}}
                    ],
                },
                {
                    "name": "Broken Products",
                    "fields": [{"name": "Name", "type": "singleLineText"}],
                    "records": [
                        {"fields": {"Name": "屏障修护精华", "Unexpected Field": "bad"}}
                    ],
                },
                {
                    "name": "External Table",
                    "fields": [{"name": "Name", "type": "singleLineText"}],
                    "records": [{"fields": {"Name": "should block"}}],
                    "external_action_enabled": True,
                },
            ],
            "summary": {"table_count": 4, "record_count": 5},
            "sync_boundary": {"can_import_later": True},
        },
        "connector_reviews": [
            {
                "connector_id": "airtable-ops",
                "surface": "airtable",
                "status": "ready",
                "permissions_granted": ["base_read", "record_write"],
                "audit_ready": True,
                "rollback_ready": True,
                "approval_level": 2,
                "external_action_enabled": False,
            }
        ],
    }


def test_build_airtable_sync_plan_records_valid_tables_and_blocks_unsafe_tables(tmp_workspace):
    report = build_airtable_sync_plan(_airtable_sync_payload(tmp_workspace))

    assert report["workflow"] == "airtable_sync_plan"
    assert report["namespace"] == "venus_airtable_sync"
    assert report["approval_mode"] == "manual"
    assert report["external_actions"] == []
    assert report["sync_state"] == "planned"
    assert report["summary"] == {
        "table_count": 4,
        "planned_count": 2,
        "duplicate_count": 0,
        "blocked_count": 2,
        "record_count": 5,
        "stored_total_count": 2,
    }

    plans = {item["table_name"]: item for item in report["sync_plan_records"]}
    assert plans["Hotspots"]["planned_operation"] == "create_or_update_records"
    assert plans["Hotspots"]["record_count"] == 2
    assert plans["Hotspots"]["execution_state"] == "local_sync_plan_ready"
    assert plans["Approvals"]["field_count"] == 2
    assert {item["skip_reason"] for item in report["blocked_tables"]} == {
        "schema_field_mismatch",
        "external_table_action_enabled",
    }
    assert report["write_plan"]["target_collection"] == "airtable_sync_plans"
    assert report["rollback_plan"]["sync_plan_ids_to_remove"] == [
        item["sync_plan_id"] for item in report["sync_plan_records"]
    ]

    stored = JsonStore(tmp_workspace).read_collection("airtable_sync_plans")
    assert stored == report["sync_plan_records"]
    assert "secret-airtable-token" not in str(report)
    assert "Xiaolongxia" not in str(report)
    assert "小龙虾" not in str(report)


def test_build_airtable_sync_plan_blocks_without_ready_airtable_connector(tmp_workspace):
    payload = _airtable_sync_payload(tmp_workspace)
    payload["connector_reviews"] = [
        {
            "connector_id": "airtable-ops",
            "surface": "airtable",
            "status": "missing_permission",
            "permissions_granted": ["base_read"],
            "audit_ready": True,
            "rollback_ready": True,
            "external_action_enabled": False,
        }
    ]

    report = build_airtable_sync_plan(payload)

    assert report["sync_state"] == "blocked_connector_not_ready"
    assert report["summary"]["planned_count"] == 0
    assert report["summary"]["blocked_count"] == 4
    assert {item["skip_reason"] for item in report["blocked_tables"]} == {
        "connector_not_ready"
    }
    assert not (tmp_workspace / "data" / "venus" / "airtable_sync_plans.json").exists()


def test_build_airtable_sync_plan_is_idempotent_for_existing_local_plans(tmp_workspace):
    first = build_airtable_sync_plan(_airtable_sync_payload(tmp_workspace))
    second = build_airtable_sync_plan(_airtable_sync_payload(tmp_workspace))

    assert first["summary"]["planned_count"] == 2
    assert second["summary"]["planned_count"] == 0
    assert second["summary"]["duplicate_count"] == 2
    assert second["sync_state"] == "already_planned"
    stored = JsonStore(tmp_workspace).read_collection("airtable_sync_plans")
    assert len(stored) == 2


def test_build_airtable_sync_plan_blocks_without_sync_review(tmp_workspace):
    report = build_airtable_sync_plan(_airtable_sync_payload(tmp_workspace, approved=False))

    assert report["sync_state"] == "blocked_until_sync_review"
    assert report["summary"]["planned_count"] == 0
    assert report["write_plan"]["execution_state"] == "blocked_until_sync_review"
    assert not (tmp_workspace / "data" / "venus" / "airtable_sync_plans.json").exists()
    assert report["external_actions"] == []


def test_airtable_sync_plan_config_rejects_xiaolongxia_namespace(tmp_workspace):
    with pytest.raises(ValueError, match="Xiaolongxia"):
        AirtableSyncPlanConfig(
            workspace_root=tmp_workspace,
            namespace="xiaolongxia_airtable_sync",
        )
