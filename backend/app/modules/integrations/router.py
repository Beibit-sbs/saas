from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.integrations.service import (
    get_ai_provider_config_for_admin,
    get_ldap_config_for_admin,
    list_ai_provider_config_for_admin,
    save_ai_provider_config,
    save_ldap_config,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/integrations", tags=["integrations"])


class LdapConfigPayload(BaseModel):
    enabled: bool | None = None
    server_uri: str | None = None
    bind_dn: str | None = None
    bind_password: str | None = None
    base_dn: str | None = None
    user_filter: str | None = None
    display_name_attribute: str | None = None
    login_attribute: str | None = None
    group_attribute: str | None = None
    group_role_map_json: str | None = None
    default_role: str | None = None
    timeout_seconds: int | None = None


class AiProviderConfigPayload(BaseModel):
    api_key: str | None = None
    validation_url: str | None = None


class LdapUpdateResponse(BaseModel):
    ldap: dict[str, object]
    idempotent_replay: bool


class AiProviderUpdateResponse(BaseModel):
    provider: dict[str, object]
    idempotent_replay: bool


@router.get("/settings")
def get_settings(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    return {
        "ldap": get_ldap_config_for_admin(tenant_id=int(tenant["id"])),
        "ai_providers": list_ai_provider_config_for_admin(tenant_id=int(tenant["id"])),
    }


@router.put("/ldap")
def update_ldap_settings(
    payload: LdapConfigPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> LdapUpdateResponse:
    before = get_ldap_config_for_admin(tenant_id=int(tenant["id"]))
    updated_fields = payload.model_dump(exclude_unset=True)
    ldap = save_ldap_config(updated_fields, tenant_id=int(tenant["id"]))
    log_admin_action(
        actor=actor,
        action="integrations.ldap.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="integrations_ldap",
        result="success",
        metadata={
            "fields_updated": sorted(list(updated_fields.keys())),
            "bind_password_changed": "bind_password" in updated_fields,
        },
        tenant_id=int(tenant["id"]),
    )
    return LdapUpdateResponse(ldap=ldap, idempotent_replay=before == ldap)


@router.put("/ai/{provider}")
def update_ai_provider_settings(
    provider: str,
    payload: AiProviderConfigPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AiProviderUpdateResponse:
    before = get_ai_provider_config_for_admin(provider, tenant_id=int(tenant["id"]))
    try:
        result = save_ai_provider_config(
            provider,
            payload.api_key,
            payload.validation_url,
            tenant_id=int(tenant["id"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="integrations.ai_provider.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="integrations_ai",
        result="success",
        metadata={
            "provider": provider,
            "api_key_updated": payload.api_key is not None,
            "validation_url_updated": payload.validation_url is not None,
        },
        tenant_id=int(tenant["id"]),
    )

    return AiProviderUpdateResponse(provider=result, idempotent_replay=before == result)
