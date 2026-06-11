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
from app.modules.quality_accreditation.quality_accreditation_readiness_monitoring_schemas import (
    ReadinessDomainDTO,
    ReadinessIndicatorDTO,
    ReadinessMonitoringRuntimeResponseDTO,
    ReadinessRemediationDTO,
    ReadinessRiskDTO,
    ReadinessSummaryDTO,
)
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/readiness-monitoring-runtime"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="713",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_readiness_monitoring_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_readiness_monitoring_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.readiness_monitoring_runtime_router.readiness_monitoring_runtime_service.get_readiness_monitoring_runtime")
def test_readiness_monitoring_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = ReadinessMonitoringRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        readiness_summary=ReadinessSummaryDTO(
            monitored_domains_total=2,
            domains_on_track=1,
            domains_at_risk=1,
            average_readiness_score=79,
        ),
        readiness_domains=[
            ReadinessDomainDTO(
                domain_id="RD-1",
                domain_name="INTERNAL_AUDIT_READINESS",
                readiness_score=82,
                threshold=90,
                status="WATCH",
                trend="UP",
            )
        ],
        readiness_risks=[
            ReadinessRiskDTO(
                risk_id="RR-1",
                risk_title="Delayed closure",
                risk_level="HIGH",
                impacted_domain="CLOSURE_TRACKING_READINESS",
                mitigation_status="IN_PROGRESS",
            )
        ],
        remediation_tracking=[
            ReadinessRemediationDTO(
                remediation_id="RM-1",
                remediation_title="Close unresolved checklist items",
                owner_unit="quality_accreditation",
                completion_percentage=65,
                status="IN_PROGRESS",
                due_date=datetime(2026, 8, 10, tzinfo=UTC),
            )
        ],
        readiness_indicators=[
            ReadinessIndicatorDTO(
                indicator_name="READINESS_SCORE_GLOBAL",
                indicator_value=79,
                threshold=85,
                status="WATCH",
            )
        ],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "READINESS_MONITORING_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["readiness_summary"]
    assert body["readiness_domains"]
    assert body["readiness_risks"]
    assert body["remediation_tracking"]
    assert body["readiness_indicators"]


def test_readiness_monitoring_runtime_tenant_required() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": None, "name": "Tenant-None"}
    response = client.get(BASE, headers=_headers())
    assert response.status_code in (400, 403, 422)


@patch("app.modules.quality_accreditation.readiness_monitoring_runtime_router.readiness_monitoring_runtime_service.get_readiness_monitoring_runtime")
def test_readiness_monitoring_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = ReadinessMonitoringRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        readiness_summary=ReadinessSummaryDTO(
            monitored_domains_total=0,
            domains_on_track=0,
            domains_at_risk=0,
            average_readiness_score=0,
        ),
        readiness_domains=[],
        readiness_risks=[],
        remediation_tracking=[],
        readiness_indicators=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
