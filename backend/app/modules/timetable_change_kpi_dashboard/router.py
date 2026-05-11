from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.timetable_change_kpi_dashboard.schemas import (
    TimetableChangeKpiDashboardVisibilitySchema,
    KpiDashboardL5ReadinessSchema,
)
from app.modules.timetable_change_kpi_dashboard.service import (
    get_kpi_dashboard_visibility_summary,
    get_kpi_dashboard_l5_readiness,
)

router = APIRouter(
    prefix="/api/admin/timetable-change-kpi-dashboard",
    tags=["timetable_change_kpi_dashboard"],
)


@router.get("/summary", response_model=TimetableChangeKpiDashboardVisibilitySchema)
def timetable_change_kpi_dashboard_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("timetable.change_kpi.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> TimetableChangeKpiDashboardVisibilitySchema:
    payload = get_kpi_dashboard_visibility_summary(int(tenant["id"]))
    return TimetableChangeKpiDashboardVisibilitySchema(**payload)


@router.get("/l5-readiness", response_model=KpiDashboardL5ReadinessSchema)
def timetable_change_kpi_dashboard_l5_readiness(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("timetable.change_kpi.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> KpiDashboardL5ReadinessSchema:
    payload = get_kpi_dashboard_l5_readiness(int(tenant["id"]))
    return KpiDashboardL5ReadinessSchema(**payload)
