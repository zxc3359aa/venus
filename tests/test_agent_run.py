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
        "hotspot",
        "product",
        "comments",
        "douyin",
        "wechat",
        "commercial",
        "improvement",
        "monitoring",
        "airtable",
    ]
    assert plan["workflow_summaries"]["hotspot"]["top_topic"] == "早C晚A翻车"
    assert plan["workflow_summaries"]["product"]["risk_level"] == "high"
    assert plan["workflow_summaries"]["comments"]["approval_gated"] == 1
    assert plan["workflow_summaries"]["douyin"]["approval_gated_reply_count"] == 2
    assert plan["workflow_summaries"]["wechat"]["enterprise_wechat_handoff_count"] == 1
    assert plan["workflow_summaries"]["commercial"]["approval_gated_action_count"] == 3
    assert plan["workflow_summaries"]["improvement"]["learning_candidate_count"] == 2
    assert plan["workflow_summaries"]["improvement"]["backup_issue_count"] == 1
    assert plan["workflow_summaries"]["improvement"]["approval_gated_action_count"] == 4
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
