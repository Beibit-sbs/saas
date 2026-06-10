from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db
from app.modules.quality_accreditation.models import AccreditationStandard, InstitutionalAccreditationReadiness, ProgramAccreditationReadiness, QualityRiskRegister
from app.modules.quality_accreditation.quality_accreditation_registry_schemas import (
    AccreditationRegistryItem,
    AccreditationRegistryRuntimeResponse,
)
from app.modules.quality_accreditation.quality_accreditation_registry_service import AccreditationRegistryRuntimeService
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/accreditation-registry"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="707",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _build_rows(tenant_id: int):
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    return {
        AccreditationStandard: [
            SimpleNamespace(
                id=tenant_id * 10 + 1,
                tenant_id=tenant_id,
                standard_ref=f"STD-{tenant_id}-A",
                title="Institutional Quality Accreditation",
                framework_ref="quality_accreditation",
                status="ACTIVE_METADATA_ONLY",
                created_at=issued_at,
                updated_at=issued_at,
                source_capability_id=None,
                source_family_id="quality_accreditation",
            ),
            SimpleNamespace(
                id=tenant_id * 10 + 2,
                tenant_id=tenant_id,
                standard_ref=f"STD-{tenant_id}-B",
                title="Program Accreditation Registry",
                framework_ref="academic_operations",
                status="REVIEW_REQUIRED",
                created_at=issued_at,
                updated_at=issued_at,
                source_capability_id=None,
                source_family_id="academic_operations",
            ),
        ],
        ProgramAccreditationReadiness: [
            SimpleNamespace(
                id=tenant_id * 20 + 1,
                tenant_id=tenant_id,
                readiness_ref=f"READY-{tenant_id}-A",
                framework_ref="quality_accreditation",
                program_ref=None,
                status="READY_FOR_INTERNAL_REVIEW",
                completion_percent=92,
                created_at=issued_at,
                updated_at=issued_at,
            ),
            SimpleNamespace(
                id=tenant_id * 20 + 2,
                tenant_id=tenant_id,
                readiness_ref=f"READY-{tenant_id}-B",
                framework_ref="academic_operations",
                program_ref=None,
                status="EVIDENCE_INCOMPLETE",
                completion_percent=48,
                created_at=issued_at,
                updated_at=issued_at,
            ),
        ],
        InstitutionalAccreditationReadiness: [
            SimpleNamespace(
                id=tenant_id * 30 + 1,
                tenant_id=tenant_id,
                readiness_ref=f"INST-{tenant_id}-A",
                framework_ref="quality_accreditation",
                status="IN_PROGRESS",
                completion_percent=74,
                created_at=issued_at,
                updated_at=issued_at,
            )
        ],
        QualityRiskRegister: [
            SimpleNamespace(
                id=tenant_id * 40 + 1,
                tenant_id=tenant_id,
                risk_ref=f"RISK-{tenant_id}-A",
                standard_ref=f"STD-{tenant_id}-B",
                program_ref=None,
                risk_band="HIGH",
                status="ACTIVE_METADATA_ONLY",
                created_at=issued_at,
                updated_at=issued_at,
            )
        ],
    }


def test_accreditation_registry_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_accreditation_registry_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.accreditation_registry_router.accreditation_registry_runtime_service.get_accreditation_registry")
def test_accreditation_registry_response_contract(mock_service) -> None:
    mock_service.return_value = AccreditationRegistryRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        active_accreditations=[
            AccreditationRegistryItem(
                accreditation_id="ACC-1",
                accreditation_name="Institutional Quality Accreditation",
                accreditation_type="INSTITUTIONAL",
                accreditation_scope="quality_accreditation",
                provider="quality_accreditation",
                status="ACTIVE_METADATA_ONLY",
                issued_date=datetime(2026, 1, 1, tzinfo=UTC),
                expiry_date=datetime(2026, 12, 30, tzinfo=UTC),
                readiness_score=92,
                risk_level="LOW",
            )
        ],
        expiring_accreditations=[],
        accreditation_provider=[],
        accreditation_status=[],
        accreditation_readiness=[],
        accreditation_risk=[],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["runtime_registry"] == "ACCREDITATION_REGISTRY_RUNTIME"
    assert body["active_accreditations"][0]["accreditation_id"] == "ACC-1"
    assert body["active_accreditations"][0]["provider"] == "quality_accreditation"


@patch("app.modules.quality_accreditation.quality_accreditation_registry_service.repository.list_resources")
def test_accreditation_registry_service_is_tenant_scoped(mock_list_resources) -> None:
    rows_by_tenant = {tenant_id: _build_rows(tenant_id) for tenant_id in (4, 11)}

    def _list_resources(_db, model, tenant_id):
        return rows_by_tenant[tenant_id][model]

    mock_list_resources.side_effect = _list_resources
    service = AccreditationRegistryRuntimeService()
    session = MagicMock(spec=Session)

    tenant4 = service.get_accreditation_registry(session, 4).model_dump(mode="json")
    tenant11 = service.get_accreditation_registry(session, 11).model_dump(mode="json")

    assert tenant4["tenant_id"] == 4
    assert tenant11["tenant_id"] == 11
    assert tenant4["active_accreditations"][0]["accreditation_id"] != tenant11["active_accreditations"][0]["accreditation_id"]
    assert tenant4["expiring_accreditations"]
    assert tenant11["expiring_accreditations"]
    assert {item["provider"] for item in tenant4["accreditation_provider"]} == {"academic_operations", "quality_accreditation"}
    assert {item["status"] for item in tenant4["accreditation_status"]} == {"ACTIVE_METADATA_ONLY", "REVIEW_REQUIRED"}
    assert {item["risk_level"] for item in tenant4["accreditation_risk"]} == {"HIGH", "LOW"}


@patch("app.modules.quality_accreditation.accreditation_registry_router.accreditation_registry_runtime_service.get_accreditation_registry")
def test_accreditation_registry_is_read_only(mock_service) -> None:
    mock_service.return_value = AccreditationRegistryRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        active_accreditations=[],
        expiring_accreditations=[],
        accreditation_provider=[],
        accreditation_status=[],
        accreditation_readiness=[],
        accreditation_risk=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
