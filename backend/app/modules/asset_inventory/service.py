"""Phase XI-XI2: Asset Inventory service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.asset_inventory.schemas import (
    AssetCategory,
    AssetCondition,
    AssetItemCreateSchema,
    AssetItemSchema,
    AssetItemStatusUpdateSchema,
    AssetStatus,
    DepreciationRecordCreateSchema,
    DepreciationRecordSchema,
    DepreciationStatus,
)
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="asset_inventory",
        metadata=metadata,
        tenant_id=tenant_id,
    )


# --- Asset Items ---

def list_asset_items(
    tenant_id: int,
    status: AssetStatus | None = None,
    category: AssetCategory | None = None,
    condition: AssetCondition | None = None,
) -> list[AssetItemSchema]:
    rows = list_entities_for_tenant("asset_inventory_items", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if category is not None:
        rows = [r for r in rows if str(r.get("category") or "") == category]
    if condition is not None:
        rows = [r for r in rows if str(r.get("condition") or "") == condition]
    return [AssetItemSchema.model_validate(r) for r in rows]


def get_asset_item(tenant_id: int, asset_id: int) -> AssetItemSchema | None:
    rows = list_entities_for_tenant("asset_inventory_items", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == asset_id), None)
    if row is None:
        return None
    return AssetItemSchema.model_validate(row)


def create_asset_item(
    tenant_id: int,
    request: AssetItemCreateSchema,
    actor: str,
) -> AssetItemSchema:
    created = create_entity_for_tenant(
        "asset_inventory_items",
        {
            "asset_code": request.asset_code.strip(),
            "name": request.name.strip(),
            "category": request.category,
            "location": request.location.strip(),
            "condition": request.condition,
            "purchase_year": int(request.purchase_year),
            "vendor": request.vendor,
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("asset_inventory", "item", "create"),
        path="/internal/asset-inventory/items",
        metadata={"resource_id": str(created.get("id")), "asset_code": request.asset_code},
        tenant_id=tenant_id,
    )
    if request.condition == "condemned":
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="asset_inventory.item.condemned_asset",
            aggregate_type="asset_inventory_items",
            aggregate_id=str(created.get("id") or "unknown"),
            payload_json={
                "asset_code": request.asset_code,
                "name": request.name,
                "condition": request.condition,
            },
        )
    return AssetItemSchema.model_validate(created)


def update_asset_item_status(
    tenant_id: int,
    asset_id: int,
    request: AssetItemStatusUpdateSchema,
    actor: str,
) -> AssetItemSchema | None:
    rows = list_entities_for_tenant("asset_inventory_items", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == asset_id), None)
    if existing is None:
        return None
    updated = update_entity_for_tenant(
        "asset_inventory_items", asset_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("asset_inventory", "item", "status_update"),
        path=f"/internal/asset-inventory/items/{asset_id}/status",
        metadata={"resource_id": str(asset_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return AssetItemSchema.model_validate(updated)


# --- Depreciation Records ---

def list_depreciation_records(
    tenant_id: int,
    status: DepreciationStatus | None = None,
) -> list[DepreciationRecordSchema]:
    rows = list_entities_for_tenant("asset_depreciation_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [DepreciationRecordSchema.model_validate(r) for r in rows]


def get_depreciation_record(tenant_id: int, record_id: int) -> DepreciationRecordSchema | None:
    rows = list_entities_for_tenant("asset_depreciation_records", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if row is None:
        return None
    return DepreciationRecordSchema.model_validate(row)


def create_depreciation_record(
    tenant_id: int,
    request: DepreciationRecordCreateSchema,
    actor: str,
) -> DepreciationRecordSchema:
    created = create_entity_for_tenant(
        "asset_depreciation_records",
        {
            "asset_code": request.asset_code.strip(),
            "depreciation_method": request.depreciation_method,
            "original_value": float(request.original_value),
            "current_value": float(request.current_value),
            "depreciation_rate": float(request.depreciation_rate),
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("asset_inventory", "depreciation", "create"),
        path="/internal/asset-inventory/depreciation",
        metadata={"resource_id": str(created.get("id")), "asset_code": request.asset_code},
        tenant_id=tenant_id,
    )
    return DepreciationRecordSchema.model_validate(created)
