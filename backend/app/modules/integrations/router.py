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
from app.platform.events.publisher import EventPublisher

router = APIRouter(prefix="/api/admin/integrations", tags=["integrations"])


def _publish_integration_updated_event(
    *,
    tenant_id: int,
    actor: str,
    integration_type: str,
    aggregate_id: str,
    fields_updated: list[str],
    idempotent_replay: bool,
    provider: str | None = None,
    secret_fields_updated: list[str] | None = None,
) -> None:
    if idempotent_replay:
        return

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="integration.updated",
        aggregate_type="integration",
        aggregate_id=aggregate_id,
        payload_json={
            "integration_type": integration_type,
            "actor": actor,
            "fields_updated": fields_updated,
            "idempotent_replay": False,
            "provider": provider,
            "secret_fields_updated": secret_fields_updated or [],
        },
    )


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
    # For secret fields, admin responses only expose presence flags, so treat explicit updates as non-idempotent.
    if "bind_password" in updated_fields:
        idempotent_replay = False
    else:
        idempotent_replay = all(
            str(before.get(field, "")).strip() == str(value).strip()
            for field, value in updated_fields.items()
        )
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

    _publish_integration_updated_event(
        tenant_id=int(tenant["id"]),
        actor=actor,
        integration_type="ldap",
        aggregate_id="ldap",
        fields_updated=sorted(list(updated_fields.keys())),
        idempotent_replay=idempotent_replay,
        secret_fields_updated=["bind_password"] if "bind_password" in updated_fields else [],
    )

    return LdapUpdateResponse(ldap=ldap, idempotent_replay=idempotent_replay)


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
    updated_fields = {
        field_name: field_value
        for field_name, field_value in {
            "api_key": payload.api_key,
            "validation_url": payload.validation_url,
        }.items()
        if field_value is not None
    }
    if "api_key" in updated_fields:
        idempotent_replay = False
    elif "validation_url" in updated_fields:
        idempotent_replay = str(before.get("validation_url", "")).strip() == str(updated_fields["validation_url"]).strip()
    else:
        idempotent_replay = True
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

    _publish_integration_updated_event(
        tenant_id=int(tenant["id"]),
        actor=actor,
        integration_type="ai_provider",
        aggregate_id=provider.strip().lower(),
        fields_updated=sorted(updated_fields.keys()),
        idempotent_replay=idempotent_replay,
        provider=provider.strip().lower(),
        secret_fields_updated=["api_key"] if payload.api_key is not None else [],
    )

    return AiProviderUpdateResponse(provider=result, idempotent_replay=idempotent_replay)
