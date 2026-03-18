from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.modules.feature_flags.service import list_flags, set_flag
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/feature-flags", tags=["feature-flags"])


class FeatureFlagPayload(BaseModel):
    key: str = Field(min_length=3, max_length=128)
    enabled: bool
    description: str | None = Field(default=None, max_length=256)
    scope: str = Field(default="global", min_length=3, max_length=64)


@router.get("")
def get_feature_flags(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, list[dict[str, object]]]:
    return {"flags": list_flags()}


@router.post("")
def upsert_feature_flag(
    payload: FeatureFlagPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
) -> dict[str, dict[str, object]]:
    updated = set_flag(
        key=payload.key,
        enabled=payload.enabled,
        description=payload.description,
        scope=payload.scope,
    )
    return {"flag": updated}
