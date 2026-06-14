from venus.product_research import build_product_research_card


def test_build_product_research_card_separates_evidence_and_safe_claims():
    product = {
        "brand": "示例品牌",
        "name": "屏障修护精华",
        "filing_id": "国妆网备字20260001",
        "ingredients": ["烟酰胺", "泛醇", "神经酰胺NP"],
        "claims": ["修护", "维稳", "100%修复屏障"],
        "supplier_docs": ["泛醇供应商COA"],
        "controversies": ["用户反馈刺痛"],
        "evidence": [
            {"id": "nmpa-001", "type": "regulator", "title": "备案查询", "confidence": "high"},
            {"id": "ugc-001", "type": "social", "title": "用户评论截图", "confidence": "medium"},
        ],
    }

    card = build_product_research_card(product)

    assert card["product"] == "示例品牌 屏障修护精华"
    assert card["sections"]["filing"]["status"] == "has_filing_id"
    assert "100%修复屏障" in card["forbidden_claims"]
    assert "可以说支持屏障护理，但不要承诺修复结果" in card["safe_talking_points"]
    assert card["risk_level"] == "high"
