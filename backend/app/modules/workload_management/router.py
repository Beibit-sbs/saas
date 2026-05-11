from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.workload_management.schemas import WorkloadManagementVisibilitySchema
from app.modules.workload_management.service import get_workload_visibility_summary

router = APIRouter(
    prefix="/api/admin/workload-management",
    tags=["workload_management"],
)


@router.get("/summary", response_model=WorkloadManagementVisibilitySchema)
def workload_management_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("workload.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> WorkloadManagementVisibilitySchema:
    payload = get_workload_visibility_summary(int(tenant["id"]))
    return WorkloadManagementVisibilitySchema(**payload)
