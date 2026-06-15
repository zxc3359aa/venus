import pytest

from venus.agents_sdk_runtime import AgentsSdkRuntimeConfig, build_agents_sdk_manifest


def _agents_sdk_payload(live_requested=True):
    return {
        "source": "manual_agents_sdk_review",
        "generated_at": "2026-06-15T12:00:00+08:00",
        "live_sdk_requested": live_requested,
        "openai_api_key": "secret-openai-token",
        "environment": {
            "OPENAI_API_KEY_configured": False,
            "openai_agents_installed": False,
            "deployment_manager_ready": False,
        },
        "agent_run": {
            "run_id": "venus-run-sdk-001",
            "executed_workflows": [
                "trend_scan",
                "product_intel",
                "content_eval",
                "performance",
                "connectors",
                "scheduler",
                "memory",
            ],
            "action_plan": [
                {
                    "action_type": "feishu_mobile_report",
                    "approval_level": 2,
                    "execution_state": "blocked_until_approved",
                    "external_action_enabled": False,
                }
            ],
            "external_actions": [],
        },
        "eval_report": {
            "summary": {
                "autopilot_ready": False,
                "readiness_status": "blocked_by_connector_readiness",
            }
        },
        "tool_overrides": [
            {
                "tool_name": "unsafe_live_douyin_reply",
                "workflow": "douyin",
                "description": "Attempt to reply publicly.",
                "approval_level": 4,
                "external_action_enabled": True,
            }
        ],
    }


def test_build_agents_sdk_manifest_blocks_live_sdk_until_environment_and_evals_ready():
    manifest = build_agents_sdk_manifest(_agents_sdk_payload())

    assert manifest["workflow"] == "agents_sdk"
    assert manifest["namespace"] == "venus_agents_sdk"
    assert manifest["sdk_mode"] == "manifest_only"
    assert manifest["external_actions"] == []
    assert manifest["summary"] == {
        "agent_count": 1,
        "tool_count": 16,
        "blocked_tool_count": 1,
        "readiness_blocker_count": 4,
        "approval_record_count": 1,
        "deployment_ready": False,
    }
    assert manifest["agent_manifest"]["name"] == "VenusSkincareOperator"
    assert manifest["agent_manifest"]["model_env_var"] == "VENUS_OPENAI_MODEL"
    assert "OPENAI_API_KEY" in manifest["runtime_plan"]["required_env"]

    tool_names = {item["tool_name"] for item in manifest["tool_registry"]}
    assert {"run_trend_scan", "build_product_intel", "draft_douyin_replies", "plan_airtable_sync"} <= tool_names
    assert {item["external_action_enabled"] for item in manifest["tool_registry"]} == {False}
    assert manifest["blocked_tools"][0]["tool_name"] == "unsafe_live_douyin_reply"
    assert manifest["blocked_tools"][0]["skip_reason"] == "external_tool_not_allowed"
    assert {item["blocker_id"] for item in manifest["deployment_readiness"]["blockers"]} == {
        "missing_openai_api_key",
        "missing_openai_agents_dependency",
        "evals_not_ready",
        "external_tool_blocked",
    }
    assert manifest["approval_records"][0]["action_type"] == "venus_agents_sdk_live_enablement_review"
    assert manifest["approval_records"][0]["approval_level"] == 4
    assert "secret-openai-token" not in str(manifest)
    assert "Xiaolongxia" not in str(manifest)
    assert "小龙虾" not in str(manifest)


def test_build_agents_sdk_manifest_can_be_ready_for_sdk_build_review_when_gates_clear():
    payload = _agents_sdk_payload(live_requested=False)
    payload["environment"] = {
        "OPENAI_API_KEY_configured": True,
        "openai_agents_installed": True,
        "deployment_manager_ready": True,
    }
    payload["eval_report"]["summary"] = {
        "autopilot_ready": True,
        "readiness_status": "ready_for_manual_autopilot_review",
    }
    payload["tool_overrides"] = []

    manifest = build_agents_sdk_manifest(payload)

    assert manifest["runtime_plan"]["readiness_state"] == "ready_for_sdk_build_review"
    assert manifest["summary"]["deployment_ready"] is True
    assert manifest["summary"]["readiness_blocker_count"] == 0
    assert manifest["approval_records"] == []


def test_agents_sdk_runtime_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        AgentsSdkRuntimeConfig(namespace="xiaolongxia_agents_sdk")
