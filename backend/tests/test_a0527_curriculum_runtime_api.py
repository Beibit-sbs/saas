from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/curriculum"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="726",
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


def test_curriculum_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.curriculum_runtime_router.get_curriculum_runtime")
def test_curriculum_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "CURRICULUM_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "curriculum_statistics": {
            "program_structures_total": 12,
            "curriculum_versions_total": 4,
            "curriculum_health_score": 92,
            "course_catalog_linkage_total": 10,
            "prerequisite_chains_total": 7,
            "learning_outcomes_total": 15,
            "academic_plans_total": 6,
            "canonical_bridge_total": 3,
        },
        "program_structures": {
            "owner_module": "academic_operations",
            "records": 12,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["curriculum_management", "course_catalog_management"],
        },
        "curriculum_versions": {
            "owner_module": "academic_operations",
            "records": 4,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["curriculum_management"],
        },
        "curriculum_health": {
            "healthy": True,
            "consistency_score": 92,
            "issues": [],
        },
        "course_catalog_linkage": {
            "owner_module": "academic_operations",
            "records": 10,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["course_catalog_management"],
        },
        "prerequisite_chains": {
            "owner_module": "academic_operations",
            "records": 7,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["prerequisite_management"],
        },
        "learning_outcomes_summary": {
            "owner_module": "academic_operations",
            "records": 15,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["course_learning_outcomes", "program_learning_outcomes"],
        },
        "curriculum_risks": {
            "risk_score": 12,
            "open_risks": 0,
            "indicators": [],
        },
        "curriculum_readiness": {
            "ready_for_runtime": True,
            "checklist": ["read_only_runtime", "aggregator_only_runtime"],
            "readiness_score": 94,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "CURRICULUM_RUNTIME"
    assert body["curriculum_statistics"]["program_structures_total"] == 12
    assert body["course_catalog_linkage"]["records"] == 10
    assert body["prerequisite_chains"]["records"] == 7
    assert body["learning_outcomes_summary"]["records"] == 15


@patch("app.modules.academic_operations_runtime.curriculum_runtime_router.get_curriculum_runtime")
def test_curriculum_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "CURRICULUM_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "curriculum_statistics": {
                "program_structures_total": tenant_id,
                "curriculum_versions_total": tenant_id + 1,
                "curriculum_health_score": 80,
                "course_catalog_linkage_total": tenant_id + 2,
                "prerequisite_chains_total": tenant_id + 3,
                "learning_outcomes_total": tenant_id + 4,
                "academic_plans_total": tenant_id + 5,
                "canonical_bridge_total": tenant_id + 6,
            },
            "program_structures": {
                "owner_module": "academic_operations",
                "records": tenant_id,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["curriculum_management"],
            },
            "curriculum_versions": {
                "owner_module": "academic_operations",
                "records": tenant_id + 1,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["curriculum_management"],
            },
            "curriculum_health": {"healthy": True, "consistency_score": 80, "issues": []},
            "course_catalog_linkage": {
                "owner_module": "academic_operations",
                "records": tenant_id + 2,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["course_catalog_management"],
            },
            "prerequisite_chains": {
                "owner_module": "academic_operations",
                "records": tenant_id + 3,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["prerequisite_management"],
            },
            "learning_outcomes_summary": {
                "owner_module": "academic_operations",
                "records": tenant_id + 4,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["course_learning_outcomes", "program_learning_outcomes"],
            },
            "curriculum_risks": {"risk_score": 10, "open_risks": 0, "indicators": []},
            "curriculum_readiness": {"ready_for_runtime": True, "checklist": ["read_only_runtime"], "readiness_score": 90},
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 6, "name": "Tenant-6"}
    tenant6 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 10, "name": "Tenant-10"}
    tenant10 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant6.status_code == 200
    assert tenant10.status_code == 200
    assert tenant6.json()["tenant_id"] == 6
    assert tenant10.json()["tenant_id"] == 10


@patch("app.modules.academic_operations_runtime.curriculum_runtime_router.get_curriculum_runtime")
def test_curriculum_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="727",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_curriculum_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405
