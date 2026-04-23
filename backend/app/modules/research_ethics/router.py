"""Phase VII-VII1: Research ethics router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research_ethics.schemas import (
    EthicsReviewCreatePayload,
    EthicsReviewItemResponse,
    EthicsReviewListResponse,
    ResearchEthicsBrainContextResponse,
)
from app.modules.research_ethics.service import (
    create_ethics_review,
    get_research_ethics_brain_context,
    list_ethics_reviews,
)

router = APIRouter(prefix="/api/admin/research-ethics", tags=["research-ethics"])


@router.get("/reviews", response_model=EthicsReviewListResponse)
def list_ethics_reviews_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    risk_level: str | None = None,
) -> EthicsReviewListResponse:
    return EthicsReviewListResponse(
        records=list_ethics_reviews(int(tenant["id"]), status=status, risk_level=risk_level)
    )


@router.post("/reviews", response_model=EthicsReviewItemResponse, status_code=201)
def create_ethics_review_endpoint(
    payload: EthicsReviewCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EthicsReviewItemResponse:
    return EthicsReviewItemResponse(
        record=create_ethics_review(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=ResearchEthicsBrainContextResponse)
def get_research_ethics_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchEthicsBrainContextResponse:
    return ResearchEthicsBrainContextResponse.model_validate(
        get_research_ethics_brain_context(int(tenant["id"]))
    )
