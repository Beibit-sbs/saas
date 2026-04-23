"""Phase VIII-1: Communications router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.communications.schemas import (
    CommunicationMessageCreatePayload,
    CommunicationMessageItemResponse,
    CommunicationMessageListResponse,
    CommunicationsBrainContextResponse,
)
from app.modules.communications.service import (
    create_message,
    get_communications_brain_context,
    list_messages,
)

router = APIRouter(prefix="/api/admin/communications", tags=["communications"])


@router.get("/messages", response_model=CommunicationMessageListResponse)
def list_messages_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    message_type: str | None = None,
    status: str | None = None,
) -> CommunicationMessageListResponse:
    return CommunicationMessageListResponse(
        records=list_messages(int(tenant["id"]), message_type=message_type, status=status)
    )


@router.post("/messages", response_model=CommunicationMessageItemResponse, status_code=201)
def create_message_endpoint(
    payload: CommunicationMessageCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CommunicationMessageItemResponse:
    return CommunicationMessageItemResponse(
        record=create_message(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=CommunicationsBrainContextResponse)
def brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CommunicationsBrainContextResponse:
    return CommunicationsBrainContextResponse(
        **get_communications_brain_context(int(tenant["id"]))
    )
