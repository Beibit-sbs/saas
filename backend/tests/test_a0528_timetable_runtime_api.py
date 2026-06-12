from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/timetable"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="736",
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


def test_timetable_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.timetable_runtime_router.get_timetable_runtime")
def test_timetable_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "TIMETABLE_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "timetable_statistics": {
            "course_sections_total": 18,
            "schedules_total": 25,
            "calendar_periods_total": 4,
            "rooms_total": 12,
            "instructors_total": 14,
            "students_total": 220,
            "conflicts_total": 3,
            "capacity_alerts_total": 2,
            "canonical_bridge_total": 6,
        },
        "academic_calendar_summary": {
            "owner_module": "academic_calendar",
            "records": 4,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_calendar", "scheduling"],
        },
        "room_utilization": {
            "records": 12,
            "utilization_rate": 78,
            "underutilized_rooms": 2,
            "overloaded_rooms": 1,
            "read_only": True,
        },
        "instructor_allocation": {
            "records": 14,
            "assigned_instructors": 13,
            "unassigned_sections": 1,
            "read_only": True,
        },
        "student_schedule_summary": {
            "owner_module": "timetable_management",
            "records": 220,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["scheduling", "student_lifecycle"],
        },
        "schedule_conflicts": {
            "records": 3,
            "conflict_rate": 16,
            "critical_conflicts": 1,
            "read_only": True,
        },
        "capacity_indicators": {
            "records": 2,
            "over_capacity_sections": 2,
            "under_capacity_sections": 1,
            "read_only": True,
        },
        "timetable_health": {
            "healthy": False,
            "consistency_score": 82,
            "issues": ["schedule_conflicts_detected"],
        },
        "timetable_readiness": {
            "ready_for_runtime": False,
            "checklist": ["read_only_runtime", "aggregator_only_runtime"],
            "readiness_score": 79,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "TIMETABLE_RUNTIME"
    assert body["timetable_statistics"]["course_sections_total"] == 18
    assert body["room_utilization"]["records"] == 12
    assert body["instructor_allocation"]["records"] == 14
    assert body["schedule_conflicts"]["records"] == 3


@patch("app.modules.academic_operations_runtime.timetable_runtime_router.get_timetable_runtime")
def test_timetable_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "TIMETABLE_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "timetable_statistics": {
                "course_sections_total": tenant_id,
                "schedules_total": tenant_id + 1,
                "calendar_periods_total": 2,
                "rooms_total": tenant_id + 2,
                "instructors_total": tenant_id + 3,
                "students_total": tenant_id + 4,
                "conflicts_total": tenant_id + 5,
                "capacity_alerts_total": tenant_id + 6,
                "canonical_bridge_total": tenant_id + 7,
            },
            "academic_calendar_summary": {
                "owner_module": "academic_calendar",
                "records": 2,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["academic_calendar", "scheduling"],
            },
            "room_utilization": {
                "records": tenant_id + 2,
                "utilization_rate": 70,
                "underutilized_rooms": 1,
                "overloaded_rooms": 0,
                "read_only": True,
            },
            "instructor_allocation": {
                "records": tenant_id + 3,
                "assigned_instructors": tenant_id + 2,
                "unassigned_sections": 1,
                "read_only": True,
            },
            "student_schedule_summary": {
                "owner_module": "timetable_management",
                "records": tenant_id + 4,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["scheduling", "student_lifecycle"],
            },
            "schedule_conflicts": {
                "records": tenant_id + 5,
                "conflict_rate": 20,
                "critical_conflicts": 1,
                "read_only": True,
            },
            "capacity_indicators": {
                "records": tenant_id + 6,
                "over_capacity_sections": 1,
                "under_capacity_sections": 0,
                "read_only": True,
            },
            "timetable_health": {"healthy": True, "consistency_score": 84, "issues": []},
            "timetable_readiness": {"ready_for_runtime": True, "checklist": ["read_only_runtime"], "readiness_score": 88},
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 7, "name": "Tenant-7"}
    tenant7 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 11, "name": "Tenant-11"}
    tenant11 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant7.status_code == 200
    assert tenant11.status_code == 200
    assert tenant7.json()["tenant_id"] == 7
    assert tenant11.json()["tenant_id"] == 11


@patch("app.modules.academic_operations_runtime.timetable_runtime_router.get_timetable_runtime")
def test_timetable_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="737",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_timetable_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405
