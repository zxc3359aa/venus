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
