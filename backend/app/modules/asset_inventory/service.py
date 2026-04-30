"""Phase XI-XI2: Asset Inventory service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
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

# W26 — depreciation method cap (max active records per method per tenant)
_METHOD_MAX_ACTIVE_DEPR: dict[str, int] = {
    "straight_line": 10,
    "declining_balance": 5,
}
_ACTIVE_STATUSES_DEPR: frozenset[str] = frozenset({"active"})

# W114: Only assets in these statuses may receive new depreciation records.
# decommissioned assets have been taken out of service — scheduling amortization
# on them creates phantom financial entries and corrupts book value calculations.
_DEPRECIABLE_ASSET_STATUSES: frozenset[str] = frozenset({"active", "in_maintenance"})

# W114: Asset conditions that disqualify an asset from receiving depreciation records.
# A condemned asset is already flagged for disposal/write-off; adding depreciation
# creates conflicting financial records and distorts the write-off process.
_NON_DEPRECIABLE_ASSET_CONDITIONS: frozenset[str] = frozenset({"condemned"})

# ---------------------------------------------------------------------------
# W56 — condemned asset cap: max allowed condemned items per category
# ---------------------------------------------------------------------------
_ASSET_CATEGORY_MAX_CONDEMNED: dict[str, int] = {
    "it_hardware": 10,
    "furniture": 20,
    "vehicle": 5,
    "equipment": 8,
    "other": 6,
}

# ---------------------------------------------------------------------------
# Asset statuses that indicate condemned/write-off risk state
# ---------------------------------------------------------------------------
_CONDEMNED_ASSET_STATUSES: frozenset[str] = frozenset({"condemned"})

# ---------------------------------------------------------------------------
# Asset statuses that trigger write-off risk alerts
# ---------------------------------------------------------------------------
_WRITEOFF_RISK_STATUSES: frozenset[str] = frozenset({"condemned"})


def _check_asset_depreciable(
    *,
    tenant_id: int,
    asset_code: str,
) -> None:
    """Cross-entity guard: asset_depreciation_records × asset_inventory_items by asset_code.

    A depreciation record may ONLY be created when the referenced asset is in an
    active operational state (status: active or in_maintenance) AND is not condemned:

    - decommissioned: taken out of service — no remaining book value to depreciate
    - condemned: flagged for disposal/write-off — depreciation conflicts with write-off process

    Creating depreciation on non-depreciable assets:
    - Inflates reported depreciation expenses (phantom entries in P&L)
    - Distorts asset portfolio valuation and book value
    - Creates conflicting financial records (simultaneous write-off + active depreciation)
    - Causes audit failures in asset register reviews

    FAIL-CLOSED: If asset lookup raises any exception, depreciation creation is BLOCKED.
    Cannot schedule amortization without confirming the asset's operational status.
    """
    try:
        all_assets = list_entities_for_tenant("asset_inventory_items", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Depreciation record blocked for asset_code='{asset_code}': "
            f"asset lookup failed \u2014 {exc}. "
            f"Cannot schedule amortization without confirming asset status."
        ) from exc

    normalized_code = asset_code.strip().lower()
    asset = next(
        (row for row in all_assets
         if str(row.get("asset_code") or "").strip().lower() == normalized_code),
        None,
    )

    if asset is None:
        raise DomainValidationError(
            f"Depreciation record blocked: asset_code='{asset_code}' not found. "
            f"Cannot create depreciation schedule for a non-existent asset."
        )

    asset_status = str(asset.get("status") or "").strip().lower()
    if asset_status not in _DEPRECIABLE_ASSET_STATUSES:
        raise DomainValidationError(
            f"Depreciation record blocked for asset_code='{asset_code}': "
            f"asset status is '{asset_status}' which is not eligible for depreciation. "
            f"Only assets with status active or in_maintenance may be depreciated. "
            f"Decommissioned assets have no remaining book value to schedule amortization against."
        )

    asset_condition = str(asset.get("condition") or "").strip().lower()
    if asset_condition in _NON_DEPRECIABLE_ASSET_CONDITIONS:
        raise DomainValidationError(
            f"Depreciation record blocked for asset_code='{asset_code}': "
            f"asset condition is '{asset_condition}'. "
            f"Condemned assets are flagged for disposal — creating a depreciation schedule "
            f"simultaneously conflicts with the write-off process and distorts book value."
        )


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
    # W56 — condemned cap: limit condemned assets per category
    condemned_cap = _ASSET_CATEGORY_MAX_CONDEMNED.get(str(request.category or ""))
    if condemned_cap is not None and str(request.condition) in _CONDEMNED_ASSET_STATUSES:
        existing_items = list_entities_for_tenant("asset_inventory_items", tenant_id)
        condemned_count = sum(
            1 for r in existing_items
            if str(r.get("category") or "") == request.category
            and str(r.get("condition") or "") in _CONDEMNED_ASSET_STATUSES
        )
        if condemned_count >= condemned_cap:
            raise ValueError(
                f"condemned asset cap reached for category '{request.category}'"
            )

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

    # W56 — trigger condemned risk alert on status update if condition is in risk set
    if str(existing.get("condition") or "") in _WRITEOFF_RISK_STATUSES:
        _ensure_asset_condemned_risk_alert(tenant_id, asset_id, dict(updated))

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


def _ensure_asset_condemned_risk_alert(tenant_id: int, asset_id: int, asset_data: dict) -> None:
    """Idempotent: create asset_condemned_risk_alerts record and publish event.

    Uses integration_source='asset_condemned_queue' + source_entity_id to prevent duplicates.
    """
    existing = [
        r for r in list_entities_for_tenant("asset_condemned_risk_alerts", tenant_id)
        if str(r.get("integration_source")) == "asset_condemned_queue"
        and str(r.get("source_entity_id")) == str(asset_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "asset_condemned_risk_alerts",
        {
            "asset_id": asset_id,
            "asset_code": asset_data.get("asset_code"),
            "category": asset_data.get("category"),
            "condition": asset_data.get("condition"),
            "status": asset_data.get("status"),
            "alert_level": "warning",
            "risk_status": "active",
            "integration_source": "asset_condemned_queue",
            "source_entity_id": str(asset_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.asset_inventory.condemned_risk_detected",
        aggregate_type="asset_inventory_items",
        aggregate_id=asset_id,
        payload_json={
            "asset_id": asset_id,
            "asset_code": asset_data.get("asset_code"),
            "category": asset_data.get("category"),
            "condition": asset_data.get("condition"),
        },
    )


def _ensure_asset_writeoff_record(depr_record: dict, tenant_id: int) -> None:
    """W26 — Idempotent: create a write-off record when an asset reaches zero current_value.

    Deduplicates by integration_source='asset_depreciation' + source_entity_id (depr record id).
    """
    source_entity_id = str(depr_record.get("id") or "")
    existing = list_entities_for_tenant("asset_writeoff_records", tenant_id)
    already_exists = any(
        str(r.get("integration_source") or "") == "asset_depreciation"
        and str(r.get("source_entity_id") or "") == source_entity_id
        for r in existing
    )
    if already_exists:
        return
    create_entity_for_tenant(
        "asset_writeoff_records",
        {
            "asset_code": str(depr_record.get("asset_code") or ""),
            "depreciation_method": str(depr_record.get("depreciation_method") or ""),
            "original_value": float(depr_record.get("original_value") or 0),
            "current_value": 0.0,
            "status": "written_off",
            "integration_source": "asset_depreciation",
            "source_entity_id": source_entity_id,
            "tenant_id": str(tenant_id),
        },
        tenant_id,
    )


def create_depreciation_record(
    tenant_id: int,
    request: DepreciationRecordCreateSchema,
    actor: str,
) -> DepreciationRecordSchema:
    # W114: Cross-entity guard — asset must be in a depreciable status/condition
    _check_asset_depreciable(
        tenant_id=tenant_id,
        asset_code=request.asset_code,
    )

    assets = list_entities_for_tenant("asset_inventory_items", tenant_id)
    asset_exists = any(
        str(row.get("asset_code") or "").strip() == request.asset_code.strip()
        for row in assets
    )
    if not asset_exists:
        raise ValueError("Asset not found for depreciation record")

    if float(request.current_value) > float(request.original_value):
        raise ValueError("current_value cannot exceed original_value")

    # W26 — cap guard: max active depreciation records per method
    method = str(request.depreciation_method)
    cap = _METHOD_MAX_ACTIVE_DEPR.get(method, 10)
    existing_records = list_entities_for_tenant("asset_depreciation_records", tenant_id)
    active_count = sum(
        1 for r in existing_records
        if str(r.get("depreciation_method") or "") == method
        and str(r.get("status") or "") in _ACTIVE_STATUSES_DEPR
    )
    if active_count >= cap:
        raise ValueError(
            f"Active depreciation records cap exceeded for method '{method}': "
            f"limit={cap}, current={active_count}"
        )

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
    # W26 — side effect: when asset is fully depreciated (current_value=0) → write-off record
    if float(request.current_value) == 0.0:
        _ensure_asset_writeoff_record(created, tenant_id)
    return DepreciationRecordSchema.model_validate(created)
