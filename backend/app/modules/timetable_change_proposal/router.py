from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.timetable_change_proposal.schemas import TimetableChangeProposalVisibilitySchema
from app.modules.timetable_change_proposal.service import (
    get_timetable_proposal_visibility_summary,
)

router = APIRouter(
    prefix="/api/admin/timetable-change-proposal",
    tags=["timetable_change_proposal"],
)


@router.get("/summary", response_model=TimetableChangeProposalVisibilitySchema)
def timetable_change_proposal_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("timetable.change_proposal.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> TimetableChangeProposalVisibilitySchema:
    payload = get_timetable_proposal_visibility_summary(int(tenant["id"]))
    return TimetableChangeProposalVisibilitySchema(**payload)
