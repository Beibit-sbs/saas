"""
Backend tests for AI Copilot Recommendation Layer v1.

Covers:
- academic_risk_followup rule fires correctly
- automation_rule_health_review rule fires correctly
- failed_jobs_attention rule fires correctly (threshold 5)
- failed_notifications_attention rule fires correctly (threshold 10)
- enrollment_drop_attention rule fires when drop >= 30%
- low_activity_attention rule fires when activity_score <= 0.20
- No recommendations generated when context is neutral/clean
- Recommendations logging in-memory
- Recommendations included in copilot answer shape
- Tenant isolation: recommendations for tenant A not visible for tenant B
- API: POST /api/v1/admin/platform/ai/copilot/ask returns recommendations list
"""
from __future__ import annotations

import pytest
from uuid import uuid4

from app.platform.ai.recommendations.rule_catalog import evaluate_rules
from app.platform.ai.recommendations.schemas import CopilotRecommendationSchema
from app.platform.ai.recommendations.repository import AiRecommendationRepository
from app.platform.ai.recommendations.service import AiRecommendationService
from app.platform.ai.service import AiCopilotService
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork
from tests.conftest import ADMIN_HEADERS, client


def _tenant(prefix: str) -> int:
    row = tenant_service.create_tenant(f"{prefix}-{uuid4().hex[:8]}", f"{prefix} Tenant")
    return int(row["tenant_id"])


# ---------------------------------------------------------------------------
# Rule catalog unit tests
# ---------------------------------------------------------------------------


class TestRuleCatalogAcademicRisk:
    def test_fires_when_at_risk_count_positive(self) -> None:
        recs = evaluate_rules({"at_risk_count": 3})
        types = [r.recommendation_type for r in recs]
        assert "academic_risk_followup" in types

    def test_priority_high_when_five_or_more(self) -> None:
        recs = evaluate_rules({"at_risk_count": 10})
        rec = next(r for r in recs if r.recommendation_type == "academic_risk_followup")
        assert rec.priority == "high"

    def test_priority_medium_when_below_five(self) -> None:
        recs = evaluate_rules({"at_risk_count": 2})
        rec = next(r for r in recs if r.recommendation_type == "academic_risk_followup")
        assert rec.priority == "medium"

    def test_does_not_fire_when_zero(self) -> None:
        recs = evaluate_rules({"at_risk_count": 0})
        types = [r.recommendation_type for r in recs]
        assert "academic_risk_followup" not in types


class TestRuleCatalogAutomationHealth:
    def test_fires_when_unhealthy_rules_positive(self) -> None:
        recs = evaluate_rules({"unhealthy_rules": 2})
        types = [r.recommendation_type for r in recs]
        assert "automation_rule_health_review" in types

    def test_does_not_fire_when_zero(self) -> None:
        recs = evaluate_rules({"unhealthy_rules": 0})
        types = [r.recommendation_type for r in recs]
        assert "automation_rule_health_review" not in types


class TestRuleCatalogFailedJobs:
    def test_fires_at_threshold_five(self) -> None:
        recs = evaluate_rules({"failed_jobs": 5})
        types = [r.recommendation_type for r in recs]
        assert "failed_jobs_attention" in types

    def test_does_not_fire_below_threshold(self) -> None:
        recs = evaluate_rules({"failed_jobs": 4})
        types = [r.recommendation_type for r in recs]
        assert "failed_jobs_attention" not in types

    def test_high_priority_at_twenty(self) -> None:
        recs = evaluate_rules({"failed_jobs": 20})
        rec = next(r for r in recs if r.recommendation_type == "failed_jobs_attention")
        assert rec.priority == "high"


class TestRuleCatalogFailedNotifications:
    def test_fires_at_threshold_ten(self) -> None:
        recs = evaluate_rules({"failed_notifications": 10})
        types = [r.recommendation_type for r in recs]
        assert "failed_notifications_attention" in types

    def test_does_not_fire_below_threshold(self) -> None:
        recs = evaluate_rules({"failed_notifications": 9})
        types = [r.recommendation_type for r in recs]
        assert "failed_notifications_attention" not in types


class TestRuleCatalogEnrollmentDrop:
    def test_fires_when_drop_exceeds_30_percent(self) -> None:
        recs = evaluate_rules({"total_enrollments": 60, "avg_enrollments": 100})
        types = [r.recommendation_type for r in recs]
        assert "enrollment_drop_attention" in types

    def test_does_not_fire_when_drop_below_30_percent(self) -> None:
        recs = evaluate_rules({"total_enrollments": 80, "avg_enrollments": 100})
        types = [r.recommendation_type for r in recs]
        assert "enrollment_drop_attention" not in types

    def test_does_not_fire_when_no_avg(self) -> None:
        recs = evaluate_rules({"total_enrollments": 0, "avg_enrollments": 0})
        types = [r.recommendation_type for r in recs]
        assert "enrollment_drop_attention" not in types


class TestRuleCatalogLowActivity:
    def test_fires_when_score_at_or_below_020(self) -> None:
        recs = evaluate_rules({"activity_score": 0.10})
        types = [r.recommendation_type for r in recs]
        assert "low_activity_attention" in types

    def test_does_not_fire_above_threshold(self) -> None:
        recs = evaluate_rules({"activity_score": 0.50})
        types = [r.recommendation_type for r in recs]
        assert "low_activity_attention" not in types

    def test_high_priority_when_critical(self) -> None:
        recs = evaluate_rules({"activity_score": 0.03})
        rec = next(r for r in recs if r.recommendation_type == "low_activity_attention")
        assert rec.priority == "high"


class TestNoRecommendations:
    def test_no_recommendations_for_clean_context(self) -> None:
        recs = evaluate_rules(
            {
                "at_risk_count": 0,
                "unhealthy_rules": 0,
                "failed_jobs": 0,
                "failed_notifications": 0,
                "total_enrollments": 100,
                "avg_enrollments": 100,
                "activity_score": 0.8,
            }
        )
        assert recs == []


# ---------------------------------------------------------------------------
# Repository in-memory tests
# ---------------------------------------------------------------------------


class TestAiRecommendationRepository:
    def test_log_and_list(self) -> None:
        repo = AiRecommendationRepository()
        with UnitOfWork() as uow:
            row_id = repo.log_recommendation(
                tenant_id=1,
                actor_id="admin",
                question="Show me risks",
                recommendation_type="academic_risk_followup",
                context_json={"at_risk_count": 3},
                recommendation_json={"priority": "medium"},
                conn=uow.conn,
            )
        assert row_id == 1

        with UnitOfWork() as uow:
            rows = repo.list_for_tenant(tenant_id=1, conn=uow.conn)
        assert len(rows) == 1
        assert rows[0]["recommendation_type"] == "academic_risk_followup"

    def test_tenant_isolation(self) -> None:
        repo = AiRecommendationRepository()
        with UnitOfWork() as uow:
            repo.log_recommendation(
                tenant_id=1,
                actor_id="a",
                question="q",
                recommendation_type="academic_risk_followup",
                context_json={},
                recommendation_json={},
                conn=uow.conn,
            )
            repo.log_recommendation(
                tenant_id=2,
                actor_id="b",
                question="q",
                recommendation_type="failed_jobs_attention",
                context_json={},
                recommendation_json={},
                conn=uow.conn,
            )
        with UnitOfWork() as uow:
            rows_1 = repo.list_for_tenant(tenant_id=1, conn=uow.conn)
            rows_2 = repo.list_for_tenant(tenant_id=2, conn=uow.conn)
        assert len(rows_1) == 1
        assert rows_1[0]["recommendation_type"] == "academic_risk_followup"
        assert len(rows_2) == 1
        assert rows_2[0]["recommendation_type"] == "failed_jobs_attention"


# ---------------------------------------------------------------------------
# Service integration test
# ---------------------------------------------------------------------------


class TestAiRecommendationService:
    def test_generate_logs_and_returns(self) -> None:
        repo = AiRecommendationRepository()
        svc = AiRecommendationService(repository=repo)
        with UnitOfWork() as uow:
            recs = svc.generate_recommendations(
                tenant_id=99,
                actor_id="admin",
                question="Platform health?",
                query_type="platform_health",
                retrieved_context={"failed_jobs": 10, "failed_notifications": 15},
                uow=uow,
            )
        types = [r.recommendation_type for r in recs]
        assert "failed_jobs_attention" in types
        assert "failed_notifications_attention" in types

        with UnitOfWork() as uow:
            logged = repo.list_for_tenant(tenant_id=99, conn=uow.conn)
        assert len(logged) >= 2


# ---------------------------------------------------------------------------
# AiCopilotService integration: recommendations in answer dict
# ---------------------------------------------------------------------------


class TestCopilotServiceRecommendationsIntegration:
    def test_academic_risk_answer_contains_recommendations(self) -> None:
        rec_repo = AiRecommendationRepository()
        rec_svc = AiRecommendationService(repository=rec_repo)
        svc = AiCopilotService(recommendation_service=rec_svc)

        # Seed at-risk students via KPI / context in-memory state
        # The retrieval.retrieve_academic_risk returns whatever the context service
        # exposes, which defaults to an empty list — so at_risk_count will be 0
        # unless we specifically test via rule evaluation.
        # We test that the answer shape includes the recommendations key always.
        answer = svc.answer_question(
            tenant_id=1,
            actor_id="admin",
            question="Are there any students at academic risk?",
        )
        assert "recommendations" in answer
        assert isinstance(answer["recommendations"], list)

    def test_answer_without_recommendations_for_unsupported_query(self) -> None:
        svc = AiCopilotService()
        answer = svc.answer_question(
            tenant_id=1,
            actor_id="admin",
            question="Something completely unknown and unsupported xyz123",
        )
        assert "recommendations" in answer
        assert answer["recommendations"] == []


# ---------------------------------------------------------------------------
# Admin API shape test
# ---------------------------------------------------------------------------


def test_api_ask_returns_recommendations_field(reset_shared_state) -> None:
    tenant_id = _tenant("ai-rec-api")
    resp = client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        json={"tenant_id": tenant_id, "question": "What is the KPI summary?"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "recommendations" in body
    assert isinstance(body["recommendations"], list)


def test_api_ask_recommendations_schema_shape(reset_shared_state) -> None:
    """When a recommendation fires, each item must have the correct keys."""
    tenant_id = _tenant("ai-rec-shape")
    resp = client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        json={"tenant_id": tenant_id, "question": "What is the platform health?"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for rec in body.get("recommendations", []):
        assert "recommendation_type" in rec
        assert "title" in rec
        assert "priority" in rec
        assert "reason" in rec
        assert "suggested_actions" in rec
        for action in rec["suggested_actions"]:
            assert "action_type" in action
            assert "label" in action
