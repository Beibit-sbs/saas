"""Phase LXXV — Quotas Router tests (21 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.quotas.router import router

app = FastAPI()
app.include_router(router)
# A-009 added router-level permission_dependency — override in unit tests.
app.dependency_overrides = {dep.dependency: lambda: None for dep in router.dependencies}
client = TestClient(app)

MODULE = "app.modules.quotas.router"


# ─── helpers ──────────────────────────────────────────────────────────────────


def _quota_row(id_: int = 1, plan_id: int = 1, key: str = "users", limit_value: int = 10) -> dict:
    return {"id": id_, "plan_id": plan_id, "key": key, "limit_value": limit_value}


def _check_result(
    tenant_id: int = 1,
    quota_key: str = "users",
    limit_value: int = 100,
    current_value: int = 5,
    within_limit: bool = True,
    soft_warning: bool = False,
    message: str = "within quota",
) -> dict:
    return {
        "tenant_id": tenant_id,
        "quota_key": quota_key,
        "limit_value": limit_value,
        "current_value": current_value,
        "within_limit": within_limit,
        "soft_warning": soft_warning,
        "message": message,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/quotas — list_all_quotas
# ═══════════════════════════════════════════════════════════════════════════════


def test_list_quotas_returns_all():
    rows = [_quota_row(1, 1, "users", 10), _quota_row(2, 1, "api_requests", 5000)]
    with patch(f"{MODULE}.list_quotas", return_value=rows) as mock:
        resp = client.get("/api/quotas")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["quotas"]) == 2
    assert body["quotas"][0]["key"] == "users"
    mock.assert_called_once_with(plan_id=None)


def test_list_quotas_filtered_by_plan():
    rows = [_quota_row(1, 2, "users", 25)]
    with patch(f"{MODULE}.list_quotas", return_value=rows) as mock:
        resp = client.get("/api/quotas?plan_id=2")
    assert resp.status_code == 200
    assert len(resp.json()["quotas"]) == 1
    mock.assert_called_once_with(plan_id=2)


def test_list_quotas_empty_returns_empty_list():
    with patch(f"{MODULE}.list_quotas", return_value=[]):
        resp = client.get("/api/quotas")
    assert resp.status_code == 200
    assert resp.json()["quotas"] == []


def test_list_quotas_invalid_plan_id_rejected():
    resp = client.get("/api/quotas?plan_id=0")
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/quotas/plans/{plan_id}
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_plan_quota_map_success():
    quotas = {"users": 100, "api_requests": 50000}
    with patch(f"{MODULE}.get_plan_quotas", return_value=quotas) as mock:
        resp = client.get("/api/quotas/plans/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"] == 1
    assert body["quotas"]["users"] == 100
    mock.assert_called_once_with(plan_id=1)


def test_get_plan_quota_map_empty_plan():
    with patch(f"{MODULE}.get_plan_quotas", return_value={}):
        resp = client.get("/api/quotas/plans/99")
    assert resp.status_code == 200
    assert resp.json()["quotas"] == {}


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /api/quotas/plans/{plan_id}
# ═══════════════════════════════════════════════════════════════════════════════


def test_update_plan_quotas_success():
    rows = [_quota_row(1, 1, "users", 50)]
    with patch(f"{MODULE}.update_plan_quotas", return_value=rows) as mock:
        resp = client.put(
            "/api/quotas/plans/1",
            json={"quotas": {"users": 50}},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["quotas"]) == 1
    assert body["quotas"][0]["limit_value"] == 50
    mock.assert_called_once_with(plan_id=1, quotas={"users": 50})


def test_update_plan_quotas_plan_not_found_returns_400():
    with patch(f"{MODULE}.update_plan_quotas", side_effect=ValueError("plan not found")):
        resp = client.put(
            "/api/quotas/plans/999",
            json={"quotas": {"users": 10}},
        )
    assert resp.status_code == 400
    assert "plan not found" in resp.json()["detail"]


def test_update_plan_quotas_empty_quotas_accepted():
    with patch(f"{MODULE}.update_plan_quotas", return_value=[]) as mock:
        resp = client.put("/api/quotas/plans/1", json={"quotas": {}})
    assert resp.status_code == 200
    assert resp.json()["quotas"] == []


def test_update_plan_quotas_multiple_keys():
    rows = [
        _quota_row(1, 1, "users", 200),
        _quota_row(2, 1, "api_requests", 100000),
    ]
    with patch(f"{MODULE}.update_plan_quotas", return_value=rows):
        resp = client.put(
            "/api/quotas/plans/1",
            json={"quotas": {"users": 200, "api_requests": 100000}},
        )
    assert resp.status_code == 200
    assert len(resp.json()["quotas"]) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/quotas/tenants/{tenant_id}
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_tenant_quotas_success():
    quotas = {"users": 100, "storage_mb": 10240}
    with patch(f"{MODULE}.resolve_tenant_quotas", return_value=quotas) as mock:
        resp = client.get("/api/quotas/tenants/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == 1
    assert body["quotas"]["storage_mb"] == 10240
    mock.assert_called_once_with(tenant_id=1)


def test_get_tenant_quotas_not_found_returns_404():
    with patch(f"{MODULE}.resolve_tenant_quotas", side_effect=ValueError("tenant not found")):
        resp = client.get("/api/quotas/tenants/999")
    assert resp.status_code == 404
    assert "tenant not found" in resp.json()["detail"]


def test_get_tenant_quotas_includes_plan_defaults():
    quotas = {"users": 25, "jobs_per_day": 300}
    with patch(f"{MODULE}.resolve_tenant_quotas", return_value=quotas):
        resp = client.get("/api/quotas/tenants/5")
    assert resp.status_code == 200
    assert resp.json()["quotas"]["jobs_per_day"] == 300


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/quotas/check
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_quota_within_limit():
    result = _check_result(within_limit=True, soft_warning=False, message="within quota")
    with patch(f"{MODULE}.check_quota", return_value=result) as mock:
        resp = client.get("/api/quotas/check?tenant_id=1&quota_key=users")
    assert resp.status_code == 200
    body = resp.json()
    assert body["within_limit"] is True
    assert body["soft_warning"] is False
    mock.assert_called_once_with(tenant_id=1, quota_key="users")


def test_check_quota_exceeded():
    result = _check_result(
        current_value=110,
        limit_value=100,
        within_limit=False,
        soft_warning=True,
        message="quota exceeded (soft enforcement)",
    )
    with patch(f"{MODULE}.check_quota", return_value=result):
        resp = client.get("/api/quotas/check?tenant_id=1&quota_key=users")
    assert resp.status_code == 200
    body = resp.json()
    assert body["within_limit"] is False
    assert body["soft_warning"] is True


def test_check_quota_missing_tenant_id_rejected():
    resp = client.get("/api/quotas/check?quota_key=users")
    assert resp.status_code == 422


def test_check_quota_missing_key_rejected():
    resp = client.get("/api/quotas/check?tenant_id=1")
    assert resp.status_code == 422


def test_check_quota_invalid_key_returns_400():
    with patch(f"{MODULE}.check_quota", side_effect=ValueError("quota_key is required")):
        resp = client.get("/api/quotas/check?tenant_id=1&quota_key=x")
    assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/quotas/consistency
# ═══════════════════════════════════════════════════════════════════════════════


def test_consistency_report_clean():
    from app.modules.quotas.schemas import PlanQuotaConsistencyReportSchema

    report = PlanQuotaConsistencyReportSchema(
        total_plan_count=4,
        configured_plan_quota_count=4,
        issue_count=0,
        issues=[],
    )
    with patch(f"{MODULE}.get_plan_quota_consistency_report", return_value=report) as mock:
        resp = client.get("/api/quotas/consistency")
    assert resp.status_code == 200
    body = resp.json()
    assert body["issue_count"] == 0
    assert body["total_plan_count"] == 4
    mock.assert_called_once()


def test_consistency_report_with_issues():
    from app.modules.quotas.schemas import (
        PlanQuotaConsistencyIssueSchema,
        PlanQuotaConsistencyReportSchema,
    )

    issue = PlanQuotaConsistencyIssueSchema(
        issue_type="plan_missing_quota_key",
        plan_id=1,
        plan_code="free",
        quota_key="storage_mb",
        detail="Plan is missing a baseline quota key.",
    )
    report = PlanQuotaConsistencyReportSchema(
        total_plan_count=4,
        configured_plan_quota_count=3,
        issue_count=1,
        issues=[issue],
    )
    with patch(f"{MODULE}.get_plan_quota_consistency_report", return_value=report):
        resp = client.get("/api/quotas/consistency")
    assert resp.status_code == 200
    body = resp.json()
    assert body["issue_count"] == 1
    assert body["issues"][0]["issue_type"] == "plan_missing_quota_key"
