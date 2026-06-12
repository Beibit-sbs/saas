from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from tests.conftest import client


BASE = "/api/v1/student-success/dashboard"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="1413",
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


def test_student_success_dashboard_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.student_success_runtime.student_success_dashboard_runtime_router.get_student_success_dashboard_runtime")
def test_student_success_dashboard_runtime_payload_and_read_only_contract(mock_runtime) -> None:
    payload = {
        "tenant_id": 1,
        "owner_module": "student_success_brain",
        "runtime_surface": "STUDENT_SUCCESS_DASHBOARD_RUNTIME",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-12T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "executive_summary": {
            "owner_module": "student_success_brain",
            "records": 66,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_success_runtime_shell", "student_success_signals_runtime", "reporting_runtime"],
        },
        "student_population": {
            "owner_module": "student_success_brain",
            "records": 53,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_registry_runtime", "student_lifecycle"],
        },
        "retention_overview": {
            "owner_module": "student_success_brain",
            "records": 42,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_retention_runtime", "student_success_analytics"],
        },
        "academic_risk_overview": {
            "owner_module": "student_success_brain",
            "records": 39,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_academic_risk_runtime", "academic_operations"],
        },
        "attendance_risk_overview": {
            "owner_module": "student_success_brain",
            "records": 36,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_attendance_risk_runtime", "attendance_tracking"],
        },
        "intervention_overview": {
            "owner_module": "student_success_brain",
            "records": 47,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_intervention_runtime", "interventions"],
        },
        "advisor_overview": {
            "owner_module": "student_success_brain",
            "records": 35,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_advisor_runtime", "advising"],
        },
        "success_signals": {
            "owner_module": "student_success_brain",
            "records": 120,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_success_signals_runtime", "student_success_analytics"],
        },
        "priority_actions": {
            "owner_module": "student_success_brain",
            "records": 74,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_success_signals_runtime", "student_intervention_runtime", "student_advisor_runtime"],
        },
        "dashboard_kpis": {
            "owner_module": "student_success_brain",
            "records": 385,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_success_runtime_shell", "student_success_signals_runtime", "reporting_runtime"],
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
            "notification_execution_enabled": False,
            "provider_mutation_enabled": False,
            "outbound_integrations_enabled": False,
            "scheduling_engine_enabled": False,
            "persistence_enabled": False,
            "limitations": ["read_only_runtime", "no_scheduling_engine"],
        },
    }
    mock_runtime.return_value = payload

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body == payload
    assert body["runtime_surface"] == "STUDENT_SUCCESS_DASHBOARD_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["write_operations_enabled"] is False
    assert body["safety"]["workflow_execution_enabled"] is False
    assert body["safety"]["approval_execution_enabled"] is False
    assert body["safety"]["background_jobs_enabled"] is False
    assert body["safety"]["notification_execution_enabled"] is False
    assert body["safety"]["provider_mutation_enabled"] is False
    assert body["safety"]["outbound_integrations_enabled"] is False
    assert body["safety"]["scheduling_engine_enabled"] is False
    assert body["safety"]["persistence_enabled"] is False


@patch("app.modules.student_success_runtime.student_success_dashboard_runtime_router.get_student_success_dashboard_runtime")
def test_student_success_dashboard_runtime_tenant_enforcement(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "student_success_brain",
            "runtime_surface": "STUDENT_SUCCESS_DASHBOARD_RUNTIME",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "executive_summary": {"owner_module": "student_success_brain", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["student_success_runtime_shell"]},
            "student_population": {"owner_module": "student_success_brain", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["student_registry_runtime"]},
            "retention_overview": {"owner_module": "student_success_brain", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["student_retention_runtime"]},
            "academic_risk_overview": {"owner_module": "student_success_brain", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["student_academic_risk_runtime"]},
            "attendance_risk_overview": {"owner_module": "student_success_brain", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["student_attendance_risk_runtime"]},
            "intervention_overview": {"owner_module": "student_success_brain", "records": tenant_id + 5, "read_only": True, "aggregator_only": True, "source_modules": ["student_intervention_runtime"]},
            "advisor_overview": {"owner_module": "student_success_brain", "records": tenant_id + 6, "read_only": True, "aggregator_only": True, "source_modules": ["student_advisor_runtime"]},
            "success_signals": {"owner_module": "student_success_brain", "records": tenant_id + 7, "read_only": True, "aggregator_only": True, "source_modules": ["student_success_signals_runtime"]},
            "priority_actions": {"owner_module": "student_success_brain", "records": tenant_id + 8, "read_only": True, "aggregator_only": True, "source_modules": ["student_success_signals_runtime"]},
            "dashboard_kpis": {"owner_module": "student_success_brain", "records": tenant_id + 9, "read_only": True, "aggregator_only": True, "source_modules": ["student_success_runtime_shell"]},
            "safety": {
                "read_only": True,
                "aggregator_only": True,
                "tenant_aware": True,
                "summary_read_required": True,
                "write_operations_enabled": False,
                "workflow_execution_enabled": False,
                "approval_execution_enabled": False,
                "background_jobs_enabled": False,
                "notification_execution_enabled": False,
                "provider_mutation_enabled": False,
                "outbound_integrations_enabled": False,
                "scheduling_engine_enabled": False,
                "persistence_enabled": False,
                "limitations": ["read_only_runtime"],
            },
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 10, "name": "Tenant-10"}
    tenant10 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 22, "name": "Tenant-22"}
    tenant22 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant10.status_code == 200
    assert tenant22.status_code == 200
    assert tenant10.json()["tenant_id"] == 10
    assert tenant22.json()["tenant_id"] == 22


@patch("app.modules.student_success_runtime.student_success_dashboard_runtime_router.get_student_success_dashboard_runtime")
def test_student_success_dashboard_runtime_rejects_missing_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="1514",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["student_lifecycle.dashboard.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
