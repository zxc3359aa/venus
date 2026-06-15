from html.parser import HTMLParser

from venus.dashboard import build_dashboard_html


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.text.append(stripped)


def _payload():
    return {
        "hotspots": [
            {
                "topic": "早C晚A翻车 <script>",
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
                            "high_risk_comments": ["敏感肌会不会烂脸"],
                        }
                    ],
                    "live_sessions": [{"duration_minutes": 60}],
                }
            ]
        },
        "approvals": [],
    }


def test_build_dashboard_html_returns_static_dashboard_with_reconciled_summary():
    result = build_dashboard_html(_payload())

    assert result["external_actions"] == []
    assert result["summary"]["table_count"] == 6
    assert result["summary"]["record_count"] >= 6
    assert result["summary"]["high_risk_comments"] == 1
    assert result["summary"]["high_risk_products"] == 1
    assert result["summary"]["opportunity_count"] >= 1

    html = result["html"]
    assert html.startswith("<!doctype html>")
    assert "<title>Venus Operations Dashboard</title>" in html
    assert "Airtable write is disabled" in html
    assert "external-actions-empty" in html
    assert "早C晚A翻车 &lt;script&gt;" in html
    assert "早C晚A翻车 <script>" not in html
    for section in [
        "Hotspots",
        "Products",
        "Comments",
        "Competitors",
        "Monitoring Opportunities",
        "Approvals",
    ]:
        assert f">{section}<" in html

    parser = TextCollector()
    parser.feed(html)
    assert "Venus Operations Dashboard" in parser.text
