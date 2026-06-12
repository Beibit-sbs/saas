from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/academic-registry"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="706",
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


def test_academic_registry_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.academic_registry_runtime_router.get_academic_registry_runtime")
def test_academic_registry_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "ACADEMIC_REGISTRY_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "registry_statistics": {
            "academic_periods_total": 4,
            "academic_groups_total": 9,
            "curriculum_registry_total": 7,
            "course_catalog_linkage_total": 3,
            "student_registry_linkage_total": 12,
            "canonical_bridge_total": 2,
        },
        "academic_periods": {
            "owner_module": "academic_operations",
            "records": 4,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations"],
        },
        "academic_groups": {
            "owner_module": "academic_operations",
            "records": 9,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations"],
        },
        "curriculum_linkage": {
            "owner_module": "academic_operations",
            "records": 7,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["academic_operations", "course_catalog_management"],
        },
        "catalog_linkage": {
            "owner_module": "academic_operations",
            "records": 3,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["course_catalog_management"],
        },
        "sis_status": {
            "provider": "student_information_system_integration",
            "status": "READINESS_ONLY",
            "integration_mode": "READINESS_ONLY",
            "ready": True,
            "evidence_count": 0,
            "read_only": True,
        },
        "lms_status": {
            "provider": "learning_management_system_integration",
            "status": "READINESS_ONLY",
            "integration_mode": "READINESS_ONLY",
            "ready": True,
            "evidence_count": 0,
            "read_only": True,
        },
        "health": {
            "healthy": True,
            "consistency_score": 88,
            "issues": [],
        },
        "readiness": {
            "ready_for_runtime": True,
            "checklist": ["read_only_runtime", "aggregator_only_runtime"],
            "readiness_score": 90,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "ACADEMIC_REGISTRY_RUNTIME"
    assert body["registry_statistics"]["academic_groups_total"] == 9
    assert body["sis_status"]["status"] == "READINESS_ONLY"
    assert body["lms_status"]["status"] == "READINESS_ONLY"
    assert body["health"]["healthy"] is True


@patch("app.modules.academic_operations_runtime.academic_registry_runtime_router.get_academic_registry_runtime")
def test_academic_registry_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "ACADEMIC_REGISTRY_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "registry_statistics": {
                "academic_periods_total": tenant_id,
                "academic_groups_total": tenant_id + 1,
                "curriculum_registry_total": tenant_id + 2,
                "course_catalog_linkage_total": tenant_id + 3,
                "student_registry_linkage_total": tenant_id + 4,
                "canonical_bridge_total": tenant_id + 5,
            },
            "academic_periods": {
                "owner_module": "academic_operations",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["academic_operations"],
            },
            "academic_groups": {
                "owner_module": "academic_operations",
                "records": tenant_id + 1,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["academic_operations"],
            },
            "curriculum_linkage": {
                "owner_module": "academic_operations",
                "records": tenant_id + 2,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["academic_operations"],
            },
            "catalog_linkage": {
                "owner_module": "academic_operations",
                "records": tenant_id + 3,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["course_catalog_management"],
            },
            "sis_status": {
                "provider": "student_information_system_integration",
                "status": "READINESS_ONLY",
                "integration_mode": "READINESS_ONLY",
                "ready": True,
                "evidence_count": 0,
                "read_only": True,
            },
            "lms_status": {
                "provider": "learning_management_system_integration",
                "status": "READINESS_ONLY",
                "integration_mode": "READINESS_ONLY",
                "ready": True,
                "evidence_count": 0,
                "read_only": True,
            },
            "health": {"healthy": True, "consistency_score": 80, "issues": []},
            "readiness": {"ready_for_runtime": True, "checklist": ["read_only_runtime"], "readiness_score": 85},
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 5, "name": "Tenant-5"}
    tenant5 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 9, "name": "Tenant-9"}
    tenant9 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant5.status_code == 200
    assert tenant9.status_code == 200
    assert tenant5.json()["tenant_id"] == 5
    assert tenant9.json()["tenant_id"] == 9


@patch("app.modules.academic_operations_runtime.academic_registry_runtime_router.get_academic_registry_runtime")
def test_academic_registry_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="707",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_academic_registry_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405
