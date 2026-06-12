from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from tests.conftest import client


BASE = "/api/v1/student-success/advisors"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="1411",
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


def test_student_advisor_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.student_success_runtime.student_advisor_runtime_router.get_student_advisor_runtime")
def test_student_advisor_runtime_payload_and_read_only_contract(mock_runtime) -> None:
    payload = {
        "tenant_id": 1,
        "owner_module": "student_success_brain",
        "runtime_surface": "STUDENT_ADVISOR_RUNTIME",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-12T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "advisor_summary": {
            "owner_module": "student_success_brain",
            "records": 22,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "advising", "student_services"],
        },
        "advisor_workload_distribution": {
            "owner_module": "student_success_brain",
            "records": 14,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["advising", "interventions", "student_services"],
        },
        "advisor_student_assignments": {
            "owner_module": "student_success_brain",
            "records": 12,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "advising"],
        },
        "advisor_intervention_queue": {
            "owner_module": "student_success_brain",
            "records": 11,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["interventions", "student_success_analytics"],
        },
        "advisor_follow_up_summary": {
            "owner_module": "student_success_brain",
            "records": 10,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_services", "advising", "interventions"],
        },
        "advisor_risk_coverage": {
            "owner_module": "student_success_brain",
            "records": 13,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "student_lifecycle", "student_services"],
        },
        "advisor_effectiveness_summary": {
            "owner_module": "student_success_brain",
            "records": 15,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["analytics", "advising", "reporting_runtime"],
        },
        "advisor_signal_summary": {
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
            "intervention_execution_enabled": False,
            "workflow_execution_enabled": False,
            "approval_execution_enabled": False,
            "background_jobs_enabled": False,
            "notification_execution_enabled": False,
            "provider_mutation_enabled": False,
            "outbound_integrations_enabled": False,
            "scheduling_engine_enabled": False,
            "limitations": ["read_only_runtime", "no_scheduling_engine"],
        },
    }
    mock_runtime.return_value = payload

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body == payload
    assert body["runtime_surface"] == "STUDENT_ADVISOR_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["write_operations_enabled"] is False
    assert body["safety"]["intervention_execution_enabled"] is False
    assert body["safety"]["workflow_execution_enabled"] is False
    assert body["safety"]["approval_execution_enabled"] is False
    assert body["safety"]["background_jobs_enabled"] is False
    assert body["safety"]["notification_execution_enabled"] is False
    assert body["safety"]["provider_mutation_enabled"] is False
    assert body["safety"]["outbound_integrations_enabled"] is False
    assert body["safety"]["scheduling_engine_enabled"] is False


@patch("app.modules.student_success_runtime.student_advisor_runtime_router.get_student_advisor_runtime")
def test_student_advisor_runtime_tenant_enforcement(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "student_success_brain",
            "runtime_surface": "STUDENT_ADVISOR_RUNTIME",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "advisor_summary": {"owner_module": "student_success_brain", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "advisor_workload_distribution": {"owner_module": "student_success_brain", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["advising"]},
            "advisor_student_assignments": {"owner_module": "student_success_brain", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "advisor_intervention_queue": {"owner_module": "student_success_brain", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["interventions"]},
            "advisor_follow_up_summary": {"owner_module": "student_success_brain", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["student_services"]},
            "advisor_risk_coverage": {"owner_module": "student_success_brain", "records": tenant_id + 5, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "advisor_effectiveness_summary": {"owner_module": "student_success_brain", "records": tenant_id + 6, "read_only": True, "aggregator_only": True, "source_modules": ["analytics"]},
            "advisor_signal_summary": {"owner_module": "student_success_brain", "records": tenant_id + 7, "read_only": True, "aggregator_only": True, "source_modules": ["brain_core", "analytics"]},
            "safety": {
                "read_only": True,
                "aggregator_only": True,
                "tenant_aware": True,
                "summary_read_required": True,
                "write_operations_enabled": False,
                "intervention_execution_enabled": False,
                "workflow_execution_enabled": False,
                "approval_execution_enabled": False,
                "background_jobs_enabled": False,
                "notification_execution_enabled": False,
                "provider_mutation_enabled": False,
                "outbound_integrations_enabled": False,
                "scheduling_engine_enabled": False,
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


@patch("app.modules.student_success_runtime.student_advisor_runtime_router.get_student_advisor_runtime")
def test_student_advisor_runtime_rejects_missing_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="1512",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["student_lifecycle.dashboard.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
