from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.core.tenant import get_current_tenant
from app.modules.ldap.schemas import LdapTestPayload
from app.modules.ldap.service import ldap_status, test_ldap_connection
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/ldap", tags=["ldap-admin"])


@router.get("/status")
def get_ldap_status(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    return {"ldap": ldap_status(tenant_id=int(tenant["id"]))}


@router.post("/test-connection")
def test_connection(
    payload: LdapTestPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    try:
        result = test_ldap_connection(payload.username, payload.password, tenant_id=int(tenant["id"]))
        log_admin_action(
            actor=actor,
            action="ldap.test_connection",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="integrations_ldap",
            result="success",
            metadata={"username_provided": bool(payload.username)},
            tenant_id=int(tenant["id"]),
        )
        return {"result": result}
    except ValueError as exc:
        log_admin_action(
            actor=actor,
            action="ldap.test_connection",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="integrations_ldap",
            result="failed",
            metadata={"username_provided": bool(payload.username), "error": str(exc)},
            tenant_id=int(tenant["id"]),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc