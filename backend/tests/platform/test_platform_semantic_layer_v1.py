from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.billing import service as platform_billing_service
from app.platform.repository.billing_repository import BillingRepository
from app.platform.uow import UnitOfWork
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def _seed_semantic_platform_subscription(*, tenant_id: int = 1, analytics_queries_limit: int, price_cents: int = 1000) -> str:
    suffix = uuid4().hex[:8]
    plan_code = f"semantic-{suffix}"
    with UnitOfWork() as uow:
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Semantic {suffix}",
            price_cents=price_cents,
            features={"analytics": True},
            limits={"analytics_queries": analytics_queries_limit},
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(int(tenant_id), plan_code, conn=uow.conn)
    return plan_code


def test_semantic_catalog_endpoints_return_entities_metrics_dimensions() -> None:
    entities = client.get("/api/v2/semantic/entities", headers=ADMIN_HEADERS)
    assert entities.status_code == 200, entities.text
    entity_codes = {item["code"] for item in entities.json()}
    assert "student" in entity_codes
    assert "scorecard" in entity_codes

    metrics = client.get("/api/v2/semantic/metrics", headers=ADMIN_HEADERS)
    assert metrics.status_code == 200, metrics.text
    metric_codes = {item["code"] for item in metrics.json()}
    assert "student.success_rate" in metric_codes
    assert "ops.latency_p95" in metric_codes

    dimensions = client.get("/api/v2/semantic/dimensions", headers=ADMIN_HEADERS)
    assert dimensions.status_code == 200, dimensions.text
    dimension_codes = {item["code"] for item in dimensions.json()}
    assert "term" in dimension_codes
    assert "program" in dimension_codes


def test_semantic_query_returns_data_metadata_and_lineage() -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=10)

    response = client.post(
        "/api/v2/semantic/query",
        headers=ADMIN_HEADERS,
        json={
            "entity": "student",
            "metrics": ["student.success_rate", "student.dropout_risk"],
            "dimensions": ["program", "term"],
            "filters": {"program": "CS", "term": "2025-FALL"},
            "time_range": "last_12_months",
            "explain": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1
    assert body["metadata"]["entity"] == "student"
    assert "lineage_ref" in body
    assert "data_as_of" in body
    assert isinstance(body.get("explanation"), str)


def test_semantic_query_records_platform_usage_and_does_not_use_legacy_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=10)

    def _legacy_must_not_run(*args, **kwargs):
        raise AssertionError("legacy quota helper must not be used by semantic path")

    monkeypatch.setattr("app.modules.billing.service.assert_quota_with_increment", _legacy_must_not_run)

    response = client.post(
        "/api/v2/semantic/query",
        headers=ADMIN_HEADERS,
        json={
            "entity": "student",
            "metrics": ["student.success_rate"],
            "dimensions": ["term"],
            "filters": {"term": "2025-FALL"},
            "time_range": "last_12_months",
        },
    )

    assert response.status_code == 200, response.text

    with UnitOfWork() as uow:
        usage_rows = uow.usage_repository.list_for_tenant_period(1, period_key="current", conn=uow.conn)

    analytics_queries = [row for row in usage_rows if str(row.get("metric")) == "analytics_queries"]
    assert len(analytics_queries) == 1
    assert int(analytics_queries[0]["value"]) == 1


def test_semantic_query_denies_when_platform_quota_exceeded() -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=1)
    platform_billing_service.increment_usage(tenant_id=1, metric="analytics_queries", value=1)

    response = client.post(
        "/api/v2/semantic/query",
        headers=ADMIN_HEADERS,
        json={
            "entity": "student",
            "metrics": ["student.success_rate"],
            "dimensions": ["term"],
            "filters": {"term": "2025-FALL"},
            "time_range": "last_12_months",
        },
    )

    assert response.status_code == 403, response.text
    assert "quota exceeded" in str(response.json().get("detail", "")).lower()


def test_semantic_query_denies_when_platform_subscription_inactive(monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=10)

    original_get_subscription = BillingRepository.get_subscription

    def _suspended_subscription(self, tenant_id: int, *, conn=None):
        row = original_get_subscription(self, tenant_id, conn=conn)
        if row is None:
            return None
        return {**row, "status": "suspended"}

    monkeypatch.setattr(BillingRepository, "get_subscription", _suspended_subscription)

    response = client.post(
        "/api/v2/semantic/query",
        headers=ADMIN_HEADERS,
        json={
            "entity": "student",
            "metrics": ["student.success_rate"],
            "dimensions": ["term"],
            "filters": {"term": "2025-FALL"},
            "time_range": "last_12_months",
        },
    )

    assert response.status_code == 403, response.text
    assert "billing_required" in str(response.json().get("detail", "")).lower()


def test_semantic_query_denies_cross_tenant_override() -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=10)

    response = client.post(
        "/api/v2/semantic/query",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": "999"},
        json={
            "entity": "student",
            "metrics": ["student.success_rate"],
            "dimensions": ["term"],
            "filters": {"term": "2025-FALL"},
            "time_range": "last_12_months",
        },
    )
    assert response.status_code == 403
    assert "cross-tenant" in str(response.json().get("detail", "")).lower()


def test_semantic_query_teacher_scope_forces_instructor_self() -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=10)

    teacher_headers = _auth_headers("teacher.alpha@example.com", ["teacher"], tenant_id=1)

    denied = client.post(
        "/api/v2/semantic/query",
        headers=teacher_headers,
        json={
            "entity": "faculty",
            "metrics": ["faculty.workload_index"],
            "dimensions": ["instructor"],
            "filters": {"instructor": "another.teacher@example.com"},
            "time_range": "last_30_days",
        },
    )
    assert denied.status_code == 403
    assert "scope filter mismatch" in str(denied.json().get("detail", "")).lower()

    allowed = client.post(
        "/api/v2/semantic/query",
        headers=teacher_headers,
        json={
            "entity": "faculty",
            "metrics": ["faculty.workload_index"],
            "dimensions": ["instructor"],
            "filters": {},
            "time_range": "last_30_days",
        },
    )
    assert allowed.status_code == 200, allowed.text
    payload = allowed.json()
    assert payload["data"][0]["instructor"] == "teacher.alpha@example.com"


def test_semantic_query_dean_requires_program_or_department_filter() -> None:
    _seed_semantic_platform_subscription(tenant_id=1, analytics_queries_limit=10)

    dean_headers = _auth_headers("dean.alpha@example.com", ["dean"], tenant_id=1)

    denied = client.post(
        "/api/v2/semantic/query",
        headers=dean_headers,
        json={
            "entity": "student",
            "metrics": ["student.success_rate"],
            "dimensions": ["term"],
            "filters": {"term": "2025-FALL"},
            "time_range": "last_12_months",
        },
    )
    assert denied.status_code == 403
    assert "requires program or department" in str(denied.json().get("detail", "")).lower()

    allowed = client.post(
        "/api/v2/semantic/query",
        headers=dean_headers,
        json={
            "entity": "student",
            "metrics": ["student.success_rate"],
            "dimensions": ["program", "term"],
            "filters": {"program": "CS", "term": "2025-FALL"},
            "time_range": "last_12_months",
        },
    )
    assert allowed.status_code == 200, allowed.text
