"""Research Brain runtime shell router (A-047.6-E1 Batch 1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research_science import permissions, service
from app.modules.research_science.dependencies import get_research_science_db, require_research_science_tenant
from app.modules.research_science.schemas import (
    CitationAnalyticsSummary,
    PublicationImpactProfile,
    ResearcherActivityProfileResponse,
    ResearcherDashboardSummaryResponse,
    ResearcherListResponse,
    ResearcherRankingResponse,
    ResearcherRiskProfileResponse,
    ResearchRiskProfile,
    ResearchRiskSignal,
    ResearchRiskSummary,
    ResearchRiskTrend,
    ResearcherScientometricProfile,
    Researcher,
    ResearchBrainContextResponse,
    ResearchBrainKpiSurfaceResponse,
    ResearchBrainOrchestrationResponse,
    ResearchBrainRbacValidationResponse,
    ResearchBrainShellResponse,
    ResearchBrainSignalSurfaceResponse,
    ScientometricTrend,
    ScientometricsSummaryResponse,
)


router = APIRouter(prefix="/api/admin/research-brain", tags=["research-brain"])

_Tenant = Annotated[int, Depends(require_research_science_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_research_science_db)]


@router.get("/shell", response_model=ResearchBrainShellResponse)
def get_runtime_shell(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))],
    tenant: _Tenant,
) -> ResearchBrainShellResponse:
    return service.get_research_brain_shell_service(tenant)


@router.get("/orchestration", response_model=ResearchBrainOrchestrationResponse)
def get_orchestration(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchBrainOrchestrationResponse:
    return service.get_research_brain_orchestration_service(db, tenant)


@router.get("/context", response_model=ResearchBrainContextResponse)
def get_context(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchBrainContextResponse:
    return service.get_research_brain_context_service(db, tenant)


@router.get("/kpis", response_model=ResearchBrainKpiSurfaceResponse)
def get_kpis(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchBrainKpiSurfaceResponse:
    return service.get_research_brain_kpi_surface_service(db, tenant)


@router.get("/signals", response_model=ResearchBrainSignalSurfaceResponse)
def get_signals(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchBrainSignalSurfaceResponse:
    return service.get_research_brain_signal_surface_service(db, tenant)


@router.get("/rbac-validation", response_model=ResearchBrainRbacValidationResponse)
def get_rbac_validation(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))],
    tenant: _Tenant,
) -> ResearchBrainRbacValidationResponse:
    return service.get_research_brain_rbac_validation_service(tenant)


@router.get("/researchers", response_model=ResearcherListResponse)
def list_researchers(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearcherListResponse:
    return service.list_researchers_service(db, tenant)


@router.get("/researchers/summary", response_model=ResearcherDashboardSummaryResponse)
def get_researcher_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearcherDashboardSummaryResponse:
    return service.get_researcher_dashboard_summary_service(db, tenant)


@router.get("/researchers/{researcher_id}", response_model=Researcher)
def get_researcher(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> Researcher:
    return service.get_researcher_service(db, tenant, researcher_id)


@router.get("/researchers/{researcher_id}/activity", response_model=ResearcherActivityProfileResponse)
def get_researcher_activity(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> ResearcherActivityProfileResponse:
    return service.get_researcher_activity_profile_service(db, tenant, researcher_id)


@router.get("/researchers/{researcher_id}/risk", response_model=ResearcherRiskProfileResponse)
def get_researcher_risk(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> ResearcherRiskProfileResponse:
    return service.get_researcher_risk_profile_service(db, tenant, researcher_id)


@router.get("/scientometrics/dashboard", response_model=ScientometricsSummaryResponse)
def get_scientometrics_dashboard(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ScientometricsSummaryResponse:
    return service.get_scientometrics_dashboard_service(db, tenant)


@router.get("/scientometrics/ranking", response_model=ResearcherRankingResponse)
def get_scientometric_ranking(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearcherRankingResponse:
    return service.get_scientometric_researcher_ranking_service(db, tenant)


@router.get("/scientometrics/{researcher_id}", response_model=ResearcherScientometricProfile)
def get_researcher_scientometrics(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> ResearcherScientometricProfile:
    return service.get_researcher_scientometric_profile_service(db, tenant, researcher_id)


@router.get("/scientometrics/{researcher_id}/citations", response_model=CitationAnalyticsSummary)
def get_researcher_citations(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> CitationAnalyticsSummary:
    return service.get_researcher_citation_summary_service(db, tenant, researcher_id)


@router.get("/scientometrics/{researcher_id}/impact", response_model=PublicationImpactProfile)
def get_researcher_impact(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> PublicationImpactProfile:
    return service.get_researcher_impact_analysis_service(db, tenant, researcher_id)


@router.get("/scientometrics/{researcher_id}/publication-impact", response_model=PublicationImpactProfile)
def get_researcher_publication_impact(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> PublicationImpactProfile:
    return service.get_researcher_publication_impact_service(db, tenant, researcher_id)


@router.get("/scientometrics/{researcher_id}/trends", response_model=list[ScientometricTrend])
def get_researcher_scientometric_trends(
    researcher_id: str = Path(..., min_length=1),
    actor: _Actor = None,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))] = None,
    tenant: _Tenant = None,
    db: _DB = None,
) -> list[ScientometricTrend]:
    return service.get_researcher_scientometric_trends_service(db, tenant, researcher_id)


@router.get("/risk/dashboard", response_model=ResearchRiskProfile)
def get_research_risk_dashboard(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchRiskProfile:
    return service.get_research_risk_profile_service(db, tenant)


@router.get("/risk/profile", response_model=ResearchRiskProfile)
def get_research_risk_profile(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchRiskProfile:
    return service.get_research_risk_profile_service(db, tenant)


@router.get("/risk/summary", response_model=ResearchRiskSummary)
def get_research_risk_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ResearchRiskSummary:
    return service.get_research_risk_summary_service(db, tenant)


@router.get("/risk/signals", response_model=list[ResearchRiskSignal])
def get_research_risk_signals(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> list[ResearchRiskSignal]:
    return service.get_research_risk_signals_service(db, tenant)


@router.get("/risk/trends", response_model=list[ResearchRiskTrend])
def get_research_risk_trends(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> list[ResearchRiskTrend]:
    return service.get_research_risk_trends_service(db, tenant)


@router.get("/risk/recommendations", response_model=list[str])
def get_research_risk_recommendations(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> list[str]:
    return service.get_research_risk_recommendations_service(db, tenant)
