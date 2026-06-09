"""Research Brain runtime shell router (A-047.6-E1 Batch 1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research_science import permissions, service
from app.modules.research_science.dependencies import get_research_science_db, require_research_science_tenant
from app.modules.research_science.schemas import (
    ResearchBrainContextResponse,
    ResearchBrainKpiSurfaceResponse,
    ResearchBrainOrchestrationResponse,
    ResearchBrainRbacValidationResponse,
    ResearchBrainShellResponse,
    ResearchBrainSignalSurfaceResponse,
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
