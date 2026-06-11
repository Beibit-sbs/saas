from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from tests.conftest import client


BASE = "/api/v1/student-success/runtime-shell"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="605",
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


def test_runtime_shell_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.student_success_runtime.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_surface_contract(mock_runtime_shell) -> None:
    mock_runtime_shell.return_value = {
        "tenant_id": 1,
        "owner_module": "student_success_brain",
        "runtime_shell": "STUDENT_SUCCESS_RUNTIME_SHELL",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-11T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "student_success_overview": {
            "owner_module": "student_success_brain",
            "records": 12,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle"],
        },
        "lifecycle_summary": {
            "owner_module": "student_lifecycle",
            "records": 24,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle"],
        },
        "retention_summary": {
            "owner_module": "student_success_brain",
            "records": 8,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "student_success_analytics"],
        },
        "risk_summary": {
            "owner_module": "student_success_brain",
            "records": 10,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "student_services"],
        },
        "intervention_summary": {
            "owner_module": "student_services",
            "records": 6,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["interventions", "student_lifecycle"],
        },
        "advisor_summary": {
            "owner_module": "student_success_brain",
            "records": 5,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_services", "interventions"],
        },
        "signal_summary": {
            "owner_module": "student_success_brain",
            "records": 11,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "finance", "career", "alumni"],
        },
        "dashboard_summary": {
            "owner_module": "student_success_brain",
            "records": 30,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_success_brain", "student_lifecycle", "reporting_runtime"],
        },
        "safety": {
            "read_only": True,
            "aggregator_only": True,
            "tenant_aware": True,
            "summary_read_required": True,
            "workflow_execution_enabled": False,
            "provider_mutation_enabled": False,
            "limitations": ["read_only_runtime", "no_provider_mutation"],
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["owner_module"] == "student_success_brain"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["tenant_aware"] is True
    assert body["safety"]["workflow_execution_enabled"] is False


@patch("app.modules.student_success_runtime.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_preserves_tenant_isolation(mock_runtime_shell) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "student_success_brain",
            "runtime_shell": "STUDENT_SUCCESS_RUNTIME_SHELL",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-11T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "student_success_overview": {"owner_module": "student_success_brain", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "lifecycle_summary": {"owner_module": "student_lifecycle", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "retention_summary": {"owner_module": "student_success_brain", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "risk_summary": {"owner_module": "student_success_brain", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "intervention_summary": {"owner_module": "student_services", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["interventions"]},
            "advisor_summary": {"owner_module": "student_success_brain", "records": tenant_id + 5, "read_only": True, "aggregator_only": True, "source_modules": ["student_services"]},
            "signal_summary": {"owner_module": "student_success_brain", "records": tenant_id + 6, "read_only": True, "aggregator_only": True, "source_modules": ["finance", "career", "alumni"]},
            "dashboard_summary": {"owner_module": "student_success_brain", "records": tenant_id + 7, "read_only": True, "aggregator_only": True, "source_modules": ["student_success_brain"]},
            "safety": {
                "read_only": True,
                "aggregator_only": True,
                "tenant_aware": True,
                "summary_read_required": True,
                "workflow_execution_enabled": False,
                "provider_mutation_enabled": False,
                "limitations": ["read_only_runtime"],
            },
        }

    mock_runtime_shell.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 3, "name": "Tenant-3"}
    tenant3 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 11, "name": "Tenant-11"}
    tenant11 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant3.status_code == 200
    assert tenant11.status_code == 200
    assert tenant3.json()["tenant_id"] == 3
    assert tenant11.json()["tenant_id"] == 11


@patch("app.modules.student_success_runtime.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_rejects_missing_summary_permission(mock_runtime_shell) -> None:
    mock_runtime_shell.return_value = {}
    token = create_access_token(
        user_id="705",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["student_lifecycle.dashboard.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
