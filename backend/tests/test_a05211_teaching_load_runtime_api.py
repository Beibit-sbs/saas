from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/teaching-load"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="756",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["academic_operations.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_academic_operations_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_academic_operations_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_teaching_load_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.teaching_load_runtime_router.get_teaching_load_runtime")
def test_teaching_load_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "TEACHING_LOAD_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "teaching_load_statistics": {
            "tracked_faculty_total": 12,
            "department_groups_total": 4,
            "high_utilization_total": 3,
            "low_utilization_total": 2,
            "high_risk_assignments_total": 2,
            "teaching_load_signals_total": 3,
            "canonical_bridge_total": 7,
        },
        "faculty_workload_distribution": {
            "evenly_distributed_total": 7,
            "overloaded_total": 3,
            "underutilized_total": 2,
            "fairness_alert_total": 1,
            "read_only": True,
        },
        "workload_utilization": {
            "average_utilization_pct": 0.84,
            "median_utilization_pct": 0.81,
            "min_utilization_pct": 0.32,
            "max_utilization_pct": 1.28,
            "utilization_std_dev": 0.19,
            "read_only": True,
        },
        "overload_risk_summary": {
            "risk_score": 55,
            "open_risks": 3,
            "indicators": ["utilization_above_capacity", "overload_alerts_present"],
            "read_only": True,
        },
        "underutilization_summary": {
            "owner_module": "academic_operations",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["faculty", "teaching_load_contracts"],
        },
        "faculty_assignment_health": {
            "owner_module": "academic_operations",
            "records": 10,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["faculty", "scheduling"],
        },
        "coverage_risk_summary": {
            "risk_score": 30,
            "open_risks": 2,
            "indicators": ["department_distribution_imbalance", "high_risk_assignment_gap"],
            "read_only": True,
        },
        "high_risk_assignments": {
            "owner_module": "academic_operations",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["faculty", "scheduling", "teaching_load_contracts"],
        },
        "teaching_load_signals": {
            "generated_signals": 3,
            "signal_types": [
                "teaching_load_overload",
                "teaching_load_underutilization",
                "teaching_load_distribution_variance",
            ],
            "read_only": True,
        },
        "teaching_load_readiness": {
            "ready_for_runtime": True,
            "checklist": ["read_only_runtime", "aggregator_only_runtime"],
            "readiness_score": 74,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "TEACHING_LOAD_RUNTIME"
    assert body["teaching_load_statistics"]["tracked_faculty_total"] == 12
    assert body["faculty_workload_distribution"]["overloaded_total"] == 3
    assert body["workload_utilization"]["max_utilization_pct"] == 1.28


@patch("app.modules.academic_operations_runtime.teaching_load_runtime_router.get_teaching_load_runtime")
def test_teaching_load_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "TEACHING_LOAD_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "teaching_load_statistics": {
                "tracked_faculty_total": tenant_id,
                "department_groups_total": 1,
                "high_utilization_total": 0,
                "low_utilization_total": 0,
                "high_risk_assignments_total": 0,
                "teaching_load_signals_total": 0,
                "canonical_bridge_total": tenant_id + 1,
            },
            "faculty_workload_distribution": {
                "evenly_distributed_total": tenant_id,
                "overloaded_total": 0,
                "underutilized_total": 0,
                "fairness_alert_total": 0,
                "read_only": True,
            },
            "workload_utilization": {
                "average_utilization_pct": 0.5,
                "median_utilization_pct": 0.5,
                "min_utilization_pct": 0.5,
                "max_utilization_pct": 0.5,
                "utilization_std_dev": 0.0,
                "read_only": True,
            },
            "overload_risk_summary": {
                "risk_score": 0,
                "open_risks": 0,
                "indicators": [],
                "read_only": True,
            },
            "underutilization_summary": {
                "owner_module": "academic_operations",
                "records": 0,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["faculty"],
            },
            "faculty_assignment_health": {
                "owner_module": "academic_operations",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["faculty", "scheduling"],
            },
            "coverage_risk_summary": {
                "risk_score": 0,
                "open_risks": 0,
                "indicators": [],
                "read_only": True,
            },
            "high_risk_assignments": {
                "owner_module": "academic_operations",
                "records": 0,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["faculty", "scheduling"],
            },
            "teaching_load_signals": {
                "generated_signals": 0,
                "signal_types": [],
                "read_only": True,
            },
            "teaching_load_readiness": {
                "ready_for_runtime": True,
                "checklist": ["read_only_runtime"],
                "readiness_score": 90,
            },
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 9, "name": "Tenant-9"}
    tenant9 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 13, "name": "Tenant-13"}
    tenant13 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant9.status_code == 200
    assert tenant13.status_code == 200
    assert tenant9.json()["tenant_id"] == 9
    assert tenant13.json()["tenant_id"] == 13


@patch("app.modules.academic_operations_runtime.teaching_load_runtime_router.get_teaching_load_runtime")
def test_teaching_load_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="757",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_teaching_load_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405