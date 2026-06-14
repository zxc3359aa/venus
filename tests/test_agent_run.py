import pytest

from venus.agent_run import AgentRunConfig, build_agent_run_plan


def _agent_run_payload():
    return {
        "run_id": "venus-run-2026-06-14-am",
        "trigger": "manual_feishu",
        "requested_at": "2026-06-14T09:00:00+08:00",
        "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        "requested_surfaces": [
            "feishu_mobile_report",
            "airtable_sync_review",
            "douyin_comment_reply_queue",
            "qianchuan_budget_review",
            "xingtu_brief_response",
            "wechat_private_domain_handoff",
        ],
        "trend_scan": {
            "source": "manual_douyin_beauty_scan",
            "retrieved_at": "2026-06-14T15:00:00+08:00",
            "refresh_interval_minutes": 15,
            "live_connector_requested": True,
            "topics": [
                {
                    "id": "topic-001",
                    "label": "早C晚A翻车",
                    "mentions": 320000,
                    "growth": 0.82,
                    "controversy": 0.78,
                    "evidence": ["douyin-hot-001"],
                }
            ],
            "products": [
                {"id": "prod-001", "label": "屏障修护精华", "mentions": 98000, "growth": 0.64, "controversy": 0.7}
            ],
            "creators": [
                {"id": "creator-001", "handle": "成分党A", "mentions": 65000, "growth": 0.55, "controversy": 0.4}
            ],
            "comments": [
                {"id": "comment-001", "text": "敏感肌用了会不会烂脸？", "likes": 1800, "growth": 0.8, "controversy": 0.9}
            ],
            "ingredients": [
                {"id": "ing-001", "label": "视黄醇", "mentions": 120000, "growth": 0.7, "controversy": 0.85}
            ],
            "tags": [
                {"id": "tag-001", "label": "早C晚A", "mentions": 260000, "growth": 0.74, "controversy": 0.6}
            ],
            "controversies": [
                {"id": "risk-001", "label": "A醇叠加刷酸爆皮", "mentions": 88000, "growth": 0.71, "controversy": 0.92}
            ],
        },
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
        "product_intelligence": {
            "source": "manual_product_dossier",
            "retrieved_at": "2026-06-14T16:00:00+08:00",
            "live_connector_requested": True,
            "product": {
                "brand": "示例品牌",
                "name": "屏障修护精华",
                "filing_id": "国妆网备字20260001",
                "manufacturer": "示例化妆品有限公司",
                "claims": ["舒缓", "100%修复屏障"],
                "brand_backing": [
                    {"type": "dermatologist_quote", "source": "品牌手册", "status": "unverified"},
                    {"type": "lab_collaboration", "source": "品牌发布会", "status": "verified"},
                ],
                "ingredients": [
                    {
                        "name": "烟酰胺",
                        "role": "brightening",
                        "risk": "medium",
                        "supplier": "原料商A",
                        "coa": "coa-niacinamide-001",
                        "test_report": "test-niacinamide-001",
                    },
                    {
                        "name": "视黄醇",
                        "role": "renewal",
                        "risk": "high",
                        "supplier": "原料商B",
                        "coa": "",
                        "test_report": "",
                    },
                ],
                "supplier_documents": [
                    {"supplier": "原料商A", "document": "coa-niacinamide-001", "status": "provided"},
                    {"supplier": "原料商B", "document": "", "status": "missing"},
                ],
                "test_reports": [
                    {"report_id": "test-niacinamide-001", "scope": "烟酰胺纯度", "status": "provided"},
                    {"report_id": "", "scope": "视黄醇稳定性", "status": "missing"},
                ],
                "controversies": [
                    {"source": "douyin_comment", "issue": "用户反馈刺痛", "severity": "medium"},
                    {"source": "creator_video", "issue": "达人质疑夸大修复", "severity": "high"},
                ],
                "evidence": [{"id": "nmpa-001", "type": "filing", "title": "备案查询"}],
            },
        },
        "comments": [
            {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
            {"id": "c2", "text": "求平价替代！"},
        ],
        "video_production": {
            "source": "manual_content_brief",
            "retrieved_at": "2026-06-14T14:00:00+08:00",
            "topic": "早C晚A翻车自查",
            "format": "douyin_short_video",
            "duration_seconds": 45,
            "objective": "提升完播、评论和关注",
            "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
            "key_points": ["先判断屏障状态", "再看成分刺激叠加", "最后给评论区肤质自查问题"],
            "risk_notes": ["避免100%修复屏障这类绝对功效承诺"],
            "broll_assets": ["评论截图", "成分表特写", "备案截图"],
        },
        "douyin_engagement": {
            "source": "manual_douyin_export",
            "retrieved_at": "2026-06-14T10:00:00+08:00",
            "videos": [
                {
                    "video_id": "video-001",
                    "title": "早C晚A翻车自查",
                    "comments": [
                        {"comment_id": "dc1", "text": "敏感肌用了会不会烂脸？", "likes": 18}
                    ],
                }
            ],
            "live_sessions": [
                {
                    "session_id": "live-001",
                    "messages": [
                        {"message_id": "dl1", "text": "刷酸爆皮了还能叠加这个吗？", "likes": 3}
                    ],
                }
            ],
        },
        "ecommerce": {
            "source": "manual_douyin_shop_export",
            "retrieved_at": "2026-06-14T17:00:00+08:00",
            "live_connector_requested": True,
            "shop": {"shop_id": "shop-001", "name": "维纳斯护肤小店", "channel": "douyin_shop"},
            "products": [
                {
                    "product_id": "sku-001",
                    "title": "屏障修护精华",
                    "price": 199,
                    "sale_price": 169,
                    "stock": 36,
                    "target_stock": 120,
                    "margin_rate": 0.42,
                    "commission_rate": 0.18,
                    "conversion_rate": 0.032,
                    "return_rate": 0.06,
                    "claim_risk": "high",
                    "evidence": ["shop-product-001"],
                },
                {
                    "product_id": "sku-002",
                    "title": "温和洁面",
                    "price": 89,
                    "sale_price": 79,
                    "stock": 320,
                    "target_stock": 80,
                    "margin_rate": 0.35,
                    "commission_rate": 0.12,
                    "conversion_rate": 0.018,
                    "return_rate": 0.18,
                    "claim_risk": "medium",
                    "evidence": ["shop-product-002"],
                },
            ],
            "live_rooms": [
                {
                    "session_id": "live-001",
                    "title": "屏障护理专场",
                    "planned_products": ["sku-001", "sku-002"],
                    "viewers": 18000,
                    "gmv": 128000,
                    "product_card_click_rate": 0.21,
                    "conversion_rate": 0.026,
                }
            ],
            "promotions": [
                {"promotion_id": "promo-001", "product_id": "sku-001", "type": "coupon", "discount": 30, "budget": 3000}
            ],
            "after_sales": [
                {"product_id": "sku-001", "issue": "敏感肌刺痛咨询", "severity": "medium"},
                {"product_id": "sku-002", "issue": "退货率偏高", "severity": "high"},
            ],
        },
        "wechat_private_domain": {
            "source": "mini_program_export",
            "retrieved_at": "2026-06-14T11:00:00+08:00",
            "mini_program_sessions": [
                {
                    "session_id": "mp-001",
                    "nickname": "敏敏",
                    "questions": [
                        {"question_id": "q1", "text": "屏障受损泛红，早C晚A还能继续吗？"},
                        {"question_id": "q2", "text": "我想加企业微信进群，让你帮我看产品搭配"},
                    ],
                }
            ],
        },
        "commercial_strategy": {
            "source": "manual_commercial_brief",
            "retrieved_at": "2026-06-14T12:00:00+08:00",
            "qianchuan": {
                "campaign_id": "qc-001",
                "objective": "直播间成交",
                "daily_budget": 3000,
                "spent_today": 1800,
                "roi": 1.4,
                "target_roi": 2.0,
                "audiences": ["敏感肌", "屏障修护"],
                "creatives": [
                    {
                        "creative_id": "ad-001",
                        "title": "早C晚A翻车自查",
                        "completion_rate": 0.72,
                        "ctr": 0.035,
                        "conversion_rate": 0.018,
                    }
                ],
            },
            "xingtu": {
                "brief_id": "xt-001",
                "brand": "示例品牌",
                "product": "屏障修护精华",
                "budget": 50000,
                "requirements": ["突出100%修复屏障"],
                "forbidden_claims": ["100%修复屏障"],
                "deliverables": ["60秒短视频"],
            },
        },
        "self_improvement": {
            "source": "manual_learning_export",
            "retrieved_at": "2026-06-14T13:00:00+08:00",
            "feedback_events": [
                {
                    "event_id": "fb-001",
                    "workflow": "comments",
                    "decision": "edited",
                    "original": "这个产品一定能修复屏障",
                    "final": "这个产品可以作为屏障护理参考，但要看肤质和耐受。",
                    "reason": "去掉绝对功效承诺",
                    "metric": {"comments": 42, "follows": 12},
                },
                {
                    "event_id": "fb-002",
                    "workflow": "content",
                    "decision": "approved",
                    "original": "早C晚A翻车自查",
                    "final": "姐妹们，先看屏障状态，再谈早C晚A。",
                    "reason": "开头更像我的口语",
                    "metric": {"completion_rate": 0.74},
                },
            ],
            "defect_reports": [
                {
                    "defect_id": "bug-001",
                    "workflow": "douyin",
                    "severity": "high",
                    "description": "直播弹幕回复没有强调先停刺激组合",
                    "expected_guardrail": "高风险直播弹幕必须提醒暂停叠加刺激组合",
                }
            ],
            "backup_checks": [
                {
                    "target": "local-json-store",
                    "schedule": "daily",
                    "last_backup_at": "2026-06-14T08:00:00+08:00",
                    "last_verified_at": "",
                    "status": "missing_verification",
                }
            ],
        },
        "memory": {
            "source": "manual_memory_review",
            "retrieved_at": "2026-06-14T18:00:00+08:00",
            "current_memory": {
                "version": "v3",
                "principles": ["先看屏障状态"],
                "style_phrases": ["姐妹们"],
                "product_beliefs": ["成分要看浓度、配方和肤质"],
                "content_rules": ["先抛出用户真实问题，再给专业判断"],
                "banned_claims": ["100%修复屏障"],
                "privacy_boundaries": ["不记录手机号、地址、订单号等直接个人信息"],
            },
            "learning_candidates": [
                {
                    "candidate_id": "mem-001",
                    "category": "principles",
                    "proposed_rule": "先判断屏障状态，再谈功效、搭配和频率。",
                    "evidence": ["fb-001"],
                },
                {
                    "candidate_id": "mem-002",
                    "category": "style_phrases",
                    "proposed_rule": "姐妹们，先别急着跟风。",
                    "evidence": ["script-001"],
                },
                {
                    "candidate_id": "mem-003",
                    "category": "privacy_boundaries",
                    "proposed_rule": "用户联系方式 contact-token-001 不进入任何记忆。",
                    "evidence": ["privacy-001"],
                    "contains_personal_data": True,
                },
            ],
            "approval_decisions": [
                {"candidate_id": "mem-001", "decision": "approved", "reviewer": "owner"},
                {"candidate_id": "mem-002", "decision": "pending", "reviewer": "owner"},
                {"candidate_id": "mem-003", "decision": "approved", "reviewer": "owner"},
            ],
            "backup": {
                "target": "local-memory-ledger",
                "last_snapshot_version": "v3",
                "last_backup_at": "2026-06-14T07:00:00+08:00",
                "last_verified_at": "",
                "status": "missing_verification",
            },
        },
        "competitors": {
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
        "api_token": "super-secret-token",
    }


def test_build_agent_run_plan_routes_workflows_and_gates_external_surfaces():
    plan = build_agent_run_plan(_agent_run_payload())

    assert plan["workflow"] == "agent_run"
    assert plan["run_id"] == "venus-run-2026-06-14-am"
    assert plan["namespace"] == "venus_agent_run"
    assert plan["dry_run"] is True
    assert plan["approval_mode"] == "manual"
    assert plan["external_actions"] == []
    assert plan["executed_workflows"] == [
        "trend_scan",
        "hotspot",
        "product",
        "product_intel",
        "comments",
        "production",
        "douyin",
        "ecommerce",
        "wechat",
        "commercial",
        "improvement",
        "memory",
        "monitoring",
        "airtable",
    ]
    assert plan["workflow_summaries"]["hotspot"]["top_topic"] == "早C晚A翻车"
    assert plan["workflow_summaries"]["trend_scan"]["signal_count"] == 7
    assert plan["workflow_summaries"]["trend_scan"]["top_signal"] == "早C晚A翻车"
    assert plan["workflow_summaries"]["trend_scan"]["refresh_interval_minutes"] == 15
    assert plan["workflow_summaries"]["product"]["risk_level"] == "high"
    assert plan["workflow_summaries"]["product_intel"]["risk_level"] == "high"
    assert plan["workflow_summaries"]["product_intel"]["retrieval_task_count"] == 5
    assert plan["workflow_summaries"]["product_intel"]["missing_supplier_document_count"] == 1
    assert plan["workflow_summaries"]["comments"]["approval_gated"] == 1
    assert plan["workflow_summaries"]["production"]["scene_count"] == 5
    assert plan["workflow_summaries"]["production"]["subtitle_card_count"] == 5
    assert plan["workflow_summaries"]["production"]["approval_gated_action_count"] == 2
    assert plan["workflow_summaries"]["douyin"]["approval_gated_reply_count"] == 2
    assert plan["workflow_summaries"]["ecommerce"]["product_count"] == 2
    assert plan["workflow_summaries"]["ecommerce"]["low_stock_count"] == 1
    assert plan["workflow_summaries"]["ecommerce"]["approval_gated_action_count"] == 3
    assert plan["workflow_summaries"]["wechat"]["enterprise_wechat_handoff_count"] == 1
    assert plan["workflow_summaries"]["commercial"]["approval_gated_action_count"] == 3
    assert plan["workflow_summaries"]["improvement"]["learning_candidate_count"] == 2
    assert plan["workflow_summaries"]["improvement"]["backup_issue_count"] == 1
    assert plan["workflow_summaries"]["improvement"]["approval_gated_action_count"] == 4
    assert plan["workflow_summaries"]["memory"]["proposed_version"] == "v4"
    assert plan["workflow_summaries"]["memory"]["proposed_change_count"] == 1
    assert plan["workflow_summaries"]["memory"]["blocked_sensitive_candidate_count"] == 1
    assert plan["workflow_summaries"]["monitoring"]["top_account"] == "成分党A"
    assert plan["workflow_summaries"]["airtable"]["table_count"] == 6

    actions = {action["action_type"]: action for action in plan["action_plan"]}
    assert actions["draft_short_video"]["approval_level"] == 1
    assert actions["draft_short_video"]["requires_manual_approval"] is False
    assert actions["douyin_comment_reply_queue"]["approval_level"] == 3
    assert actions["qianchuan_budget_review"]["approval_level"] == 4
    assert actions["xingtu_brief_response"]["approval_level"] == 4
    assert actions["wechat_private_domain_handoff"]["approval_level"] == 4
    assert actions["feishu_mobile_report"]["approval_level"] == 2
    assert actions["airtable_sync_review"]["approval_level"] == 2
    assert all(action["execution_state"] != "executed" for action in plan["action_plan"])

    assert len(plan["approval_records"]) == 6
    assert {record["status"] for record in plan["approval_records"]} == {"pending"}
    assert "super-secret-token" not in str(plan)
    assert "Xiaolongxia" not in str(plan)
    assert "小龙虾" not in str(plan)


def test_agent_run_config_rejects_xiaolongxia_namespace():
    with pytest.raises(ValueError, match="Xiaolongxia"):
        AgentRunConfig(namespace="xiaolongxia_agent_run")
