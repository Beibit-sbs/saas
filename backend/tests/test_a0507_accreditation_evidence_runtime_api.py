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
from app.modules.quality_accreditation.models import EvidenceLimitation, EvidenceReview, QualityEvidenceRegistry
from app.modules.quality_accreditation.quality_accreditation_evidence_schemas import (
    AccreditationEvidenceItem,
    AccreditationEvidenceRuntimeResponse,
)
from app.modules.quality_accreditation.quality_accreditation_evidence_service import AccreditationEvidenceRuntimeService
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/accreditation-evidence"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="708",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _build_rows(tenant_id: int):
    ts = datetime(2026, 6, 10, tzinfo=UTC)
    return {
        QualityEvidenceRegistry: [
            SimpleNamespace(
                id=tenant_id * 10 + 1,
                tenant_id=tenant_id,
                evidence_ref=f"EVID-{tenant_id}-A",
                title="Curriculum mapping evidence bundle",
                criterion_ref="CURRICULUM_ALIGNMENT",
                standard_ref=f"STD-{tenant_id}-A",
                source_family_id="academic_operations",
                source_capability_id="quality_accreditation",
                status="REVIEWED_METADATA_ONLY",
                metadata_json={"evidence_category": "CURRICULUM"},
                updated_at=ts,
            ),
            SimpleNamespace(
                id=tenant_id * 10 + 2,
                tenant_id=tenant_id,
                evidence_ref=f"EVID-{tenant_id}-B",
                title="Faculty qualifications extract",
                criterion_ref="FACULTY_QUALITY",
                standard_ref=f"STD-{tenant_id}-B",
                source_family_id="quality_accreditation",
                source_capability_id=None,
                status="MISSING",
                metadata_json={"evidence_category": "FACULTY"},
                updated_at=ts,
            ),
        ],
        EvidenceReview: [
            SimpleNamespace(
                id=tenant_id * 20 + 1,
                tenant_id=tenant_id,
                evidence_ref=f"EVID-{tenant_id}-A",
                status="ACCEPTED_METADATA_ONLY",
            )
        ],
        EvidenceLimitation: [
            SimpleNamespace(
                id=tenant_id * 30 + 1,
                tenant_id=tenant_id,
                evidence_ref=f"EVID-{tenant_id}-B",
                status="LIMITATION_RECORDED",
            )
        ],
    }


def test_accreditation_evidence_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_accreditation_evidence_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.accreditation_evidence_router.accreditation_evidence_runtime_service.get_accreditation_evidence_runtime")
def test_accreditation_evidence_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = AccreditationEvidenceRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        evidence_inventory=[
            AccreditationEvidenceItem(
                evidence_id="EVID-1-A",
                evidence_name="Curriculum mapping evidence bundle",
                evidence_category="CURRICULUM",
                accreditation_standard="STD-1-A",
                accreditation_section="CURRICULUM_ALIGNMENT",
                owner_unit="academic_operations",
                evidence_status="REVIEWED_METADATA_ONLY",
                completeness_score=96,
                last_updated=datetime(2026, 6, 10, tzinfo=UTC),
                risk_level="LOW",
            )
        ],
        evidence_categories=[],
        evidence_readiness=[],
        evidence_coverage=[],
        evidence_risk=[],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "ACCREDITATION_EVIDENCE_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["evidence_inventory"][0]["evidence_id"] == "EVID-1-A"


@patch("app.modules.quality_accreditation.quality_accreditation_evidence_service.repository.list_resources")
def test_accreditation_evidence_service_is_tenant_scoped(mock_list_resources) -> None:
    rows_by_tenant = {tenant_id: _build_rows(tenant_id) for tenant_id in (5, 12)}

    def _list_resources(_db, model, tenant_id):
        return rows_by_tenant[tenant_id][model]

    mock_list_resources.side_effect = _list_resources
    service = AccreditationEvidenceRuntimeService()
    session = MagicMock(spec=Session)

    tenant5 = service.get_accreditation_evidence_runtime(session, 5).model_dump(mode="json")
    tenant12 = service.get_accreditation_evidence_runtime(session, 12).model_dump(mode="json")

    assert tenant5["tenant_id"] == 5
    assert tenant12["tenant_id"] == 12
    assert tenant5["evidence_inventory"]
    assert tenant12["evidence_inventory"]
    assert tenant5["evidence_inventory"][0]["evidence_id"] != tenant12["evidence_inventory"][0]["evidence_id"]
    assert {item["evidence_category"] for item in tenant5["evidence_categories"]} == {"CURRICULUM", "FACULTY"}
    assert {item["risk_level"] for item in tenant5["evidence_risk"]} == {"HIGH", "LOW"}


@patch("app.modules.quality_accreditation.accreditation_evidence_router.accreditation_evidence_runtime_service.get_accreditation_evidence_runtime")
def test_accreditation_evidence_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = AccreditationEvidenceRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        evidence_inventory=[],
        evidence_categories=[],
        evidence_readiness=[],
        evidence_coverage=[],
        evidence_risk=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
