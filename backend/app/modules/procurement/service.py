from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.procurement.schemas import (
    AssetCreateSchema,
    AssetSchema,
    ContractCreateSchema,
    ContractSchema,
    InventoryItemCreateSchema,
    InventoryItemSchema,
    ProcurementHealthSnapshotSchema,
    VendorCreateSchema,
    VendorSchema,
)
from app.modules.university_core.tenant_entity_service import create_entity_for_tenant, list_entities_for_tenant


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="procurement",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _to_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def list_vendors(tenant_id: int) -> list[VendorSchema]:
    rows = list_entities_for_tenant("procurement_vendors", tenant_id)
    return [VendorSchema.model_validate(r) for r in rows]


def create_vendor(tenant_id: int, request: VendorCreateSchema, actor: str) -> VendorSchema:
    created = create_entity_for_tenant(
        "procurement_vendors",
        {
            "vendor_code": request.vendor_code.strip(),
            "name": request.name.strip(),
            "category": request.category.strip(),
            "sla_breach_rate": float(request.sla_breach_rate),
            "on_time_delivery_rate": float(request.on_time_delivery_rate),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("procurement", "vendor", "create"),
        path="/internal/procurement/vendors",
        metadata={"resource_id": str(created.get("id")), "vendor_code": request.vendor_code},
        tenant_id=tenant_id,
    )
    return VendorSchema.model_validate(created)


def list_contracts(tenant_id: int) -> list[ContractSchema]:
    rows = list_entities_for_tenant("procurement_contracts", tenant_id)
    return [ContractSchema.model_validate(r) for r in rows]


def create_contract(tenant_id: int, request: ContractCreateSchema, actor: str) -> ContractSchema:
    created = create_entity_for_tenant(
        "procurement_contracts",
        {
            "contract_code": request.contract_code.strip(),
            "vendor_code": request.vendor_code.strip(),
            "title": request.title.strip(),
            "risk_score": float(request.risk_score),
            "sla_target_met": "true" if request.sla_target_met else "false",
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("procurement", "contract", "create"),
        path="/internal/procurement/contracts",
        metadata={"resource_id": str(created.get("id")), "contract_code": request.contract_code},
        tenant_id=tenant_id,
    )
    return ContractSchema.model_validate(created)


def list_assets(tenant_id: int) -> list[AssetSchema]:
    rows = list_entities_for_tenant("procurement_assets", tenant_id)
    return [AssetSchema.model_validate(r) for r in rows]


def create_asset(tenant_id: int, request: AssetCreateSchema, actor: str) -> AssetSchema:
    created = create_entity_for_tenant(
        "procurement_assets",
        {
            "asset_code": request.asset_code.strip(),
            "title": request.title.strip(),
            "asset_category": request.asset_category.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("procurement", "asset", "create"),
        path="/internal/procurement/assets",
        metadata={"resource_id": str(created.get("id")), "asset_code": request.asset_code},
        tenant_id=tenant_id,
    )
    return AssetSchema.model_validate(created)


def list_inventory_items(tenant_id: int) -> list[InventoryItemSchema]:
    rows = list_entities_for_tenant("procurement_inventory_items", tenant_id)
    return [InventoryItemSchema.model_validate(r) for r in rows]


def create_inventory_item(tenant_id: int, request: InventoryItemCreateSchema, actor: str) -> InventoryItemSchema:
    created = create_entity_for_tenant(
        "procurement_inventory_items",
        {
            "item_code": request.item_code.strip(),
            "title": request.title.strip(),
            "current_stock": float(request.current_stock),
            "reorder_point": float(request.reorder_point),
            "daily_usage_rate": float(request.daily_usage_rate),
            "lead_time_days": int(request.lead_time_days),
            "auto_reorder_enabled": bool(request.auto_reorder_enabled),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("procurement", "inventory_item", "create"),
        path="/internal/procurement/inventory-items",
        metadata={"resource_id": str(created.get("id")), "item_code": request.item_code},
        tenant_id=tenant_id,
    )
    return InventoryItemSchema.model_validate(created)


def get_procurement_health_snapshot(tenant_id: int) -> ProcurementHealthSnapshotSchema:
    vendor_rows = list_entities_for_tenant("procurement_vendors", tenant_id)
    contract_rows = list_entities_for_tenant("procurement_contracts", tenant_id)
    asset_rows = list_entities_for_tenant("procurement_assets", tenant_id)
    inventory_rows = list_entities_for_tenant("procurement_inventory_items", tenant_id)

    active_vendors = 0
    vendors_sla_breached = 0
    for row in vendor_rows:
        if str(row.get("status") or "") == "active":
            active_vendors += 1
        sla_breach_rate = _to_float(row.get("sla_breach_rate"))
        on_time_delivery_rate = _to_float(row.get("on_time_delivery_rate"))
        if (
            sla_breach_rate is not None
            and sla_breach_rate >= 0.10
        ) or (
            on_time_delivery_rate is not None
            and on_time_delivery_rate <= 0.90
        ):
            vendors_sla_breached += 1

    at_risk_contracts = 0
    contracts_high_risk = 0
    for row in contract_rows:
        if str(row.get("status") or "") in {"expiring", "expired"}:
            at_risk_contracts += 1
        risk_score = _to_float(row.get("risk_score"))
        sla_target_met = _to_bool(row.get("sla_target_met"))
        if (
            risk_score is not None
            and risk_score >= 0.70
        ) or not sla_target_met:
            contracts_high_risk += 1

    constrained_assets = 0
    for row in asset_rows:
        if str(row.get("status") or "") in {"maintenance", "retired"}:
            constrained_assets += 1

    low_stock_items = 0
    projected_stockouts_7d = 0
    auto_reorder_candidates = 0
    for row in inventory_rows:
        current_stock = _to_float(row.get("current_stock"))
        reorder_point = _to_float(row.get("reorder_point"))
        daily_usage_rate = _to_float(row.get("daily_usage_rate"))
        lead_time_days = _to_int(row.get("lead_time_days"))
        auto_reorder_enabled = _to_bool(row.get("auto_reorder_enabled"))

        if current_stock is not None and reorder_point is not None and current_stock <= reorder_point:
            low_stock_items += 1

        projected_days_remaining: float | None = None
        if current_stock is not None and daily_usage_rate is not None and daily_usage_rate > 0:
            projected_days_remaining = current_stock / daily_usage_rate

        if projected_days_remaining is not None and projected_days_remaining <= 7:
            projected_stockouts_7d += 1

        if (
            auto_reorder_enabled
            and projected_days_remaining is not None
            and lead_time_days is not None
            and projected_days_remaining <= max(7, lead_time_days)
        ):
            auto_reorder_candidates += 1

    return ProcurementHealthSnapshotSchema(
        tenant_id=tenant_id,
        vendors_total=len(vendor_rows),
        active_vendors=active_vendors,
        vendors_sla_breached=vendors_sla_breached,
        contracts_total=len(contract_rows),
        at_risk_contracts=at_risk_contracts,
        contracts_high_risk=contracts_high_risk,
        assets_total=len(asset_rows),
        constrained_assets=constrained_assets,
        inventory_items_total=len(inventory_rows),
        low_stock_items=low_stock_items,
        projected_stockouts_7d=projected_stockouts_7d,
        auto_reorder_candidates=auto_reorder_candidates,
    )