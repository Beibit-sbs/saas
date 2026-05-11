from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.timetable_approval_queue.schemas import (
    TimetableApprovalQueueVisibilitySchema,
    ApprovalQueueL5ReadinessSchema,
)
from app.modules.timetable_approval_queue.service import (
    get_approval_queue_visibility_summary,
    get_approval_queue_l5_readiness,
)

router = APIRouter(
    prefix="/api/admin/timetable-approval-queue",
    tags=["timetable_approval_queue"],
)


@router.get("/summary", response_model=TimetableApprovalQueueVisibilitySchema)
def timetable_approval_queue_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("timetable.approval_queue.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> TimetableApprovalQueueVisibilitySchema:
    payload = get_approval_queue_visibility_summary(int(tenant["id"]))
    return TimetableApprovalQueueVisibilitySchema(**payload)


@router.get("/l5-readiness", response_model=ApprovalQueueL5ReadinessSchema)
def timetable_approval_queue_l5_readiness(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("timetable.approval_queue.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> ApprovalQueueL5ReadinessSchema:
    payload = get_approval_queue_l5_readiness(int(tenant["id"]))
    return ApprovalQueueL5ReadinessSchema(**payload)
