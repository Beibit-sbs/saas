from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db
from app.modules.quality_accreditation.quality_accreditation_audit_findings_schemas import (
    AuditFindingDTO,
    AuditFindingsRuntimeResponseDTO,
    AuditObservationDTO,
    AuditReadinessDTO,
    AuditRecommendationDTO,
    AuditRemediationStatusDTO,
    AuditRiskAnalysisDTO,
    NonConformityDTO,
)
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/audit-findings-runtime"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="712",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_audit_findings_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_audit_findings_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.audit_findings_runtime_router.audit_findings_runtime_service.get_audit_findings_runtime")
def test_audit_findings_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = AuditFindingsRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        findings=[
            AuditFindingDTO(
                finding_id="AF-1",
                finding_source="INTERNAL_AUDIT",
                finding_type="INTERNAL_AUDIT_FINDING",
                finding_title="Evidence traceability gap",
                severity="HIGH",
                impacted_standard="STD-ACADEMIC-01",
                remediation_status="IN_PROGRESS",
                closure_tracking_status="TRACKED",
                opened_at=datetime(2026, 1, 10, tzinfo=UTC),
                due_date=datetime(2026, 7, 10, tzinfo=UTC),
            )
        ],
        non_conformities=[
            NonConformityDTO(
                non_conformity_id="NC-1",
                category="DOCUMENT_CONTROL",
                severity="HIGH",
                affected_area="PROGRAM_REVIEW",
                status="OPEN",
            )
        ],
        observations=[
            AuditObservationDTO(
                observation_id="OBS-1",
                observation_type="PROCESS_OBSERVATION",
                summary="Review cadence inconsistency",
                impact_level="MEDIUM",
            )
        ],
        recommendations=[
            AuditRecommendationDTO(
                recommendation_id="REC-1",
                recommendation_title="Standardize evidence taxonomy",
                priority="HIGH",
                owner_unit="quality_accreditation",
                target_date=datetime(2026, 8, 1, tzinfo=UTC),
                status="IN_PROGRESS",
            )
        ],
        risk_severity_analysis=[
            AuditRiskAnalysisDTO(
                risk_band="HIGH",
                findings_count=1,
                non_conformities_count=1,
                recommendations_open=1,
            )
        ],
        remediation_status=[
            AuditRemediationStatusDTO(
                remediation_state="IN_PROGRESS",
                findings_count=1,
                average_completion_percentage=60,
            )
        ],
        audit_readiness_indicators=[
            AuditReadinessDTO(
                indicator_name="AUDIT_EVIDENCE_COMPLETENESS",
                indicator_value=82,
                threshold=90,
                status="WATCH",
            )
        ],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "AUDIT_FINDINGS_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["findings"]
    assert body["non_conformities"]
    assert body["recommendations"]
    assert body["remediation_status"]
    assert body["audit_readiness_indicators"]


def test_audit_findings_runtime_tenant_required() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": None, "name": "Tenant-None"}
    response = client.get(BASE, headers=_headers())
    assert response.status_code in (400, 403, 422)


@patch("app.modules.quality_accreditation.audit_findings_runtime_router.audit_findings_runtime_service.get_audit_findings_runtime")
def test_audit_findings_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = AuditFindingsRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        findings=[],
        non_conformities=[],
        observations=[],
        recommendations=[],
        risk_severity_analysis=[],
        remediation_status=[],
        audit_readiness_indicators=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
