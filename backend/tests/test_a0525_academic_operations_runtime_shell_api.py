from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/v1/academic-operations/runtime-shell"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="605",
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


def test_runtime_shell_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_surface_contract(mock_runtime_shell) -> None:
    mock_runtime_shell.return_value = {
        "tenant_id": 1,
        "owner_module": "academic_operations",
        "runtime_shell": "ACADEMIC_OPERATIONS_RUNTIME_SHELL",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-12T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "runtime_shell_summary": {
            "owner_module": "academic_operations",
            "records": 32,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations"],
        },
        "runtime_shell_domain": {
            "owner_module": "academic_operations",
            "records": 18,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "course_catalog_management"],
        },
        "runtime_shell_runtime": {
            "owner_module": "academic_operations_runtime",
            "records": 45,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "scheduling", "grades"],
        },
        "runtime_shell_integration": {
            "owner_module": "academic_operations_runtime",
            "records": 7,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["student_information_system_integration", "learning_management_system_integration"],
        },
        "runtime_shell_readiness": {
            "owner_module": "academic_operations_runtime",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations_runtime"],
        },
        "safety": {
            "read_only": True,
            "aggregator_only": True,
            "tenant_aware": True,
            "summary_read_required": True,
            "workflow_execution_enabled": False,
            "approval_execution_enabled": False,
            "background_jobs_enabled": False,
            "provider_mutation_enabled": False,
            "limitations": ["read_only_runtime", "no_provider_mutation"],
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["owner_module"] == "academic_operations"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["summary_read_required"] is True
    assert body["safety"]["workflow_execution_enabled"] is False
    assert body["safety"]["approval_execution_enabled"] is False


@patch("app.modules.academic_operations_runtime.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_preserves_tenant_isolation(mock_runtime_shell) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "academic_operations",
            "runtime_shell": "ACADEMIC_OPERATIONS_RUNTIME_SHELL",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "runtime_shell_summary": {"owner_module": "academic_operations", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "runtime_shell_domain": {"owner_module": "academic_operations", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "runtime_shell_runtime": {"owner_module": "academic_operations_runtime", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations"]},
            "runtime_shell_integration": {"owner_module": "academic_operations_runtime", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["student_information_system_integration"]},
            "runtime_shell_readiness": {"owner_module": "academic_operations_runtime", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["academic_operations_runtime"]},
            "safety": {
                "read_only": True,
                "aggregator_only": True,
                "tenant_aware": True,
                "summary_read_required": True,
                "workflow_execution_enabled": False,
                "approval_execution_enabled": False,
                "background_jobs_enabled": False,
                "provider_mutation_enabled": False,
                "limitations": ["read_only_runtime"],
            },
        }

    mock_runtime_shell.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 4, "name": "Tenant-4"}
    tenant4 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant4.status_code == 200
    assert tenant12.status_code == 200
    assert tenant4.json()["tenant_id"] == 4
    assert tenant12.json()["tenant_id"] == 12


@patch("app.modules.academic_operations_runtime.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_rejects_missing_summary_permission(mock_runtime_shell) -> None:
    mock_runtime_shell.return_value = {}
    token = create_access_token(
        user_id="705",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
