from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.modules.ldap.service import ldap_status, test_ldap_connection
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/ldap", tags=["ldap-admin"])


class LdapTestPayload(BaseModel):
    username: str | None = None
    password: str | None = None


@router.get("/status")
def get_ldap_status(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, object]:
    return {"ldap": ldap_status()}


@router.post("/test-connection")
def test_connection(
    payload: LdapTestPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, object]:
    try:
        return {"result": test_ldap_connection(payload.username, payload.password)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc