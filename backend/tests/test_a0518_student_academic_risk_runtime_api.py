from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from tests.conftest import client


BASE = "/api/v1/student-success/academic-risk"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="808",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["student_success.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_student_lifecycle_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_student_lifecycle_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_student_academic_risk_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.student_success_runtime.student_academic_risk_runtime_router.get_student_academic_risk_runtime")
def test_student_academic_risk_runtime_payload_and_read_only_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "owner_module": "student_success_brain",
        "runtime_surface": "STUDENT_ACADEMIC_RISK_RUNTIME",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-12T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "academic_risk_summary": {
            "owner_module": "student_success_brain",
            "records": 21,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "academic_operations"],
        },
        "gpa_risk_distribution": {
            "owner_module": "student_success_brain",
            "records": 16,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "academic_operations"],
        },
        "failed_course_risk_summary": {
            "owner_module": "student_success_brain",
            "records": 12,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "degree_progress"],
        },
        "low_performance_summary": {
            "owner_module": "student_success_brain",
            "records": 11,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "student_lifecycle"],
        },
        "probation_summary": {
            "owner_module": "student_success_brain",
            "records": 9,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_services", "student_lifecycle"],
        },
        "progression_risk_summary": {
            "owner_module": "student_success_brain",
            "records": 13,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["degree_progress", "student_lifecycle"],
        },
        "academic_alert_summary": {
            "owner_module": "student_success_brain",
            "records": 10,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["interventions", "student_services", "advising"],
        },
        "academic_signal_summary": {
            "owner_module": "student_success_brain",
            "records": 28,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["brain_core", "analytics", "student_lifecycle"],
        },
        "safety": {
            "read_only": True,
            "aggregator_only": True,
            "tenant_aware": True,
            "summary_read_required": True,
            "write_operations_enabled": False,
            "workflow_execution_enabled": False,
            "approval_execution_enabled": False,
            "background_jobs_enabled": False,
            "provider_mutation_enabled": False,
            "outbound_integrations_enabled": False,
            "limitations": ["read_only_runtime", "no_outbound_integrations"],
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["runtime_surface"] == "STUDENT_ACADEMIC_RISK_RUNTIME"
    assert body["academic_risk_summary"]["owner_module"] == "student_success_brain"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["write_operations_enabled"] is False
    assert body["safety"]["workflow_execution_enabled"] is False
    assert body["safety"]["approval_execution_enabled"] is False
    assert body["safety"]["background_jobs_enabled"] is False
    assert body["safety"]["provider_mutation_enabled"] is False
    assert body["safety"]["outbound_integrations_enabled"] is False


@patch("app.modules.student_success_runtime.student_academic_risk_runtime_router.get_student_academic_risk_runtime")
def test_student_academic_risk_runtime_tenant_enforcement(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "student_success_brain",
            "runtime_surface": "STUDENT_ACADEMIC_RISK_RUNTIME",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "academic_risk_summary": {"owner_module": "student_success_brain", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "gpa_risk_distribution": {"owner_module": "student_success_brain", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "failed_course_risk_summary": {"owner_module": "student_success_brain", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["degree_progress"]},
            "low_performance_summary": {"owner_module": "student_success_brain", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "probation_summary": {"owner_module": "student_success_brain", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["student_services"]},
            "progression_risk_summary": {"owner_module": "student_success_brain", "records": tenant_id + 5, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "academic_alert_summary": {"owner_module": "student_success_brain", "records": tenant_id + 6, "read_only": True, "aggregator_only": True, "source_modules": ["interventions"]},
            "academic_signal_summary": {"owner_module": "student_success_brain", "records": tenant_id + 7, "read_only": True, "aggregator_only": True, "source_modules": ["brain_core", "analytics"]},
            "safety": {
                "read_only": True,
                "aggregator_only": True,
                "tenant_aware": True,
                "summary_read_required": True,
                "write_operations_enabled": False,
                "workflow_execution_enabled": False,
                "approval_execution_enabled": False,
                "background_jobs_enabled": False,
                "provider_mutation_enabled": False,
                "outbound_integrations_enabled": False,
                "limitations": ["read_only_runtime"],
            },
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 6, "name": "Tenant-6"}
    tenant6 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant6.status_code == 200
    assert tenant12.status_code == 200
    assert tenant6.json()["tenant_id"] == 6
    assert tenant12.json()["tenant_id"] == 12


@patch("app.modules.student_success_runtime.student_academic_risk_runtime_router.get_student_academic_risk_runtime")
def test_student_academic_risk_runtime_rejects_missing_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="909",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["student_lifecycle.dashboard.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
