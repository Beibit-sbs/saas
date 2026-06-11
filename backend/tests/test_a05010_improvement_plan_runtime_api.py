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
from app.modules.quality_accreditation.quality_accreditation_improvement_plan_schemas import (
    ImprovementForecastDTO,
    ImprovementInitiativeDTO,
    ImprovementKpiTargetDTO,
    ImprovementMilestoneDTO,
    ImprovementPlanRuntimeDTO,
    ImprovementPlanRuntimeResponseDTO,
    ImprovementRoadmapDTO,
)
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/improvement-plan-runtime"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="711",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_improvement_plan_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_improvement_plan_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.improvement_plan_runtime_router.improvement_plan_runtime_service.get_improvement_plan_runtime")
def test_improvement_plan_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = ImprovementPlanRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        improvement_plans=[
            ImprovementPlanRuntimeDTO(
                plan_id="PLAN-1",
                plan_title="Quality Accreditation Improvement Plan",
                accreditation_standard="INSTITUTIONAL_QUALITY_STANDARD_SET",
                owner_unit="quality_accreditation",
                progress_tracking_status="TRACKED",
                completion_percentage=55,
                initiatives=[
                    ImprovementInitiativeDTO(
                        initiative_id="INIT-1",
                        initiative_title="Close curriculum evidence gaps",
                        strategic_theme="ACADEMIC_QUALITY",
                        owner_unit="academic_operations",
                        status="IN_PROGRESS",
                        completion_percentage=65,
                        milestones=[
                            ImprovementMilestoneDTO(
                                milestone_id="MS-1",
                                milestone_title="Milestone one",
                                due_date=datetime(2026, 7, 1, tzinfo=UTC),
                                completion_percentage=70,
                                status="IN_PROGRESS",
                            )
                        ],
                        kpi_targets=[
                            ImprovementKpiTargetDTO(
                                kpi_target_id="KPI-1",
                                kpi_name="Evidence completeness ratio",
                                baseline_value=60,
                                target_value=90,
                                current_value=75,
                                unit="percent",
                            )
                        ],
                    )
                ],
                roadmaps=[
                    ImprovementRoadmapDTO(
                        roadmap_id="ROADMAP-1",
                        roadmap_title="Roadmap",
                        accreditation_cycle="2026-2027",
                        phase="EXECUTION",
                        initiatives_total=1,
                        initiatives_completed=0,
                        completion_percentage=50,
                    )
                ],
                forecasts=[
                    ImprovementForecastDTO(
                        forecast_id="FC-1",
                        forecast_type="COMPLETION_FORECAST",
                        confidence_level="MEDIUM",
                        projected_completion_date=datetime(2026, 12, 1, tzinfo=UTC),
                        readiness_forecast_score=80,
                        risk_level="MEDIUM",
                    )
                ],
                last_updated=datetime(2026, 6, 11, tzinfo=UTC),
            )
        ],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "IMPROVEMENT_PLAN_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["improvement_plans"][0]["roadmaps"]
    assert body["improvement_plans"][0]["initiatives"][0]["milestones"]
    assert body["improvement_plans"][0]["initiatives"][0]["kpi_targets"]
    assert body["improvement_plans"][0]["forecasts"]


def test_improvement_plan_runtime_tenant_required() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": None, "name": "Tenant-None"}
    response = client.get(BASE, headers=_headers())
    assert response.status_code in (400, 403, 422)


@patch("app.modules.quality_accreditation.improvement_plan_runtime_router.improvement_plan_runtime_service.get_improvement_plan_runtime")
def test_improvement_plan_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = ImprovementPlanRuntimeResponseDTO(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        improvement_plans=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
