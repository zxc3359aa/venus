from venus.orchestrator import VenusOrchestrator


def test_first_slice_acceptance_workflows():
    orchestrator = VenusOrchestrator()

    hotspot = orchestrator.run(
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
    product = orchestrator.run(
        "product",
        {
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
            ]
        },
    )
    comments = orchestrator.run(
        "comments",
        {
            "comments": [
                {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
                {"id": "c2", "text": "求平价替代！"},
            ]
        },
    )
    monitoring = orchestrator.run(
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
                            "high_risk_comments": ["敏感肌会不会烂脸"],
                        }
                    ],
                    "live_sessions": [{"duration_minutes": 60}],
                }
            ]
        },
    )

    assert hotspot["external_actions"] == []
    assert product["result"]["forbidden_claims"] == ["100%修复屏障"]
    assert comments["result"]["summary"]["approval_gated"] == 1
    assert monitoring["external_actions"] == []
    assert monitoring["result"]["opportunities"][0]["action_type"] == "film"
