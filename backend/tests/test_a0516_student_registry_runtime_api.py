from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from tests.conftest import client


BASE = "/api/v1/student-success/student-registry"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="606",
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


def test_student_registry_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.student_success_runtime.student_registry_runtime_router.get_student_registry_runtime")
def test_student_registry_runtime_surface_contract(mock_registry_runtime) -> None:
    mock_registry_runtime.return_value = {
        "tenant_id": 1,
        "owner_module": "student_success_brain",
        "runtime_surface": "STUDENT_REGISTRY_RUNTIME",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-12T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "student_registry_summary": {
            "owner_module": "student_lifecycle",
            "records": 21,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle"],
        },
        "enrollment_summary": {
            "owner_module": "student_lifecycle",
            "records": 11,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle"],
        },
        "academic_standing_summary": {
            "owner_module": "student_success_brain",
            "records": 9,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "student_lifecycle"],
        },
        "retention_link_summary": {
            "owner_module": "student_success_brain",
            "records": 8,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle", "student_success_analytics"],
        },
        "advisor_link_summary": {
            "owner_module": "student_success_brain",
            "records": 6,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_services", "interventions"],
        },
        "risk_link_summary": {
            "owner_module": "student_success_brain",
            "records": 7,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "student_services", "student_lifecycle"],
        },
        "lifecycle_status_summary": {
            "owner_module": "student_lifecycle",
            "records": 34,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_lifecycle"],
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
            "outbound_calls_enabled": False,
            "limitations": ["read_only_runtime", "no_outbound_calls"],
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["runtime_surface"] == "STUDENT_REGISTRY_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["tenant_aware"] is True
    assert body["safety"]["workflow_execution_enabled"] is False
    assert body["safety"]["approval_execution_enabled"] is False
    assert body["safety"]["background_jobs_enabled"] is False
    assert body["safety"]["outbound_calls_enabled"] is False


@patch("app.modules.student_success_runtime.student_registry_runtime_router.get_student_registry_runtime")
def test_student_registry_runtime_preserves_tenant_isolation(mock_registry_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "student_success_brain",
            "runtime_surface": "STUDENT_REGISTRY_RUNTIME",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "student_registry_summary": {"owner_module": "student_lifecycle", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "enrollment_summary": {"owner_module": "student_lifecycle", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
            "academic_standing_summary": {"owner_module": "student_success_brain", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "retention_link_summary": {"owner_module": "student_success_brain", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["student_success_analytics"]},
            "advisor_link_summary": {"owner_module": "student_success_brain", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["student_services"]},
            "risk_link_summary": {"owner_module": "student_success_brain", "records": tenant_id + 5, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations", "student_services"]},
            "lifecycle_status_summary": {"owner_module": "student_lifecycle", "records": tenant_id + 6, "read_only": True, "aggregator_only": True, "source_modules": ["student_lifecycle"]},
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
                "outbound_calls_enabled": False,
                "limitations": ["read_only_runtime"],
            },
        }

    mock_registry_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 4, "name": "Tenant-4"}
    tenant4 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant4.status_code == 200
    assert tenant12.status_code == 200
    assert tenant4.json()["tenant_id"] == 4
    assert tenant12.json()["tenant_id"] == 12


@patch("app.modules.student_success_runtime.student_registry_runtime_router.get_student_registry_runtime")
def test_student_registry_runtime_rejects_missing_summary_permission(mock_registry_runtime) -> None:
    mock_registry_runtime.return_value = {}
    token = create_access_token(
        user_id="706",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["student_lifecycle.dashboard.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
