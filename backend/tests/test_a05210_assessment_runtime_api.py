from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/assessment"


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


def test_assessment_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.assessment_runtime_router.get_assessment_runtime")
def test_assessment_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "ASSESSMENT_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "assessment_statistics": {
            "exams_total": 7,
            "completed_exams_total": 5,
            "gradebook_entries_total": 18,
            "grading_distribution_total": 18,
            "schedule_alignment_total": 6,
            "assessment_signals_total": 4,
            "canonical_bridge_total": 9,
        },
        "exam_governance_summary": {
            "owner_module": "academic_operations",
            "records": 7,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["exam_governance", "academic_operations"],
        },
        "gradebook_readiness": {
            "owner_module": "academic_operations",
            "records": 18,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["grades", "academic_operations"],
        },
        "grading_distribution": {
            "excellent_band": 6,
            "good_band": 7,
            "warning_band": 3,
            "critical_band": 2,
            "read_only": True,
        },
        "assessment_schedule_alignment": {
            "owner_module": "academic_operations",
            "records": 6,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["scheduling", "exam_governance", "academic_operations"],
        },
        "assessment_risk_summary": {
            "risk_score": 42,
            "open_risks": 2,
            "indicators": ["exam_completion_gap", "critical_gradebook_distribution"],
            "read_only": True,
        },
        "high_risk_assessments": {
            "owner_module": "academic_operations",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["exam_governance", "grades", "scheduling"],
        },
        "assessment_signals": {
            "generated_signals": 4,
            "signal_types": ["gradebook_warning", "exam_completion_gap"],
            "read_only": True,
        },
        "assessment_readiness": {
            "ready_for_runtime": False,
            "checklist": ["read_only_runtime", "aggregator_only_runtime"],
            "readiness_score": 78,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "ASSESSMENT_RUNTIME"
    assert body["assessment_statistics"]["exams_total"] == 7
    assert body["grading_distribution"]["critical_band"] == 2
    assert body["assessment_risk_summary"]["open_risks"] == 2


@patch("app.modules.academic_operations_runtime.assessment_runtime_router.get_assessment_runtime")
def test_assessment_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "ASSESSMENT_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "assessment_statistics": {
                "exams_total": tenant_id,
                "completed_exams_total": tenant_id,
                "gradebook_entries_total": tenant_id + 10,
                "grading_distribution_total": tenant_id + 10,
                "schedule_alignment_total": tenant_id + 5,
                "assessment_signals_total": tenant_id + 3,
                "canonical_bridge_total": tenant_id + 7,
            },
            "exam_governance_summary": {
                "owner_module": "academic_operations",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["exam_governance"],
            },
            "gradebook_readiness": {
                "owner_module": "academic_operations",
                "records": tenant_id + 10,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["grades"],
            },
            "grading_distribution": {
                "excellent_band": tenant_id,
                "good_band": tenant_id,
                "warning_band": tenant_id,
                "critical_band": tenant_id,
                "read_only": True,
            },
            "assessment_schedule_alignment": {
                "owner_module": "academic_operations",
                "records": tenant_id + 5,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["scheduling", "exam_governance"],
            },
            "assessment_risk_summary": {
                "risk_score": 20,
                "open_risks": 1,
                "indicators": ["exam_completion_gap"],
                "read_only": True,
            },
            "high_risk_assessments": {
                "owner_module": "academic_operations",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["exam_governance"],
            },
            "assessment_signals": {
                "generated_signals": tenant_id + 3,
                "signal_types": ["gradebook_warning"],
                "read_only": True,
            },
            "assessment_readiness": {
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


@patch("app.modules.academic_operations_runtime.assessment_runtime_router.get_assessment_runtime")
def test_assessment_runtime_requires_summary_permission(mock_runtime) -> None:
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


def test_assessment_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405
