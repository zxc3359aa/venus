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
