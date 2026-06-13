from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service import (
    get_academic_operations_dashboard_runtime,
)
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/dashboard"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="913",
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
            "runtime_scope": "ACADEMIC_OPERATIONS_DASHBOARD_RUNTIME",
            "generated_at": "2026-06-13T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "kpi_summary": {
            "runtime_slice_count": 9,
            "aggregated_records_total": 220,
            "high_priority_total": 3,
            "recommended_actions_total": 4,
            "read_only": True,
        },
        "registry_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 32,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations_runtime_shell", "academic_registry_runtime"],
        },
        "curriculum_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 28,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["curriculum_runtime", "course_catalog_management", "prerequisite_management"],
        },
        "timetable_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 34,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["timetable_runtime", "scheduling"],
        },
        "attendance_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 29,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["attendance_runtime", "attendance"],
        },
        "assessment_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 25,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["assessment_runtime", "grades", "exam_governance"],
        },
        "teaching_load_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 24,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["teaching_load_runtime", "faculty", "teaching_load_contracts"],
        },
        "internship_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 22,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["internship_runtime", "internship"],
        },
        "signals_summary": {
            "owner_module": "academic_operations_runtime",
            "records": 26,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations_signals_runtime", "brain_core"],
        },
        "high_priority_items": [
            {
                "item_id": "AO-SIG-001",
                "title": "Curriculum Coverage Risk",
                "priority": "HIGH",
                "status": "ACTION_REQUIRED",
                "score": 82,
                "domain": "curriculum",
                "source_signal_ids": ["AO-SIG-001"],
                "read_only": True,
            }
        ],
        "recommended_actions": [
            {
                "action_id": "AO-ACT-001",
                "title": "Mitigate Curriculum Coverage Risk",
                "priority": "HIGH",
                "rationale": "High curriculum risk.",
                "source_signal_ids": ["AO-SIG-001"],
            }
        ],
        "academic_operations_health_score": {
            "composite_score": 68,
            "classification": "WATCH",
            "contributing_factors": ["curriculum_consistency=77"],
            "read_only": True,
        },
    }


def test_dashboard_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_router.get_academic_operations_dashboard_runtime")
def test_dashboard_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = _runtime_payload(1)

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "ACADEMIC_OPERATIONS_DASHBOARD_RUNTIME"
    assert body["kpi_summary"]["runtime_slice_count"] == 9
    assert body["signals_summary"]["records"] == 26
    assert body["academic_operations_health_score"]["classification"] == "WATCH"


@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_router.get_academic_operations_dashboard_runtime")
def test_dashboard_runtime_enforces_tenant_isolation(mock_runtime) -> None:
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


@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_router.get_academic_operations_dashboard_runtime")
def test_dashboard_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="914",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )

    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_dashboard_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405


@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_runtime_shell")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_academic_registry_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_curriculum_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_timetable_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_attendance_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_assessment_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_teaching_load_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_internship_runtime")
@patch("app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service.get_academic_operations_signals_runtime")
def test_dashboard_runtime_aggregation_and_read_only_behavior(
    mock_signals,
    mock_internship,
    mock_teaching_load,
    mock_assessment,
    mock_attendance,
    mock_timetable,
    mock_curriculum,
    mock_registry,
    mock_runtime_shell,
) -> None:
    mock_runtime_shell.return_value = SimpleNamespace(runtime_shell_runtime=SimpleNamespace(records=18))
    mock_registry.return_value = SimpleNamespace(
        registry_statistics=SimpleNamespace(
            academic_periods_total=5,
            academic_groups_total=7,
            curriculum_registry_total=4,
            student_registry_linkage_total=3,
        ),
        health=SimpleNamespace(consistency_score=82),
    )
    mock_curriculum.return_value = SimpleNamespace(
        curriculum_statistics=SimpleNamespace(
            program_structures_total=6,
            curriculum_versions_total=5,
            learning_outcomes_total=9,
            prerequisite_chains_total=4,
        ),
        curriculum_health=SimpleNamespace(consistency_score=78),
    )
    mock_timetable.return_value = SimpleNamespace(
        timetable_statistics=SimpleNamespace(
            course_sections_total=12,
            schedules_total=8,
            conflicts_total=3,
        ),
        timetable_health=SimpleNamespace(consistency_score=81),
    )
    mock_attendance.return_value = SimpleNamespace(
        attendance_statistics=SimpleNamespace(
            tracked_students_total=24,
            at_risk_students_total=6,
            intervention_candidates_total=4,
        ),
        attendance_risk_summary=SimpleNamespace(risk_score=35),
    )
    mock_assessment.return_value = SimpleNamespace(
        assessment_statistics=SimpleNamespace(
            exams_total=10,
            completed_exams_total=7,
            assessment_signals_total=5,
        ),
        assessment_risk_summary=SimpleNamespace(risk_score=40),
    )
    mock_teaching_load.return_value = SimpleNamespace(
        teaching_load_statistics=SimpleNamespace(
            tracked_faculty_total=14,
            high_risk_assignments_total=3,
        ),
        faculty_workload_distribution=SimpleNamespace(fairness_alert_total=2),
        overload_risk_summary=SimpleNamespace(risk_score=44),
        coverage_risk_summary=SimpleNamespace(risk_score=39),
    )
    mock_internship.return_value = SimpleNamespace(
        internship_statistics=SimpleNamespace(
            total_internships=11,
            active_internships=6,
        ),
        internship_risk_summary=SimpleNamespace(high_risk_count=2),
        internship_readiness=SimpleNamespace(readiness_score=64),
    )
    mock_signals.return_value = SimpleNamespace(
        signal_summary=SimpleNamespace(total_signals=10, high_priority_total=3),
        high_priority_signals=SimpleNamespace(
            items=[
                SimpleNamespace(
                    signal_id="AO-SIG-001",
                    signal_name="Curriculum Coverage Risk",
                    severity="HIGH",
                    status="ACTION_REQUIRED",
                    score=82,
                )
            ]
        ),
        medium_priority_signals=SimpleNamespace(items=[]),
        recommended_actions=[
            SimpleNamespace(
                action_id="AO-ACT-001",
                title="Mitigate Curriculum Coverage Risk",
                priority="HIGH",
                rationale="High curriculum risk.",
                source_signal_ids=["AO-SIG-001"],
            )
        ],
        health_score=SimpleNamespace(composite_score=66),
    )

    db = MagicMock(spec=Session)
    result = get_academic_operations_dashboard_runtime(db, 5)

    assert result.tenant_id == 5
    assert result.kpi_summary.runtime_slice_count == 9
    assert result.kpi_summary.aggregated_records_total > 0
    assert result.signals_summary.records > 0
    assert len(result.high_priority_items) == 1
    assert len(result.recommended_actions) == 1
    assert 0 <= result.academic_operations_health_score.composite_score <= 100

    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()
