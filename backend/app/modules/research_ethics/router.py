"""Phase VII-VII1: Research ethics router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research_ethics.schemas import (
    EthicsReviewCreatePayload,
    EthicsReviewItemResponse,
    EthicsReviewListResponse,
    ResearchEthicsBrainContextResponse,
)
import app.modules.research_ethics.service as _svc

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
        records=_svc.list_ethics_reviews(int(tenant["id"]), status=status, risk_level=risk_level)
    )


@router.post("/reviews", response_model=EthicsReviewItemResponse, status_code=201)
def create_ethics_review_endpoint(
    payload: EthicsReviewCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EthicsReviewItemResponse:
    try:
        return EthicsReviewItemResponse(
            record=_svc.create_ethics_review(payload.model_dump(), int(tenant["id"]))
        )
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/brain-context", response_model=ResearchEthicsBrainContextResponse)
def get_research_ethics_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchEthicsBrainContextResponse:
    return ResearchEthicsBrainContextResponse.model_validate(
        _svc.get_research_ethics_brain_context(int(tenant["id"]))
    )
