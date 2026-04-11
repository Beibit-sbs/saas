from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.errors import DependencyUnavailableError
from app.core.tenant import get_current_tenant
from app.modules.identity.identity_errors import IdentityError
from app.modules.identity.router import (
	create_identity_mapping,
	delete_identity_mapping,
	list_identity_mappings,
	preview_provider_mapping,
	router,
	test_directory_provider,
	update_identity_mapping,
)
from app.modules.rbac.security import get_actor, permission_dependency


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


router = APIRouter(prefix="/api/identity", tags=["identity-phase1-compat"])


def _raise_phase1_http(exc: IdentityError) -> None:
	raise HTTPException(status_code=int(exc.http_status), detail=exc.to_response())


@router.post("/providers/{provider_id}/test")
def provider_test_compat(
	provider_id: int,
	payload: ProviderTestPayload,
	_: Annotated[str, Depends(get_actor)],
	__: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
	tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
	try:
		result = test_directory_provider(
			tenant_id=int(tenant["id"]),
			provider_id=provider_id,
			login=payload.login,
			password=payload.password,
		)
	except IdentityError as exc:
		_raise_phase1_http(exc)
	except DependencyUnavailableError as exc:
		raise HTTPException(
			status_code=503,
			detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)},
		) from exc
	return {"result": result}


@router.post("/providers/{provider_id}/mapping/preview")
def mapping_preview_compat(
	provider_id: int,
	payload: MappingPreviewPayload,
	_: Annotated[str, Depends(get_actor)],
	__: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
	tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
	try:
		preview = preview_provider_mapping(
			tenant_id=int(tenant["id"]),
			provider_id=provider_id,
			username=payload.username,
		)
	except IdentityError as exc:
		_raise_phase1_http(exc)
	except DependencyUnavailableError as exc:
		raise HTTPException(
			status_code=503,
			detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE", "message": str(exc)},
		) from exc
	return {"preview": preview}


@router.post("/mappings")
def create_mapping_compat(
	payload: CreateMappingPayload,
	_: Annotated[str, Depends(get_actor)],
	__: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
	tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
	try:
		mapping = create_identity_mapping(
			tenant_id=int(tenant["id"]),
			provider_id=payload.provider_id,
			external_group=payload.external_group,
			platform_role=payload.platform_role,
		)
	except IdentityError as exc:
		_raise_phase1_http(exc)
	return {"mapping": mapping}


@router.get("/mappings")
def list_mappings_compat(
	provider_id: int | None = Query(default=None, ge=1),
	_: Annotated[str, Depends(get_actor)] = None,
	__: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))] = None,
	tenant: Annotated[dict, Depends(get_current_tenant)] = None,
) -> dict[str, object]:
	try:
		mappings = list_identity_mappings(
			tenant_id=int(tenant["id"]),
			provider_id=provider_id,
		)
	except IdentityError as exc:
		_raise_phase1_http(exc)
	return {"mappings": mappings}


@router.put("/mappings/{mapping_id}")
def update_mapping_compat(
	mapping_id: int,
	payload: UpdateMappingPayload,
	_: Annotated[str, Depends(get_actor)],
	__: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
	tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
	try:
		mapping = update_identity_mapping(
			tenant_id=int(tenant["id"]),
			mapping_id=mapping_id,
			external_group=payload.external_group,
			platform_role=payload.platform_role,
		)
	except IdentityError as exc:
		_raise_phase1_http(exc)
	return {"mapping": mapping}


@router.delete("/mappings/{mapping_id}")
def delete_mapping_compat(
	mapping_id: int,
	_: Annotated[str, Depends(get_actor)],
	__: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
	tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
	try:
		deleted = delete_identity_mapping(
			tenant_id=int(tenant["id"]),
			mapping_id=mapping_id,
		)
	except IdentityError as exc:
		_raise_phase1_http(exc)
	return {"deleted": bool(deleted)}

__all__ = [
	"router",
	"create_identity_mapping",
	"list_identity_mappings",
	"update_identity_mapping",
	"delete_identity_mapping",
	"preview_provider_mapping",
	"test_directory_provider",
]
