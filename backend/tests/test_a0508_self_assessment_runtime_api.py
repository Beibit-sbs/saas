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
from app.modules.quality_accreditation.models import (
    AccreditationStandard,
    EvidenceLimitation,
    InstitutionalAccreditationReadiness,
    ProgramAccreditationReadiness,
    QualityEvidenceRegistry,
)
from app.modules.quality_accreditation.quality_accreditation_self_assessment_schemas import (
    SelfAssessmentRuntimeResponse,
    SelfAssessmentScorecard,
    SelfAssessmentStandard,
)
from app.modules.quality_accreditation.quality_accreditation_self_assessment_service import SelfAssessmentRuntimeService
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/self-assessment"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="709",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _build_rows(tenant_id: int):
    ts = datetime(2026, 6, 10, tzinfo=UTC)
    return {
        AccreditationStandard: [
            SimpleNamespace(
                id=tenant_id * 10 + 1,
                tenant_id=tenant_id,
                standard_ref=f"STD-{tenant_id}-1",
                title="Curriculum Quality Standard",
                framework_ref="NATIONAL_QUALITY_FRAMEWORK",
                source_family_id="academic_operations",
                source_capability_id="quality_accreditation",
                updated_at=ts,
            ),
            SimpleNamespace(
                id=tenant_id * 10 + 2,
                tenant_id=tenant_id,
                standard_ref=f"STD-{tenant_id}-2",
                title="Faculty Quality Standard",
                framework_ref="NATIONAL_QUALITY_FRAMEWORK",
                source_family_id="quality_accreditation",
                source_capability_id=None,
                updated_at=ts,
            ),
        ],
        QualityEvidenceRegistry: [
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-1"),
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-1"),
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-2"),
        ],
        EvidenceLimitation: [
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-2"),
        ],
        ProgramAccreditationReadiness: [
            SimpleNamespace(tenant_id=tenant_id, completion_percent=82),
        ],
        InstitutionalAccreditationReadiness: [
            SimpleNamespace(tenant_id=tenant_id, completion_percent=78),
        ],
    }


def test_self_assessment_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_self_assessment_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.self_assessment_runtime_router.self_assessment_runtime_service.get_self_assessment_runtime")
def test_self_assessment_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = SelfAssessmentRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        standards=[
            SelfAssessmentStandard(
                standard_id="STD-1",
                standard_name="Curriculum Quality Standard",
                accreditation_framework="NATIONAL_QUALITY_FRAMEWORK",
                readiness_score=88,
                completion_percentage=86,
                evidence_coverage=80,
                gap_count=0,
                risk_level="LOW",
                owner_unit="academic_operations",
                last_updated=datetime(2026, 6, 10, tzinfo=UTC),
            )
        ],
        scorecard=SelfAssessmentScorecard(standards_total=1, ready_standards=1),
        readiness_summary=[],
        coverage_summary=[],
        risk_summary=[],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "SELF_ASSESSMENT_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["standards"][0]["standard_id"] == "STD-1"


@patch("app.modules.quality_accreditation.quality_accreditation_self_assessment_service.repository.list_resources")
def test_self_assessment_service_is_tenant_scoped(mock_list_resources) -> None:
    rows_by_tenant = {tenant_id: _build_rows(tenant_id) for tenant_id in (7, 19)}

    def _list_resources(_db, model, tenant_id):
        return rows_by_tenant[tenant_id][model]

    mock_list_resources.side_effect = _list_resources
    service = SelfAssessmentRuntimeService()
    session = MagicMock(spec=Session)

    tenant7 = service.get_self_assessment_runtime(session, 7).model_dump(mode="json")
    tenant19 = service.get_self_assessment_runtime(session, 19).model_dump(mode="json")

    assert tenant7["tenant_id"] == 7
    assert tenant19["tenant_id"] == 19
    assert tenant7["standards"]
    assert tenant19["standards"]
    assert tenant7["standards"][0]["standard_id"] != tenant19["standards"][0]["standard_id"]


@patch("app.modules.quality_accreditation.self_assessment_runtime_router.self_assessment_runtime_service.get_self_assessment_runtime")
def test_self_assessment_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = SelfAssessmentRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        standards=[],
        scorecard=SelfAssessmentScorecard(),
        readiness_summary=[],
        coverage_summary=[],
        risk_summary=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
