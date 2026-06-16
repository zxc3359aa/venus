import pytest

from venus.airtable_export import AirtableExportConfig, build_airtable_sync_package


def _sample_payload():
    return {
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
        "products": [
            {
                "brand": "示例品牌",
                "name": "屏障修护精华",
                "filing_id": "国妆网备字20260001",
                "ingredients": ["烟酰胺", "泛醇", "神经酰胺NP"],
                "claims": ["修护", "100%修复屏障"],
                "supplier_docs": ["泛醇供应商COA"],
                "controversies": ["用户反馈刺痛"],
                "evidence": [{"id": "nmpa-001", "type": "regulator", "title": "备案查询", "confidence": "high"}],
            }
        ],
        "comments": [
            {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
            {"id": "c2", "text": "求平价替代！"},
        ],
        "competitors": {
            "competitors": [
                {
                    "handle": "成分党A",
                    "followers": 380000,
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
        "approvals": [],
    }


def test_build_airtable_sync_package_creates_dry_run_tables_and_records():
    package = build_airtable_sync_package(_sample_payload())

    assert package["dry_run"] is True
    assert package["external_actions"] == []
    assert package["base"]["name"] == "Venus Ops"
    assert package["base"]["namespace"] == "venus_airtable"
    assert package["summary"]["table_count"] == 6
    assert package["summary"]["record_count"] >= 6

    tables = {table["name"]: table for table in package["tables"]}
    assert set(tables) == {
        "Hotspots",
        "Products",
        "Comments",
        "Competitors",
        "Monitoring Opportunities",
        "Approvals",
    }
    assert tables["Hotspots"]["records"][0]["fields"]["Topic"] == "早C晚A翻车"
    assert tables["Products"]["records"][0]["fields"]["Risk Level"] == "high"
    assert tables["Comments"]["records"][0]["fields"]["Approval Level"] == 3
    assert tables["Competitors"]["records"][0]["fields"]["Handle"] == "成分党A"
    assert tables["Monitoring Opportunities"]["records"][0]["fields"]["Action Type"] == "film"
    assert "Airtable write is disabled" in package["sync_boundary"]["notes"][0]


def test_airtable_export_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        AirtableExportConfig(base_name="Xiaolongxia Ops", namespace="xiaolongxia_airtable")
