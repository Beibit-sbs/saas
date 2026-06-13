from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.academic_operations_runtime.academic_operations_signals_runtime_service import (
    get_academic_operations_signals_runtime,
)
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/signals"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="813",
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


def _runtime_payload(tenant_id: int) -> dict:
    return {
        "tenant_id": tenant_id,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "ACADEMIC_OPERATIONS_SIGNALS_RUNTIME",
            "generated_at": "2026-06-13T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "signal_summary": {
            "total_signals": 10,
            "high_priority_total": 3,
            "medium_priority_total": 4,
            "low_priority_total": 3,
            "read_only": True,
        },
        "signal_distribution": {
            "by_severity": {"HIGH": 3, "MEDIUM": 4, "LOW": 3},
            "by_domain": {
                "curriculum": 2,
                "timetable": 2,
                "attendance": 2,
                "assessment": 2,
                "teaching_load": 2,
                "internship": 2,
            },
            "read_only": True,
        },
        "high_priority_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 3,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "brain_core"],
            "items": [
                {
                    "signal_id": "AO-SIG-001",
                    "signal_name": "Curriculum Coverage Risk",
                    "severity": "HIGH",
                    "score": 82,
                    "status": "ACTION_REQUIRED",
                    "summary": "High curriculum risk.",
                    "source_modules": ["academic_operations", "brain_core"],
                    "read_only": True,
                }
            ],
        },
        "medium_priority_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 4,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "brain_core"],
            "items": [],
        },
        "low_priority_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 3,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "brain_core"],
            "items": [],
        },
        "curriculum_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "curriculum", "brain_core"],
            "items": [],
        },
        "timetable_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["scheduling", "academic_operations", "brain_core"],
            "items": [],
        },
        "attendance_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["attendance", "academic_operations", "brain_core"],
            "items": [],
        },
        "assessment_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "scheduling", "brain_core"],
            "items": [],
        },
        "teaching_load_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["faculty", "academic_operations", "brain_core"],
            "items": [],
        },
        "internship_signals": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["internship", "academic_operations", "brain_core"],
            "items": [],
        },
        "health_score": {
            "composite_score": 64,
            "classification": "WATCH",
            "contributing_factors": ["curriculum_risk=82"],
            "read_only": True,
        },
        "recommended_actions": [
            {
                "action_id": "AO-ACT-001",
                "title": "Mitigate Curriculum Coverage Risk",
                "priority": "HIGH",
                "rationale": "High curriculum risk.",
                "source_signal_ids": ["AO-SIG-001"],
            }
        ],
    }


def test_signals_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_router.get_academic_operations_signals_runtime")
def test_signals_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = _runtime_payload(1)

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "ACADEMIC_OPERATIONS_SIGNALS_RUNTIME"
    assert body["signal_summary"]["total_signals"] == 10
    assert body["high_priority_signals"]["records"] == 3
    assert body["health_score"]["classification"] == "WATCH"


@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_router.get_academic_operations_signals_runtime")
def test_signals_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    mock_runtime.side_effect = lambda _db, tenant_id: _runtime_payload(tenant_id)

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 7, "name": "Tenant-7"}
    tenant7 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant7.status_code == 200
    assert tenant12.status_code == 200
    assert tenant7.json()["tenant_id"] == 7
    assert tenant12.json()["tenant_id"] == 12


@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_router.get_academic_operations_signals_runtime")
def test_signals_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="814",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )

    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_signals_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405


@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_academic_registry_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_curriculum_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_timetable_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_attendance_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_assessment_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_teaching_load_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_signals_runtime_service.get_internship_runtime")
def test_signals_runtime_aggregation_and_read_only_behavior(
    mock_internship,
    mock_teaching_load,
    mock_assessment,
    mock_attendance,
    mock_timetable,
    mock_curriculum,
    mock_registry,
) -> None:
    mock_registry.return_value = SimpleNamespace(health=SimpleNamespace(consistency_score=81))
    mock_curriculum.return_value = SimpleNamespace(
        curriculum_health=SimpleNamespace(consistency_score=77),
        curriculum_risks=SimpleNamespace(risk_score=44),
    )
    mock_timetable.return_value = SimpleNamespace(
        schedule_conflicts=SimpleNamespace(conflict_rate=18, critical_conflicts=2),
        timetable_health=SimpleNamespace(consistency_score=79),
    )
    mock_attendance.return_value = SimpleNamespace(
        attendance_risk_summary=SimpleNamespace(risk_score=51),
        attendance_trends=SimpleNamespace(declining_count=9, improving_count=4),
        attendance_statistics=SimpleNamespace(at_risk_students_total=14),
    )
    mock_assessment.return_value = SimpleNamespace(
        assessment_risk_summary=SimpleNamespace(risk_score=47),
        grading_distribution=SimpleNamespace(critical_band=3),
    )
    mock_teaching_load.return_value = SimpleNamespace(
        overload_risk_summary=SimpleNamespace(risk_score=42),
        coverage_risk_summary=SimpleNamespace(risk_score=38),
        faculty_workload_distribution=SimpleNamespace(fairness_alert_total=2),
    )
    mock_internship.return_value = SimpleNamespace(
        internship_readiness=SimpleNamespace(readiness_score=63),
        internship_risk_summary=SimpleNamespace(high_risk_count=2),
        employer_engagement=SimpleNamespace(employer_participation_rate=41.0, repeat_employers=1),
    )

    db = MagicMock(spec=Session)
    result = get_academic_operations_signals_runtime(db, 5)

    assert result.tenant_id == 5
    assert result.signal_summary.total_signals == 10
    assert len(result.high_priority_signals.items) + len(result.medium_priority_signals.items) + len(result.low_priority_signals.items) == 10
    assert sorted(signal.signal_id for signal in result.high_priority_signals.items + result.medium_priority_signals.items + result.low_priority_signals.items) == [
        "AO-SIG-001",
        "AO-SIG-002",
        "AO-SIG-003",
        "AO-SIG-004",
        "AO-SIG-005",
        "AO-SIG-006",
        "AO-SIG-007",
        "AO-SIG-008",
        "AO-SIG-009",
        "AO-SIG-010",
    ]
    assert 0 <= result.health_score.composite_score <= 100
    assert result.signal_distribution.by_severity["HIGH"] + result.signal_distribution.by_severity["MEDIUM"] + result.signal_distribution.by_severity["LOW"] == 10

    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()
