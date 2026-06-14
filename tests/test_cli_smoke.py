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
