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
from app.modules.quality_accreditation.quality_accreditation_dashboard_schemas import (
    DashboardComplianceIndicatorDTO,
    DashboardKpiRollupDTO,
    DashboardRiskIndicatorDTO,
    DashboardRuntimeResponseDTO,
    DashboardSummaryCardDTO,
)
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/dashboard-runtime"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="714",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_dashboard_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.dashboard_runtime_router.dashboard_runtime_service.get_dashboard_runtime")
def test_dashboard_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = DashboardRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        accreditation_summary=[DashboardSummaryCardDTO(metric_key="active_cycles", label="Active cycles", value=3, status="TRACKED")],
        evidence_coverage_summary=[DashboardSummaryCardDTO(metric_key="coverage_percent", label="Coverage", value=82, status="WATCH")],
        self_assessment_status=[DashboardSummaryCardDTO(metric_key="completed_sections", label="Completed", value=41, status="TRACKED")],
        corrective_action_status=[DashboardSummaryCardDTO(metric_key="open_actions", label="Open actions", value=14, status="WATCH")],
        improvement_plan_status=[DashboardSummaryCardDTO(metric_key="on_track_initiatives", label="On track", value=6, status="TRACKED")],
        readiness_monitoring_summary=[DashboardSummaryCardDTO(metric_key="avg_readiness_score", label="Readiness", value=78, status="WATCH")],
        audit_findings_summary=[DashboardSummaryCardDTO(metric_key="open_findings", label="Open findings", value=9, status="WATCH")],
        executive_kpi_rollup=[DashboardKpiRollupDTO(kpi_group="ACCREDITATION_READINESS", score=79, threshold=85, trend="UP")],
        compliance_indicators=[
            DashboardComplianceIndicatorDTO(
                indicator_name="INTERNAL_CONTROL_COMPLIANCE",
                indicator_value=84,
                threshold=90,
                status="WATCH",
            )
        ],
        accreditation_risk_indicators=[
            DashboardRiskIndicatorDTO(
                risk_name="Delayed closure",
                risk_level="HIGH",
                impacted_area="AUDIT_FINDINGS",
                mitigation_status="IN_PROGRESS",
            )
        ],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "DASHBOARD_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["accreditation_summary"]
    assert body["evidence_coverage_summary"]
    assert body["self_assessment_status"]
    assert body["corrective_action_status"]
    assert body["improvement_plan_status"]
    assert body["readiness_monitoring_summary"]
    assert body["audit_findings_summary"]
    assert body["executive_kpi_rollup"]
    assert body["compliance_indicators"]
    assert body["accreditation_risk_indicators"]


def test_dashboard_runtime_tenant_required() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": None, "name": "Tenant-None"}
    response = client.get(BASE, headers=_headers())
    assert response.status_code in (400, 403, 422)


@patch("app.modules.quality_accreditation.dashboard_runtime_router.dashboard_runtime_service.get_dashboard_runtime")
def test_dashboard_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = DashboardRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        accreditation_summary=[],
        evidence_coverage_summary=[],
        self_assessment_status=[],
        corrective_action_status=[],
        improvement_plan_status=[],
        readiness_monitoring_summary=[],
        audit_findings_summary=[],
        executive_kpi_rollup=[],
        compliance_indicators=[],
        accreditation_risk_indicators=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
