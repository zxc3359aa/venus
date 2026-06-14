import json
import subprocess
import sys

from venus.orchestrator import VenusOrchestrator


def test_orchestrator_routes_hotspot_workflow():
    orchestrator = VenusOrchestrator()
    result = orchestrator.run(
        "hotspot",
        {
            "hotspots": [
                {
                    "topic": "早C晚A翻车",
                    "type": "controversy",
                    "freshness": 9,
                    "relevance": 10,
                    "controversy": 8,
                    "evidence": ["douyin-export-001"],
                }
            ],
            "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        },
    )

    assert result["workflow"] == "hotspot"
    assert result["result"]["top_topic"] == "早C晚A翻车"


def test_orchestrator_routes_monitoring_workflow():
    orchestrator = VenusOrchestrator()
    result = orchestrator.run(
        "monitoring",
        {
            "competitors": [
                {
                    "handle": "成分党A",
                    "videos": [
                        {
                            "title": "早C晚A翻车自查",
                            "topic": "早C晚A翻车",
                            "views": 120000,
                            "likes": 9800,
                            "comments": 1680,
                            "shares": 2400,
                            "completion_rate": 0.72,
                            "is_ad": False,
                        }
                    ],
                    "live_sessions": [{"duration_minutes": 60}],
                }
            ]
        },
    )

    assert result["workflow"] == "monitoring"
    assert result["external_actions"] == []
    assert result["result"]["summary"]["top_account"] == "成分党A"


def test_orchestrator_routes_airtable_workflow():
    orchestrator = VenusOrchestrator()
    result = orchestrator.run(
        "airtable",
        {
            "hotspots": [
                {
                    "topic": "早C晚A翻车",
                    "type": "controversy",
                    "freshness": 9,
                    "relevance": 10,
                    "controversy": 8,
                    "evidence": ["douyin-export-001"],
                }
            ],
            "products": [],
            "comments": [],
            "competitors": {"competitors": []},
            "approvals": [],
        },
    )

    assert result["workflow"] == "airtable"
    assert result["external_actions"] == []
    assert result["result"]["base"]["namespace"] == "venus_airtable"


def test_cli_hotspot_outputs_json(tmp_path):
    payload = [
        {
            "topic": "早C晚A翻车",
            "type": "controversy",
            "freshness": 9,
            "relevance": 10,
            "controversy": 8,
            "evidence": ["douyin-export-001"],
        }
    ]
    input_file = tmp_path / "hotspots.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "venus.cli", "hotspot", str(input_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "hotspot"
    assert output["result"]["top_topic"] == "早C晚A翻车"


def test_cli_monitoring_outputs_json():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "monitoring",
            "data/samples/competitors.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "monitoring"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["top_account"] == "成分党A"


def test_cli_airtable_outputs_json():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "airtable",
            "data/samples/airtable_export.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "airtable"
    assert output["external_actions"] == []
    assert output["result"]["base"]["name"] == "Venus Ops"


def test_cli_douyin_outputs_approval_gated_engagement_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "douyin",
            "data/samples/douyin_engagement.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "douyin"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["comment_count"] == 2
    assert output["result"]["summary"]["live_message_count"] == 1
    assert output["result"]["summary"]["approval_gated_reply_count"] == 2
    assert output["result"]["reply_queue"][0]["execution_state"] == "blocked_until_approved"


def test_cli_wechat_outputs_private_domain_handoff_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "wechat",
            "data/samples/wechat_private_domain.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "wechat"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["question_count"] == 2
    assert output["result"]["summary"]["enterprise_wechat_handoff_count"] == 1
    assert output["result"]["summary"]["approval_gated_action_count"] == 2
    assert output["result"]["handoff_queue"][0]["execution_state"] == "blocked_until_approved"


def test_cli_commercial_outputs_ad_strategy_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "commercial",
            "data/samples/commercial_strategy.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "commercial"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["qianchuan_campaign_count"] == 1
    assert output["result"]["summary"]["xingtu_brief_count"] == 1
    assert output["result"]["summary"]["approval_gated_action_count"] == 3
    assert output["result"]["qianchuan_recommendations"][0]["execution_state"] == "blocked_until_approved"


def test_cli_improvement_outputs_self_improvement_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "improvement",
            "data/samples/self_improvement.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "improvement"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["learning_candidate_count"] == 2
    assert output["result"]["summary"]["backup_issue_count"] == 1
    assert output["result"]["summary"]["approval_gated_action_count"] == 4
    assert output["result"]["backup_tasks"][0]["execution_state"] == "blocked_until_approved"


def test_cli_production_outputs_video_production_package():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "production",
            "data/samples/video_production.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "production"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["scene_count"] == 5
    assert output["result"]["summary"]["subtitle_card_count"] == 5
    assert output["result"]["summary"]["approval_gated_action_count"] == 2
    assert output["result"]["edit_plan"]["timeline"][0]["cut_style"] == "jump_cut"


def test_cli_content_eval_outputs_growth_and_safety_gate():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "content-eval",
            "data/samples/content_eval.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "content_eval"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["overall_score"] == 87
    assert output["result"]["summary"]["blocking_issue_count"] == 1
    assert output["result"]["publish_readiness"]["status"] == "blocked_by_claim_risk"
    assert output["result"]["scorecard"]["comment_score"]["score"] >= 90


def test_cli_performance_outputs_content_calibration_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "performance",
            "data/samples/performance.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "performance"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["winner_count"] == 2
    assert output["result"]["summary"]["underperformer_count"] == 1
    assert output["result"]["leaderboard"][0]["video_id"] == "video-001"


def test_cli_evals_outputs_agent_gate_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "evals",
            "data/samples/evals.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "evals"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["readiness_status"] == "blocked_by_connector_readiness"
    assert output["result"]["failed_gates"][0]["gate_id"] == "connector_readiness"


def test_cli_approvals_outputs_manual_review_inbox():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "approvals",
            "data/samples/approvals.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "approvals"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["pending_count"] == 4
    assert output["result"]["priority_queue"][0]["action_type"] == "venus_autopilot_enablement_review"


def test_cli_approval_ledger_outputs_decision_ledger_draft():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "approval-ledger",
            "data/samples/approval_ledger.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "approval_ledger"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["new_entry_count"] == 2
    assert output["result"]["duplicate_intents"][0]["action_type"] == "feishu_mobile_report"


def test_cli_approval_archive_persists_to_tmp_workspace(tmp_path):
    payload = {
        "source": "manual_approval_archive",
        "recorded_at": "2026-06-14T23:20:00+08:00",
        "workspace_root": str(tmp_path),
        "archive_requested": True,
        "approved_ledger_write_review": True,
        "write_requested": True,
        "approval_records": [
            {
                "action_type": "douyin_comment_reply_queue",
                "approval_level": 3,
                "draft": "Review high-risk Douyin reply drafts.",
                "evidence_ids": ["comment-001"],
                "status": "pending",
                "reviewer": "owner",
                "created_at": "2026-06-14T21:10:00+08:00",
            }
        ],
        "requested_decisions": [
            {
                "action_type": "douyin_comment_reply_queue",
                "decision": "reject",
                "reason": "回复语气还需要更克制。",
                "reviewer": "owner",
            }
        ],
        "existing_ledger_entries": [],
    }
    input_file = tmp_path / "approval_archive.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "approval-archive",
            str(input_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "approval_archive"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["archived_count"] == 1
    stored_file = tmp_path / "data" / "venus" / "approval_decision_ledger.json"
    assert stored_file.exists()
    assert "douyin_comment_reply_queue" in stored_file.read_text(encoding="utf-8")


def test_cli_action_outbox_persists_to_tmp_workspace(tmp_path):
    payload = {
        "source": "manual_action_outbox",
        "workspace_root": str(tmp_path),
        "queued_at": "2026-06-14T23:40:00+08:00",
        "execution_requested": True,
        "approved_execution_review": True,
        "action_plan": [
            {
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "surface": "feishu",
                "approval_level": 2,
                "draft": "Prepare a private Feishu card summary.",
                "external_action_enabled": False,
            }
        ],
        "archived_decisions": [
            {
                "decision_id": "feishu_mobile_report-approve-owner-feishu_mobile_report-20260614-2000000800",
                "action_type": "feishu_mobile_report",
                "decision": "approve",
                "reviewer": "owner",
                "approval_level": 2,
                "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                "archive_state": "archived",
                "record_state": "ready_for_local_ledger_review",
            }
        ],
    }
    input_file = tmp_path / "action_outbox.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "action-outbox",
            str(input_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "action_outbox"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["queued_count"] == 1
    stored_file = tmp_path / "data" / "venus" / "action_outbox.json"
    assert stored_file.exists()
    assert "feishu_mobile_report" in stored_file.read_text(encoding="utf-8")


def test_cli_delivery_drafts_persists_to_tmp_workspace(tmp_path):
    payload = {
        "source": "manual_delivery_drafts",
        "workspace_root": str(tmp_path),
        "drafted_at": "2026-06-15T09:10:00+08:00",
        "delivery_requested": True,
        "approved_delivery_review": True,
        "outbox_items": [
            {
                "outbox_id": "outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "surface": "feishu",
                "approval_level": 2,
                "decision_id": "decision-001",
                "matched_approval_id": "feishu_mobile_report-20260614-2000000800",
                "reviewer": "owner",
                "draft": "Prepare a private Feishu card summary.",
                "queued_at": "2026-06-14T23:40:00+08:00",
                "execution_state": "queued_local_outbox",
                "delivery_state": "local_manual_dispatch_required",
                "external_action_enabled": False,
            }
        ],
    }
    input_file = tmp_path / "delivery_drafts.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "delivery-drafts",
            str(input_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "delivery_drafts"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["drafted_count"] == 1
    stored_file = tmp_path / "data" / "venus" / "delivery_drafts.json"
    assert stored_file.exists()
    assert "feishu_card_draft" in stored_file.read_text(encoding="utf-8")


def test_cli_delivery_status_persists_to_tmp_workspace(tmp_path):
    payload = {
        "source": "manual_delivery_status",
        "workspace_root": str(tmp_path),
        "recorded_at": "2026-06-15T10:20:00+08:00",
        "status_update_requested": True,
        "approved_status_review": True,
        "draft_records": [
            {
                "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "outbox_id": "outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "action_id": "feishu-report-001",
                "action_type": "feishu_mobile_report",
                "artifact_type": "feishu_card_draft",
                "target_surface": "feishu",
                "dispatch_state": "local_review_required",
                "external_action_enabled": False,
            }
        ],
        "status_events": [
            {
                "draft_id": "draft-outbox-feishu_mobile_report-feishu-report-001-decision-001",
                "delivery_status": "manual_dispatch_completed",
                "reviewer": "owner",
                "event_time": "2026-06-15T10:00:00+08:00",
                "notes": "Copied the private Feishu card manually.",
                "evidence_ids": ["manual-feishu-001"],
                "external_action_enabled": False,
            }
        ],
    }
    input_file = tmp_path / "delivery_status.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "delivery-status",
            str(input_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "delivery_status"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["recorded_count"] == 1
    stored_file = tmp_path / "data" / "venus" / "delivery_status.json"
    assert stored_file.exists()
    assert "manual_dispatch_completed" in stored_file.read_text(encoding="utf-8")


def test_cli_trend_scan_outputs_douyin_beauty_signal_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "trend-scan",
            "data/samples/trend_scan.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "trend_scan"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["signal_count"] == 7
    assert output["result"]["summary"]["content_opportunity_count"] == 3
    assert output["result"]["leaderboard"][0]["label"] == "早C晚A翻车"
    assert output["result"]["watch_plan"]["refresh_interval_minutes"] == 15


def test_cli_product_intel_outputs_precise_research_dossier():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "product-intel",
            "data/samples/product_intelligence.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "product_intel"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["ingredient_count"] == 2
    assert output["result"]["summary"]["missing_supplier_document_count"] == 1
    assert output["result"]["summary"]["retrieval_task_count"] == 5
    assert output["result"]["claim_risk"]["risk_level"] == "high"


def test_cli_ecommerce_outputs_shop_operations_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "ecommerce",
            "data/samples/ecommerce.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "ecommerce"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["product_count"] == 2
    assert output["result"]["summary"]["low_stock_count"] == 1
    assert output["result"]["summary"]["approval_gated_action_count"] == 3
    assert output["result"]["live_product_card_plan"][0]["execution_state"] == "blocked_until_approved"


def test_cli_memory_outputs_versioned_memory_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "memory",
            "data/samples/memory.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "memory"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["current_version"] == "v3"
    assert output["result"]["summary"]["proposed_version"] == "v4"
    assert output["result"]["summary"]["proposed_change_count"] == 1
    assert output["result"]["summary"]["blocked_sensitive_candidate_count"] == 1


def test_cli_scheduler_outputs_24h_run_plan():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "scheduler",
            "data/samples/scheduler.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "scheduler"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["due_job_count"] == 3
    assert output["result"]["summary"]["blocked_job_count"] == 2
    assert output["result"]["summary"]["approval_gated_job_count"] == 1
    assert output["result"]["run_queue"][0]["workflow"] == "trend_scan"


def test_cli_connectors_outputs_connector_audit_report():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "connectors",
            "data/samples/connectors.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "connectors"
    assert output["external_actions"] == []
    assert output["result"]["summary"]["connector_count"] == 5
    assert output["result"]["summary"]["missing_permission_count"] == 2
    assert output["result"]["summary"]["high_risk_connector_count"] == 1
    assert len(output["result"]["launch_sequence"]) == 2


def test_cli_agent_run_outputs_approval_gated_plan():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "agent-run",
            "data/samples/agent_run.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "agent_run"
    assert output["external_actions"] == []
    assert output["result"]["run_id"] == "venus-run-sample-001"
    assert output["result"]["workflow_summaries"]["hotspot"]["top_topic"] == "早C晚A翻车"
    assert output["result"]["approval_records"]
    assert all(
        action["execution_state"] != "executed"
        for action in output["result"]["action_plan"]
    )


def test_cli_dashboard_writes_html_file(tmp_path):
    output_file = tmp_path / "venus-dashboard.html"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "dashboard",
            "data/samples/airtable_export.json",
            str(output_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "dashboard"
    assert output["external_actions"] == []
    assert output["result"]["output_path"] == str(output_file)
    assert output["result"]["summary"]["table_count"] == 6
    assert output_file.exists()
    assert "Venus Operations Dashboard" in output_file.read_text(encoding="utf-8")


def test_cli_feishu_outputs_dry_run_card():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "venus.cli",
            "feishu",
            "data/samples/feishu_message.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "feishu"
    assert output["dry_run"] is True
    assert output["command"]["name"] == "hotspot"
    assert output["external_actions"] == []
    assert output["card"]["type"] == "report"
