from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.modules.identity.service import list_identity_providers, upsert_identity_provider
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/identity", tags=["identity-admin"])


def _raise_phase1_http(exc: IdentityError) -> None:
    raise HTTPException(status_code=int(exc.http_status), detail=exc.to_response())


class IdentityProviderPayload(BaseModel):
    provider: str = Field(min_length=2, max_length=64)
    type: str = Field(min_length=4, max_length=16)
    enabled: bool = True
    issuer: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    saml_metadata_url: str | None = None
    saml_sso_url: str | None = None
    saml_entity_id: str | None = None
    tenant_scope: str = Field(default="tenant", min_length=6, max_length=16)


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


class CreateDirectoryProviderPayload(BaseModel):
    type: Literal["local", "ldap", "ad"]
    name: str = Field(min_length=2, max_length=128)
    is_enabled: bool = True
    config: IdentityProviderConfigPayload = Field(default_factory=IdentityProviderConfigPayload)
    policy: IdentityProviderPolicyPayload = Field(default_factory=IdentityProviderPolicyPayload)
    bind_password: str | None = None
    mappings: list[IdentityMappingPayload] = Field(default_factory=list)


class UpdateDirectoryProviderPayload(BaseModel):
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


@router.get("/providers")
def get_identity_providers(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, list[dict[str, object]]]:
    return {"providers": list_identity_providers(tenant_id=int(tenant["id"]))}


@router.put("/providers/{provider}")
def put_identity_provider(
    provider: str,
    payload: IdentityProviderPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    if provider.strip().lower() != payload.provider.strip().lower():
        raise HTTPException(status_code=400, detail="provider path mismatch")
    try:
        row = upsert_identity_provider(tenant_id=int(tenant["id"]), payload=payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.provider.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider": row.get("provider"), "type": row.get("type"), "enabled": row.get("enabled")},
    )
    return {"provider": row}


@router.post("/directory-providers")
def post_directory_provider(
    payload: CreateDirectoryProviderPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, Any]]:
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
        _raise_phase1_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.directory_provider.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider.get("id"), "provider_type": provider.get("type"), "provider_name": provider.get("name")},
    )
    return {"provider": provider}


@router.get("/directory-providers")
def get_directory_providers(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, list[dict[str, Any]]]:
    try:
        rows = list_directory_providers(tenant_id=int(tenant["id"]))
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc
    return {"providers": rows}


@router.put("/directory-providers/{provider_id}")
def put_directory_provider(
    provider_id: int,
    payload: UpdateDirectoryProviderPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, Any]]:
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
        _raise_phase1_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.directory_provider.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider.get("id"), "provider_type": provider.get("type"), "provider_name": provider.get("name")},
    )
    return {"provider": provider}


@router.post("/directory-providers/{provider_id}/test")
def post_directory_provider_test(
    provider_id: int,
    payload: ProviderTestPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, Any]]:
    try:
        result = test_directory_provider(
            tenant_id=int(tenant["id"]),
            provider_id=int(provider_id),
            login=payload.login,
            password=payload.password,
        )
    except IdentityError as exc:
        _raise_phase1_http(exc)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.directory_provider.test",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider_id": provider_id, "status": result.get("status")},
    )
    return {"result": result}


@router.post("/directory-providers/{provider_id}/mapping/preview")
def post_directory_mapping_preview(
    provider_id: int,
    payload: MappingPreviewPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, Any]]:
    try:
        result = preview_provider_mapping(
            tenant_id=int(tenant["id"]),
            provider_id=int(provider_id),
            username=payload.username,
        )
    except IdentityError as exc:
        _raise_phase1_http(exc)
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
def post_identity_mapping(
    payload: CreateMappingPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, Any]]:
    try:
        mapping = create_identity_mapping(
            tenant_id=int(tenant["id"]),
            provider_id=int(payload.provider_id),
            external_group=payload.external_group,
            platform_role=payload.platform_role,
        )
    except IdentityError as exc:
        _raise_phase1_http(exc)
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
def get_identity_mappings(
    provider_id: int | None = None,
    _: Annotated[str, Depends(get_actor)] = None,
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))] = None,
    tenant: Annotated[dict, Depends(get_current_tenant)] = None,
) -> dict[str, list[dict[str, Any]]]:
    try:
        rows = list_identity_mappings(tenant_id=int(tenant["id"]), provider_id=provider_id)
    except DependencyUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc
    return {"mappings": rows}


@router.put("/mappings/{mapping_id}")
def put_identity_mapping(
    mapping_id: int,
    payload: UpdateMappingPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, Any]]:
    try:
        mapping = update_identity_mapping(
            tenant_id=int(tenant["id"]),
            mapping_id=int(mapping_id),
            external_group=payload.external_group,
            platform_role=payload.platform_role,
        )
    except IdentityError as exc:
        _raise_phase1_http(exc)
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
def delete_identity_mapping_endpoint(
    mapping_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, bool]:
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
