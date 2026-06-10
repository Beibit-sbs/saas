from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/runtime-shell"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="605",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_runtime_shell_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.quality_accreditation.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_surface_contract(mock_runtime_shell) -> None:
    mock_runtime_shell.return_value = {
        "tenant_id": 1,
        "owner_module": "quality_accreditation",
        "runtime_shell": "QUALITY_ACCREDITATION_RUNTIME_SHELL",
        "runtime_mode": "READ_ONLY_AGGREGATOR",
        "generated_at": "2026-06-10T00:00:00Z",
        "read_only": True,
        "aggregator_only": True,
        "overview": {
            "owner_module": "quality_accreditation",
            "records": 4,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["quality_accreditation"],
        },
        "readiness": {
            "owner_module": "quality_accreditation",
            "records": 7,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["quality_accreditation", "academic_operations"],
        },
        "evidence": {
            "owner_module": "quality_accreditation",
            "records": 9,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["quality_accreditation"],
        },
        "risk": {
            "owner_module": "brain_core",
            "records": 5,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["brain_core", "quality_accreditation"],
        },
        "dashboard": {
            "owner_module": "quality_accreditation",
            "records": 12,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["quality_accreditation", "analytics", "reporting_runtime"],
        },
        "safety": {
            "read_only": True,
            "aggregator_only": True,
            "human_review_required": True,
            "provider_integration_enabled": False,
            "official_accreditation_approval_enabled": False,
            "official_ministry_submission_enabled": False,
            "official_ranking_claim_enabled": False,
            "hidden_score_present": False,
            "limitations": ["metadata_only_foundation"],
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["owner_module"] == "quality_accreditation"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["safety"]["human_review_required"] is True
    assert body["safety"]["provider_integration_enabled"] is False


@patch("app.modules.quality_accreditation.runtime_shell_router.get_runtime_shell")
def test_runtime_shell_preserves_tenant_isolation(mock_runtime_shell) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "owner_module": "quality_accreditation",
            "runtime_shell": "QUALITY_ACCREDITATION_RUNTIME_SHELL",
            "runtime_mode": "READ_ONLY_AGGREGATOR",
            "generated_at": "2026-06-10T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
            "overview": {"owner_module": "quality_accreditation", "records": tenant_id, "read_only": True, "aggregator_only": True, "source_modules": ["quality_accreditation"]},
            "readiness": {"owner_module": "quality_accreditation", "records": tenant_id + 1, "read_only": True, "aggregator_only": True, "source_modules": ["quality_accreditation"]},
            "evidence": {"owner_module": "quality_accreditation", "records": tenant_id + 2, "read_only": True, "aggregator_only": True, "source_modules": ["quality_accreditation"]},
            "risk": {"owner_module": "brain_core", "records": tenant_id + 3, "read_only": True, "aggregator_only": True, "source_modules": ["brain_core"]},
            "dashboard": {"owner_module": "quality_accreditation", "records": tenant_id + 4, "read_only": True, "aggregator_only": True, "source_modules": ["quality_accreditation"]},
            "safety": {
                "read_only": True,
                "aggregator_only": True,
                "human_review_required": True,
                "provider_integration_enabled": False,
                "official_accreditation_approval_enabled": False,
                "official_ministry_submission_enabled": False,
                "official_ranking_claim_enabled": False,
                "hidden_score_present": False,
                "limitations": ["metadata_only_foundation"],
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
