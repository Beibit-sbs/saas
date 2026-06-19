"""Innovation / Commercialization extension runtime shell router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.innovation_commercialization import permissions, service
from app.modules.innovation_commercialization.schemas import (
    InnovationCommercializationShellResponse,
    InnovationOpportunityListResponse,
)
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research_science.dependencies import require_research_science_tenant


router = APIRouter(prefix="/api/admin/innovation-commercialization", tags=["innovation-commercialization"])

_Tenant = Annotated[int, Depends(require_research_science_tenant)]
_Actor = Annotated[str, Depends(get_actor)]


@router.get("/shell", response_model=InnovationCommercializationShellResponse)
def get_extension_shell(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))],
    tenant: _Tenant,
) -> InnovationCommercializationShellResponse:
    return service.get_extension_shell_service(tenant)


@router.get("/opportunities", response_model=InnovationOpportunityListResponse)
def list_opportunities(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.PIPELINE_READ))],
    tenant: _Tenant,
) -> InnovationOpportunityListResponse:
    return service.list_opportunities_service(tenant)
