from __future__ import annotations

import logging
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.core.errors import DependencyUnavailableError
from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.identity.identity_errors import IdentityError
from app.modules.identity.phase1_service import (
    create_directory_provider,
    create_identity_mapping,
    delete_identity_mapping,
    list_directory_providers,
    list_identity_mappings,
    preview_provider_mapping,
    test_directory_provider,
    update_directory_provider,
    update_identity_mapping,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/identity", tags=["identity"])

logger = logging.getLogger("app.identity_phase1")


def _raise_identity_http(exc: IdentityError) -> None:
    raise HTTPException(status_code=int(exc.http_status), detail=exc.to_response())


def _mark_phase1_usage(response: Response, tenant: dict[str, object], actor: str | None, resource: str) -> None:
    response.headers["X-Legacy-Namespace"] = "true"
    response.headers["Warning"] = '299 - "Legacy identity namespace under migration review: target /api/admin/identity/*"'
    logger.warning(
        "legacy identity phase1 endpoint used; resource=%s tenant_id=%s actor=%s",
        resource, tenant.get("id"), actor,
    )


class IdentityMappingPayload(BaseModel):
    external_group: str = Field(min_length=1, max_length=512)
    platform_role: str = Field(min_length=1, max_length=128)


class IdentityProviderConfigPayload(BaseModel):
    host: str | None = None
    port: int | None = None
    use_ssl: bool = True
    base_dn: str | None = None
    bind_dn: str | None = None
    user_filter: str | None = None
    group_attribute: str | None = None
    display_name_attribute: str | None = None
    login_attribute: str | None = None
    external_id_attribute: str | None = None
    email_attribute: str | None = None
    timeout_seconds: int | None = None


class IdentityProviderPolicyPayload(BaseModel):
    is_default: bool = False
    priority: int = Field(default=100, ge=0, le=10_000)
    allow_local_login: bool = True
    allow_external_login: bool = True
    login_hint: str | None = Field(default=None, max_length=256)
    auto_provision: bool = True
    require_mapping: bool = True


class CreateIdentityProviderPayload(BaseModel):
    type: Literal["local", "ldap", "ad"]
    name: str = Field(min_length=2, max_length=128)
    is_enabled: bool = True
    config: IdentityProviderConfigPayload = Field(default_factory=IdentityProviderConfigPayload)
    policy: IdentityProviderPolicyPayload = Field(default_factory=IdentityProviderPolicyPayload)
    bind_password: str | None = None
    mappings: list[IdentityMappingPayload] = Field(default_factory=list)


class UpdateIdentityProviderPayload(BaseModel):
    type: Literal["local", "ldap", "ad"] | None = None
    name: str | None = Field(default=None, min_length=2, max_length=128)
    is_enabled: bool | None = None
    config: IdentityProviderConfigPayload | None = None
    policy: IdentityProviderPolicyPayload | None = None
    bind_password: str | None = None
    mappings: list[IdentityMappingPayload] | None = None


class ProviderTestPayload(BaseModel):
    login: str | None = None
    password: str | None = None


class MappingPreviewPayload(BaseModel):
    username: str = Field(min_length=1, max_length=256)


class CreateMappingPayload(BaseModel):
    provider_id: int = Field(ge=1)
    external_group: str = Field(min_length=1, max_length=512)
    platform_role: str = Field(min_length=1, max_length=128)


class UpdateMappingPayload(BaseModel):
    external_group: str = Field(min_length=1, max_length=512)
    platform_role: str = Field(min_length=1, max_length=128)


@router.post("/providers")
def post_identity_provider(
    payload: CreateIdentityProviderPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, dict[str, Any]]:
    _mark_phase1_usage(response, tenant, actor, resource="providers")
    try:
        provider = create_directory_provider(
            tenant_id=int(tenant["id"]),
            provider_type=payload.type,
            name=payload.name,
            is_enabled=payload.is_enabled,
            config=payload.config.model_dump(exclude_none=True),
            policy=payload.policy.model_dump(exclude_none=True),
            bind_password=payload.bind_password,
            mappings=[row.model_dump() for row in payload.mappings],
        )
    except IdentityError as exc:
        _raise_identity_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.provider.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider.get("id"), "provider_type": provider.get("type"), "provider_name": provider.get("name")},
    )
    return {"provider": provider}


@router.get("/providers")
def get_identity_providers(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, list[dict[str, Any]]]:
    _mark_phase1_usage(response, tenant, _, resource="providers")
    try:
        rows = list_directory_providers(tenant_id=int(tenant["id"]))
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc
    return {"providers": rows}


@router.put("/providers/{provider_id}")
def put_identity_provider(
    provider_id: int,
    payload: UpdateIdentityProviderPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, dict[str, Any]]:
    _mark_phase1_usage(response, tenant, actor, resource="providers")
    update_payload = payload.model_dump(exclude_none=True)
    if "config" in update_payload:
        update_payload["config"] = payload.config.model_dump(exclude_none=True) if payload.config is not None else {}
    if "policy" in update_payload:
        update_payload["policy"] = payload.policy.model_dump(exclude_none=True) if payload.policy is not None else {}
    if "mappings" in update_payload:
        update_payload["mappings"] = [row.model_dump() for row in (payload.mappings or [])]

    try:
        provider = update_directory_provider(
            tenant_id=int(tenant["id"]),
            provider_id=int(provider_id),
            payload=update_payload,
        )
    except IdentityError as exc:
        _raise_identity_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.provider.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider.get("id"), "provider_type": provider.get("type"), "provider_name": provider.get("name")},
    )
    return {"provider": provider}


@router.post("/providers/{provider_id}/test")
def test_identity_provider(
    provider_id: int,
    payload: ProviderTestPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, dict[str, Any]]:
    _mark_phase1_usage(response, tenant, actor, resource="providers")
    try:
        result = test_directory_provider(
            tenant_id=int(tenant["id"]),
            provider_id=int(provider_id),
            login=payload.login,
            password=payload.password,
        )
    except IdentityError as exc:
        _raise_identity_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.provider.test",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider_id, "status": result.get("status")},
    )
    return {"result": result}


@router.post("/providers/{provider_id}/mapping/preview")
def mapping_preview(
    provider_id: int,
    payload: MappingPreviewPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, dict[str, Any]]:
    _mark_phase1_usage(response, tenant, actor, resource="providers")
    try:
        result = preview_provider_mapping(
            tenant_id=int(tenant["id"]),
            provider_id=int(provider_id),
            username=payload.username,
        )
    except IdentityError as exc:
        _raise_identity_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.mapping.preview",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider_id, "username": payload.username},
    )
    return {"preview": result}


@router.post("/mappings")
def post_mapping(
    payload: CreateMappingPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, dict[str, Any]]:
    _mark_phase1_usage(response, tenant, actor, resource="mappings")
    try:
        mapping = create_identity_mapping(
            tenant_id=int(tenant["id"]),
            provider_id=int(payload.provider_id),
            external_group=payload.external_group,
            platform_role=payload.platform_role,
        )
    except IdentityError as exc:
        _raise_identity_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.mapping.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"mapping_id": mapping.get("id"), "provider_id": mapping.get("provider_id")},
    )
    return {"mapping": mapping}


@router.get("/mappings")
def get_mappings(
    provider_id: int | None = None,
    _: Annotated[str, Depends(get_actor)] = None,
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))] = None,
    tenant: Annotated[dict, Depends(get_current_tenant)] = None,
    response: Response = None,
) -> dict[str, list[dict[str, Any]]]:
    if response is not None:
        _mark_phase1_usage(response, tenant, _, resource="mappings")
    try:
        rows = list_identity_mappings(tenant_id=int(tenant["id"]), provider_id=provider_id)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc
    return {"mappings": rows}


@router.put("/mappings/{mapping_id}")
def put_mapping(
    mapping_id: int,
    payload: UpdateMappingPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, dict[str, Any]]:
    _mark_phase1_usage(response, tenant, actor, resource="mappings")
    try:
        mapping = update_identity_mapping(
            tenant_id=int(tenant["id"]),
            mapping_id=int(mapping_id),
            external_group=payload.external_group,
            platform_role=payload.platform_role,
        )
    except IdentityError as exc:
        _raise_identity_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.mapping.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"mapping_id": mapping.get("id")},
    )
    return {"mapping": mapping}


@router.delete("/mappings/{mapping_id}")
def remove_mapping(
    mapping_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    response: Response,
) -> dict[str, bool]:
    _mark_phase1_usage(response, tenant, actor, resource="mappings")
    try:
        deleted = delete_identity_mapping(tenant_id=int(tenant["id"]), mapping_id=int(mapping_id))
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.mapping.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success" if deleted else "noop",
        metadata={"mapping_id": mapping_id},
    )
    return {"deleted": bool(deleted)}
