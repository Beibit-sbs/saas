from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/attendance"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="746",
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


def test_attendance_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.attendance_runtime_router.get_attendance_runtime")
def test_attendance_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "ATTENDANCE_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "attendance_statistics": {
            "tracked_students_total": 220,
            "tracked_courses_total": 18,
            "average_attendance_rate": 84,
            "at_risk_students_total": 31,
            "intervention_candidates_total": 14,
            "trend_windows_total": 3,
            "canonical_bridge_total": 5,
        },
        "attendance_distribution": {
            "excellent_band": 80,
            "good_band": 90,
            "warning_band": 35,
            "critical_band": 15,
            "read_only": True,
        },
        "attendance_trends": {
            "improving_count": 24,
            "stable_count": 130,
            "declining_count": 31,
            "trend_score": 67,
            "read_only": True,
        },
        "attendance_risk_summary": {
            "risk_score": 45,
            "open_risks": 2,
            "primary_risks": ["critical_absence_population", "intervention_backlog"],
            "read_only": True,
        },
        "high_risk_population": {
            "owner_module": "attendance",
            "records": 31,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["attendance", "attendance_tracking", "scheduling"],
        },
        "course_attendance_health": {
            "owner_module": "attendance",
            "records": 18,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["attendance", "scheduling", "academic_operations"],
        },
        "attendance_intervention_candidates": {
            "owner_module": "attendance",
            "records": 14,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["attendance_tracking", "academic_operations"],
        },
        "attendance_signals": {
            "generated_signals": 23,
            "signal_types": ["warning_attendance_drop", "critical_attendance_risk"],
            "read_only": True,
        },
        "attendance_readiness": {
            "ready_for_runtime": False,
            "checklist": ["read_only_runtime", "aggregator_only_runtime"],
            "readiness_score": 71,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "ATTENDANCE_RUNTIME"
    assert body["attendance_statistics"]["tracked_students_total"] == 220
    assert body["attendance_distribution"]["critical_band"] == 15
    assert body["attendance_risk_summary"]["open_risks"] == 2


@patch("app.modules.academic_operations_runtime.attendance_runtime_router.get_attendance_runtime")
def test_attendance_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "ATTENDANCE_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "attendance_statistics": {
                "tracked_students_total": tenant_id + 200,
                "tracked_courses_total": tenant_id + 10,
                "average_attendance_rate": 80,
                "at_risk_students_total": tenant_id,
                "intervention_candidates_total": tenant_id,
                "trend_windows_total": 3,
                "canonical_bridge_total": tenant_id,
            },
            "attendance_distribution": {
                "excellent_band": tenant_id,
                "good_band": tenant_id,
                "warning_band": tenant_id,
                "critical_band": tenant_id,
                "read_only": True,
            },
            "attendance_trends": {
                "improving_count": tenant_id,
                "stable_count": tenant_id,
                "declining_count": tenant_id,
                "trend_score": 60,
                "read_only": True,
            },
            "attendance_risk_summary": {
                "risk_score": 40,
                "open_risks": 1,
                "primary_risks": ["critical_absence_population"],
                "read_only": True,
            },
            "high_risk_population": {
                "owner_module": "attendance",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["attendance"],
            },
            "course_attendance_health": {
                "owner_module": "attendance",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["attendance"],
            },
            "attendance_intervention_candidates": {
                "owner_module": "attendance",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["attendance_tracking"],
            },
            "attendance_signals": {
                "generated_signals": tenant_id,
                "signal_types": ["warning_attendance_drop"],
                "read_only": True,
            },
            "attendance_readiness": {
                "ready_for_runtime": False,
                "checklist": ["read_only_runtime"],
                "readiness_score": 70,
            },
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 8, "name": "Tenant-8"}
    tenant8 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant8.status_code == 200
    assert tenant12.status_code == 200
    assert tenant8.json()["tenant_id"] == 8
    assert tenant12.json()["tenant_id"] == 12


@patch("app.modules.academic_operations_runtime.attendance_runtime_router.get_attendance_runtime")
def test_attendance_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="747",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_attendance_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405
