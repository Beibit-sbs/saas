from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.notification_center.schemas import NotificationCenterVisibilitySchema
from app.modules.notification_center.service import get_notification_visibility_summary
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(
    prefix="/api/admin/notification-center",
    tags=["notification_center"],
)


@router.get("/summary", response_model=NotificationCenterVisibilitySchema)
def notification_center_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("notifications.read"))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> NotificationCenterVisibilitySchema:
    payload = get_notification_visibility_summary(int(tenant["id"]))
    return NotificationCenterVisibilitySchema(**payload)
