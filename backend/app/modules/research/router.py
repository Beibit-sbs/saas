from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research.schemas import (
    ResearchExperimentCreateSchema,
    ResearchExperimentItemResponseSchema,
    ResearchExperimentListResponseSchema,
    ResearchExperimentStatusUpdateSchema,
    ResearchGrantCreateSchema,
    ResearchGrantItemResponseSchema,
    ResearchGrantListResponseSchema,
    ResearchGrantStatus,
    ResearchGrantStatusUpdateSchema,
    ResearchHealthResponseSchema,
    ResearchIpAssetCreateSchema,
    ResearchIpAssetItemResponseSchema,
    ResearchIpAssetListResponseSchema,
    ResearchLabCreateSchema,
    ResearchLabItemResponseSchema,
    ResearchLabListResponseSchema,
    ResearchLabStatusUpdateSchema,
    ResearchPublicationCreateSchema,
    ResearchPublicationItemResponseSchema,
    ResearchPublicationListResponseSchema,
    ResearchPublicationStatus,
    ResearchPublicationStatusUpdateSchema,
)
import app.modules.research.service as _svc


router = APIRouter(prefix="/api/admin/research", tags=["research"])


@router.get("/health", response_model=ResearchHealthResponseSchema)
def get_research_health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchHealthResponseSchema:
    item = _svc.get_research_health_snapshot(int(tenant["id"]))
    return ResearchHealthResponseSchema(item=item)


@router.get("/grants", response_model=ResearchGrantListResponseSchema)
def list_research_grants_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: ResearchGrantStatus | None = None,
) -> ResearchGrantListResponseSchema:
    items = _svc.list_research_grants(int(tenant["id"]), status=status)
    return ResearchGrantListResponseSchema(items=items)


@router.post("/grants", response_model=ResearchGrantItemResponseSchema)
def create_research_grant_endpoint(
    payload: ResearchGrantCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchGrantItemResponseSchema:
    try:
        item = _svc.create_research_grant(int(tenant["id"]), payload, actor)
        return ResearchGrantItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/grants/{grant_id}", response_model=ResearchGrantItemResponseSchema)
def get_research_grant_endpoint(
    grant_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchGrantItemResponseSchema:
    try:
        item = _svc.get_research_grant(int(tenant["id"]), grant_id)
        return ResearchGrantItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/grants/{grant_id}/status", response_model=ResearchGrantItemResponseSchema)
def update_research_grant_status_endpoint(
    grant_id: int,
    payload: ResearchGrantStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchGrantItemResponseSchema:
    try:
        item = _svc.update_research_grant_status(int(tenant["id"]), grant_id, payload, actor)
        return ResearchGrantItemResponseSchema(item=item)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/publications", response_model=ResearchPublicationListResponseSchema)
def list_research_publications_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: ResearchPublicationStatus | None = None,
) -> ResearchPublicationListResponseSchema:
    items = _svc.list_research_publications(int(tenant["id"]), status=status)
    return ResearchPublicationListResponseSchema(items=items)


@router.post("/publications", response_model=ResearchPublicationItemResponseSchema)
def create_research_publication_endpoint(
    payload: ResearchPublicationCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchPublicationItemResponseSchema:
    try:
        item = _svc.create_research_publication(int(tenant["id"]), payload, actor)
        return ResearchPublicationItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/publications/{publication_id}", response_model=ResearchPublicationItemResponseSchema)
def get_research_publication_endpoint(
    publication_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchPublicationItemResponseSchema:
    try:
        item = _svc.get_research_publication(int(tenant["id"]), publication_id)
        return ResearchPublicationItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/publications/{publication_id}/status", response_model=ResearchPublicationItemResponseSchema)
def update_research_publication_status_endpoint(
    publication_id: int,
    payload: ResearchPublicationStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchPublicationItemResponseSchema:
    try:
        item = _svc.update_research_publication_status(int(tenant["id"]), publication_id, payload, actor)
        return ResearchPublicationItemResponseSchema(item=item)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/labs", response_model=ResearchLabListResponseSchema)
def list_research_labs_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchLabListResponseSchema:
    items = _svc.list_research_labs(int(tenant["id"]))
    return ResearchLabListResponseSchema(items=items)


@router.post("/labs", response_model=ResearchLabItemResponseSchema)
def create_research_lab_endpoint(
    payload: ResearchLabCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchLabItemResponseSchema:
    try:
        item = _svc.create_research_lab(int(tenant["id"]), payload, actor)
        return ResearchLabItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/labs/{lab_id}", response_model=ResearchLabItemResponseSchema)
def get_research_lab_endpoint(
    lab_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchLabItemResponseSchema:
    try:
        item = _svc.get_research_lab(int(tenant["id"]), lab_id)
        return ResearchLabItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/labs/{lab_id}/status", response_model=ResearchLabItemResponseSchema)
def update_research_lab_status_endpoint(
    lab_id: int,
    payload: ResearchLabStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchLabItemResponseSchema:
    try:
        item = _svc.update_research_lab_status(int(tenant["id"]), lab_id, payload, actor)
        return ResearchLabItemResponseSchema(item=item)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/ip-assets", response_model=ResearchIpAssetListResponseSchema)
def list_research_ip_assets_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchIpAssetListResponseSchema:
    items = _svc.list_research_ip_assets(int(tenant["id"]))
    return ResearchIpAssetListResponseSchema(items=items)


@router.post("/ip-assets", response_model=ResearchIpAssetItemResponseSchema)
def create_research_ip_assets_endpoint(
    payload: ResearchIpAssetCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchIpAssetItemResponseSchema:
    try:
        item = _svc.create_research_ip_asset(int(tenant["id"]), payload, actor)
        return ResearchIpAssetItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/experiments", response_model=ResearchExperimentListResponseSchema)
def list_research_experiments_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchExperimentListResponseSchema:
    items = _svc.list_research_experiments(int(tenant["id"]))
    return ResearchExperimentListResponseSchema(items=items)


@router.post("/experiments", response_model=ResearchExperimentItemResponseSchema)
def create_research_experiment_endpoint(
    payload: ResearchExperimentCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchExperimentItemResponseSchema:
    try:
        item = _svc.create_research_experiment(int(tenant["id"]), payload, actor)
        return ResearchExperimentItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/experiments/{experiment_id}", response_model=ResearchExperimentItemResponseSchema)
def get_research_experiment_endpoint(
    experiment_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchExperimentItemResponseSchema:
    try:
        item = _svc.get_research_experiment(int(tenant["id"]), experiment_id)
        return ResearchExperimentItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/experiments/{experiment_id}/status", response_model=ResearchExperimentItemResponseSchema)
def update_research_experiment_status_endpoint(
    experiment_id: int,
    payload: ResearchExperimentStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ResearchExperimentItemResponseSchema:
    try:
        item = _svc.update_research_experiment_status(int(tenant["id"]), experiment_id, payload, actor)
        return ResearchExperimentItemResponseSchema(item=item)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
