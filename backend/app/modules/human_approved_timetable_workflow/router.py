from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.human_approved_timetable_workflow.schemas import (
    HumanApprovedTimetableWorkflowVisibilitySchema,
)
from app.modules.human_approved_timetable_workflow.service import (
    get_human_workflow_visibility_summary,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(
    prefix="/api/admin/human-approved-timetable-workflow",
    tags=["human_approved_timetable_workflow"],
)


@router.get("/summary", response_model=HumanApprovedTimetableWorkflowVisibilitySchema)
def human_approved_timetable_workflow_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("timetable.workflow.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> HumanApprovedTimetableWorkflowVisibilitySchema:
    payload = get_human_workflow_visibility_summary(int(tenant["id"]))
    return HumanApprovedTimetableWorkflowVisibilitySchema(**payload)
