"""Phase VI-VI2: Dining router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.dining.schemas import (
    DiningBrainContextResponse,
    DiningMenuCreatePayload,
    DiningMenuItemResponse,
    DiningMenuListResponse,
    DiningOrderCreatePayload,
    DiningOrderItemResponse,
    DiningOrderListResponse,
)
from app.modules.dining.service import (
    create_dining_menu,
    create_dining_order,
    get_dining_brain_context,
    list_dining_menus,
    list_dining_orders,
)

router = APIRouter(prefix="/api/admin/dining", tags=["dining"])


@router.get("/menus", response_model=DiningMenuListResponse)
def list_menus_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    meal_type: str | None = None,
    status: str | None = None,
) -> DiningMenuListResponse:
    return DiningMenuListResponse(
        records=list_dining_menus(int(tenant["id"]), meal_type=meal_type, status=status)
    )


@router.post("/menus", response_model=DiningMenuItemResponse, status_code=201)
def create_menu_endpoint(
    payload: DiningMenuCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DiningMenuItemResponse:
    return DiningMenuItemResponse(
        record=create_dining_menu(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/orders", response_model=DiningOrderListResponse)
def list_orders_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
) -> DiningOrderListResponse:
    return DiningOrderListResponse(
        records=list_dining_orders(int(tenant["id"]), status=status)
    )


@router.post("/orders", response_model=DiningOrderItemResponse, status_code=201)
def create_order_endpoint(
    payload: DiningOrderCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DiningOrderItemResponse:
    return DiningOrderItemResponse(
        record=create_dining_order(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=DiningBrainContextResponse)
def brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DiningBrainContextResponse:
    return DiningBrainContextResponse(**get_dining_brain_context(int(tenant["id"])))
