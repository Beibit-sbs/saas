from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.modules.integrations.service import (
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


@router.get("/settings")
def get_settings(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, object]:
    return {
        "ldap": get_ldap_config_for_admin(),
        "ai_providers": list_ai_provider_config_for_admin(),
    }


@router.put("/ldap")
def update_ldap_settings(
    payload: LdapConfigPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, object]:
    ldap = save_ldap_config(payload.model_dump(exclude_unset=True))
    return {"ldap": ldap}


@router.put("/ai/{provider}")
def update_ai_provider_settings(
    provider: str,
    payload: AiProviderConfigPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, object]:
    try:
        result = save_ai_provider_config(provider, payload.api_key, payload.validation_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"provider": result}
