from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.procurement.schemas import (
    AssetCreateSchema,
    AssetSchema,
    ContractCreateSchema,
    ContractSchema,
    ContractStatusUpdateSchema,
    InventoryItemCreateSchema,
    InventoryItemSchema,
    ProcurementHealthSnapshotSchema,
    VendorCreateSchema,
    VendorSchema,
    # A-009 Phase 2.3: Request lifecycle schemas
    ApprovalStepSchema,
    ProcurementAuditEntrySchema,
    ProcurementDashboardSummarySchema,
    ProcurementListItemSchema,
    ProcurementOrderCreateSchema,
    ProcurementOrderSchema,
    ProcurementRequestCreateSchema,
    ProcurementRequestSchema,
    ProcurementRequestUpdateSchema,
    ProcurementStatusUpdateSchema,
)
from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import create_entity_for_tenant, list_entities_for_tenant, update_entity_for_tenant


# W111: vendor statuses that allow receiving new contracts
_VENDOR_ACTIVE_FOR_CONTRACT: frozenset[str] = frozenset({"active"})


_PO_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"SUBMITTED"},
    "SUBMITTED": {"APPROVED", "REJECTED"},
    "APPROVED": {"PO_ISSUED"},
    "REJECTED": set(),
    "PO_ISSUED": {"DELIVERED"},
    "DELIVERED": set(),
}

# W34: cap on active vendors per category
_VENDOR_CATEGORY_MAX_ACTIVE: dict[str, int] = {
    "it": 10,
    "facilities": 8,
    "catering": 5,
    "construction": 6,
    "logistics": 7,
    "other": 15,
}

_ACTIVE_VENDOR_STATUSES: frozenset[str] = frozenset({"active", "under_review"})

# W34: risk threshold for procurement alerts
_HIGH_RISK_SCORE_THRESHOLD: float = 0.8

_PO_STATUS_ALIASES: dict[str, str] = {
    "draft": "DRAFT",
    "submitted": "SUBMITTED",
    "approved": "APPROVED",
    "rejected": "REJECTED",
    "po_issued": "PO_ISSUED",
    "delivered": "DELIVERED",
}


def _emit_procurement_event(*, tenant_id: int, event_type: str, aggregate_id: int, payload: dict) -> None:
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_type="procurement_contract",
            aggregate_id=aggregate_id,
            payload_json=payload,
        )
    except Exception:  # noqa: BLE001 - events must never break primary business flow
        pass


def _check_vendor_active_for_contract(
    *,
    tenant_id: int,
    vendor_code: str,
) -> None:
    """Cross-entity guard: procurement_contracts × procurement_vendors by vendor_code.

    A contract may only be created when the referenced vendor exists in
    procurement_vendors AND has status 'active'. Contracting with non-existent
    or inactive vendors creates financial obligations without a valid counterparty,
    enables procurement fraud, and corrupts Brain Core vendor risk analytics.

    FAIL-CLOSED: If vendor lookup fails (any exception), contract creation is
    BLOCKED. Cannot bind financial commitment without verifying counterparty.
    """
    try:
        all_vendors = list_entities_for_tenant("procurement_vendors", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Contract creation blocked for vendor_code='{vendor_code}': "
            f"procurement_vendors lookup failed — {exc}. Cannot verify vendor."
        ) from exc

    matching = [
        v for v in all_vendors
        if str(v.get("vendor_code") or "").strip().lower()
        == str(vendor_code).strip().lower()
    ]

    if not matching:
        raise DomainValidationError(
            f"Contract creation blocked: vendor_code='{vendor_code}' not found in "
            f"procurement_vendors. Cannot bind financial commitment to unknown vendor."
        )

    vendor = matching[0]
    vendor_status = str(vendor.get("status") or "").strip().lower()
    if vendor_status not in _VENDOR_ACTIVE_FOR_CONTRACT:
        raise DomainValidationError(
            f"Contract creation blocked: vendor_code='{vendor_code}' has status "
            f"'{vendor_status}' — only 'active' vendors may receive new contracts. "
            f"Contracting with inactive/under_review vendors bypasses procurement controls."
        )


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


def _normalize_po_status(status: object) -> str:
    raw = str(status or "").strip()
    if raw in _PO_ALLOWED_TRANSITIONS:
        return raw
    mapped = _PO_STATUS_ALIASES.get(raw.lower())
    if mapped is not None:
        return mapped
    raise ValueError(f"Unsupported PO status '{status}'")


def list_vendors(tenant_id: int) -> list[VendorSchema]:
    rows = list_entities_for_tenant("procurement_vendors", tenant_id)
    return [VendorSchema.model_validate(r) for r in rows]


def _ensure_risk_alert_record(
    tenant_id: int,
    contract_id: int,
    contract_data: dict,
) -> None:
    """Idempotent: create a procurement_risk_alerts entry when a high-risk contract is created."""
    existing = list_entities_for_tenant("procurement_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "procurement_risk"
            and str(rec.get("source_entity_id")) == str(contract_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "procurement_risk_alerts",
        {
            "contract_id": contract_id,
            "vendor_code": str(contract_data.get("vendor_code") or ""),
            "risk_score": float(contract_data.get("risk_score") or 0.0),
            "alert_status": "open",
            "integration_source": "procurement_risk",
            "source_entity_id": str(contract_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def create_vendor(tenant_id: int, request: VendorCreateSchema, actor: str) -> VendorSchema:
    category_key = request.category.strip().lower()
    cap = _VENDOR_CATEGORY_MAX_ACTIVE.get(category_key, _VENDOR_CATEGORY_MAX_ACTIVE["other"])
    existing_vendors = list_entities_for_tenant("procurement_vendors", tenant_id)
    active_count = sum(
        1
        for v in existing_vendors
        if str(v.get("category") or "").strip().lower() == category_key
        and str(v.get("status") or "") in _ACTIVE_VENDOR_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active vendor cap ({cap}) reached for category '{category_key}'"
        )

    created = create_entity_for_tenant(
        "procurement_vendors",
        {
            "vendor_code": request.vendor_code.strip(),
            "name": request.name.strip(),
            "category": request.category.strip(),
            "sla_breach_rate": float(request.sla_breach_rate),
            "on_time_delivery_rate": float(request.on_time_delivery_rate),
            "status": request.status,
            "contact_name": str(request.contact_name or ""),
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
    # W111: Cross-entity guard — vendor must exist and be active before contract creation
    _check_vendor_active_for_contract(
        tenant_id=tenant_id,
        vendor_code=request.vendor_code,
    )

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

    if float(request.risk_score) >= _HIGH_RISK_SCORE_THRESHOLD:
        _ensure_risk_alert_record(
            tenant_id=tenant_id,
            contract_id=int(created.get("id") or 0),
            contract_data={
                "vendor_code": request.vendor_code,
                "risk_score": float(request.risk_score),
            },
        )

    contract_id = int(created.get("id") or 0)
    _emit_procurement_event(
        tenant_id=tenant_id,
        event_type="procurement.request_created",
        aggregate_id=contract_id,
        payload={
            "contract_id": contract_id,
            "contract_code": request.contract_code,
            "vendor_code": request.vendor_code,
            "status": str(request.status),
            "actor": actor,
        },
    )

    return ContractSchema.model_validate(created)


def update_contract_status(
    tenant_id: int,
    contract_id: int,
    request: ContractStatusUpdateSchema,
    actor: str,
) -> ContractSchema | None:
    rows = list_entities_for_tenant("procurement_contracts", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == contract_id), None)
    if existing is None:
        return None

    current_status = _normalize_po_status(existing.get("status") or "DRAFT")
    next_status = _normalize_po_status(request.status)
    if next_status not in _PO_ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"Invalid PO transition from '{current_status}' to '{next_status}'")

    # W70: block approval if vendor SLA breach rate is at or above threshold
    if next_status == "APPROVED":
        vendor_code = str(existing.get("vendor_code") or "").strip()
        if vendor_code:
            vendor_rows = list_entities_for_tenant("procurement_vendors", tenant_id)
            vendor = next(
                (v for v in vendor_rows if str(v.get("vendor_code") or "").strip() == vendor_code),
                None,
            )
            if vendor is not None:
                vendor_sla = float(vendor.get("sla_breach_rate") or 0.0)
                if vendor_sla >= _HIGH_RISK_SCORE_THRESHOLD:
                    raise ValueError(
                        f"Cannot approve contract: vendor '{vendor_code}' has SLA breach rate "
                        f"{vendor_sla:.0%} (threshold {_HIGH_RISK_SCORE_THRESHOLD:.0%}). "
                        "Resolve vendor SLA issues before approving."
                    )

    asset_delivery_result: dict | None = None
    # A-015.3: asset inventory registration is delivery-based, not PO-issued.
    if next_status == "DELIVERED":
        asset_delivery_result = _ensure_asset_inventory_registration_for_po_delivery(
            {**existing, "status": "DELIVERED"},
            tenant_id,
            actor,
        )

    updated = update_entity_for_tenant(
        "procurement_contracts",
        contract_id,
        {**existing, "status": next_status},
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("procurement", "contract", "status_update"),
        path=f"/internal/procurement/contracts/{contract_id}/status",
        metadata={
            "resource_id": str(contract_id),
            "old_status": current_status,
            "new_status": next_status,
            "asset_code": (asset_delivery_result or {}).get("asset_code"),
            "asset_created": (asset_delivery_result or {}).get("created"),
        },
        tenant_id=tenant_id,
    )

    event_map = {
        "APPROVED": "procurement.approved",
        "REJECTED": "procurement.rejected",
        "PO_ISSUED": "procurement.po_issued",
        "DELIVERED": "procurement.delivered",
    }
    event_type = event_map.get(next_status)
    if event_type is not None:
        _emit_procurement_event(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_id=contract_id,
            payload={
                "contract_id": contract_id,
                "contract_code": str(existing.get("contract_code") or ""),
                "old_status": current_status,
                "new_status": next_status,
                "actor": actor,
            },
        )

    return ContractSchema.model_validate(updated)


def _ensure_asset_inventory_registration_for_po_delivery(
    contract: dict,
    tenant_id: int,
    actor: str,
) -> dict:
    """Ensure a delivered procurement contract is represented in asset inventory.

    This is fail-closed: a DELIVERED transition is blocked if asset inventory
    lookup or creation cannot be completed.
    """
    if not tenant_id:
        raise DomainValidationError(
            "Cannot record delivery: tenant_id is required for asset inventory registration"
        )

    contract_id = _to_int(contract.get("id"))
    if contract_id is None:
        raise DomainValidationError(
            "Cannot record delivery: contract id is missing; asset lineage cannot be enforced"
        )

    contract_code = str(contract.get("contract_code") or "").strip()
    if not contract_code:
        raise DomainValidationError(
            "Cannot record delivery: contract_code is missing; "
            "asset inventory registration cannot be enforced"
        )

    asset_code = f"PROC-{contract_code}"[:64]

    try:
        inventory_rows = list_entities_for_tenant("asset_inventory_items", tenant_id)
    except Exception as exc:  # pragma: no cover - tested via monkeypatch
        raise DomainValidationError(
            "Cannot record delivery: asset_inventory lookup failed. "
            "Registration must be verified before DELIVERED"
        ) from exc

    already_registered = next(
        (
            row for row in inventory_rows
            if str(row.get("asset_code") or "").strip() == asset_code
        ),
        None,
    )
    if already_registered is not None:
        return {
            "created": False,
            "asset_code": asset_code,
            "asset_id": _to_int(already_registered.get("id")),
            "contract_id": contract_id,
            "contract_code": contract_code,
        }

    try:
        from datetime import datetime  # noqa: PLC0415
        from app.modules.asset_inventory.schemas import AssetItemCreateSchema  # noqa: PLC0415
        from app.modules.asset_inventory.service import create_asset_item  # noqa: PLC0415

        title = str(contract.get("title") or "Procured Asset")
        vendor_code = str(contract.get("vendor_code") or "")

        created_item = create_asset_item(
            tenant_id=tenant_id,
            request=AssetItemCreateSchema(
                asset_code=asset_code,
                name=title[:200],
                category="equipment",
                location="receiving",
                condition="good",
                purchase_year=datetime.now().year,
                vendor=vendor_code[:128] if vendor_code else None,
                status="active",
            ),
            actor=actor,
        )
    except Exception as exc:  # pragma: no cover - tested via monkeypatch
        raise DomainValidationError(
            f"Cannot record delivery for contract '{contract_code}': "
            "asset inventory registration failed"
        ) from exc

    created_asset_id = _to_int(getattr(created_item, "id", None))
    _emit_audit(
        actor=actor,
        action=build_audit_action("procurement", "asset", "create"),
        path=f"/internal/procurement/contracts/{contract_id}/delivery",
        metadata={
            "resource_id": str(contract_id),
            "contract_id": contract_id,
            "contract_code": contract_code,
            "asset_id": created_asset_id,
            "asset_code": asset_code,
            "delivery_status": "DELIVERED",
            "origin_event": "procurement.delivered",
        },
        tenant_id=tenant_id,
    )
    _emit_procurement_event(
        tenant_id=tenant_id,
        event_type="procurement.asset_created",
        aggregate_id=contract_id,
        payload={
            "contract_id": contract_id,
            "contract_code": contract_code,
            "asset_id": created_asset_id,
            "asset_code": asset_code,
            "vendor_code": str(contract.get("vendor_code") or ""),
            "delivery_status": "DELIVERED",
            "source_entity_type": "procurement_contract",
            "source_entity_id": str(contract_id),
        },
    )
    return {
        "created": True,
        "asset_code": asset_code,
        "asset_id": created_asset_id,
        "contract_id": contract_id,
        "contract_code": contract_code,
    }


def _ensure_asset_inventory_registration_for_po_issue(
    contract: dict,
    tenant_id: int,
    actor: str,
) -> None:
    """Backward-compatible wrapper kept for older tests and references.

    A-015.3 moves operational asset creation to the DELIVERED transition.
    """
    _ensure_asset_inventory_registration_for_po_delivery(
        {**contract, "status": "DELIVERED"},
        tenant_id,
        actor,
    )



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


# ─── A-009 Phase 2.3: Request lifecycle (in-memory store, tenant-scoped) ─────

import threading as _threading
import uuid as _uuid
from datetime import datetime as _dt, timezone as _tz

_requests_lock = _threading.Lock()
_requests_store: dict[str, dict] = {}
_orders_store: dict[str, dict] = {}
_approvals_store: dict[str, list[dict]] = {}
_audit_store: dict[str, list[dict]] = {}

_REQUEST_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"under_review", "cancelled"},
    "under_review": {"approved", "rejected"},
    "approved": {"ordered", "cancelled"},
    "rejected": set(),
    "ordered": {"fulfilled", "cancelled"},
    "fulfilled": set(),
    "cancelled": set(),
}


def _now_iso() -> str:
    return _dt.now(_tz.utc).isoformat()


def _request_key(tenant_id: int, request_id: str) -> str:
    return f"{tenant_id}:{request_id}"


def _gen_request_number(tenant_id: int) -> str:
    with _requests_lock:
        count = sum(1 for k in _requests_store if k.startswith(f"{tenant_id}:"))
    return f"PR-{tenant_id}-{count + 1:05d}"


def _append_audit(request_id: str, *, actor_id: str, action: str,
                  from_status: str | None = None, to_status: str | None = None,
                  metadata: dict | None = None) -> None:
    entry = {
        "audit_id": str(_uuid.uuid4()),
        "request_id": request_id,
        "action": action,
        "actor_id": actor_id,
        "actor_name": actor_id,
        "from_status": from_status,
        "to_status": to_status,
        "timestamp": _now_iso(),
        "metadata": metadata or {},
    }
    _audit_store.setdefault(request_id, []).append(entry)


def _to_list_item(req: dict) -> ProcurementListItemSchema:
    return ProcurementListItemSchema(
        request_id=req["request_id"],
        request_number=req["request_number"],
        title=req["title"],
        requester_name=req["requester_name"],
        department_name=req.get("department_name", req.get("department_id", "")),
        status=req["status"],
        priority=req["priority"],
        estimated_total=req["estimated_total"],
        created_at=req["created_at"],
        updated_at=req["updated_at"],
    )


def create_procurement_request(
    tenant_id: int, payload: ProcurementRequestCreateSchema, actor: str
) -> ProcurementRequestSchema:
    request_id = str(_uuid.uuid4())
    now = _now_iso()
    estimated_total = sum(i.quantity * i.unit_price for i in payload.items)
    req = {
        "request_id": request_id,
        "request_number": _gen_request_number(tenant_id),
        "requester_id": actor,
        "requester_name": actor,
        "department_id": payload.department_id,
        "department_name": payload.department_id,
        "title": payload.title,
        "description": payload.description,
        "status": "draft",
        "priority": payload.priority,
        "estimated_total": estimated_total,
        "currency": "KZT",
        "needed_by_date": payload.needed_by_date,
        "created_at": now,
        "updated_at": now,
        "submitted_at": None,
        "tenant_id": tenant_id,
    }
    with _requests_lock:
        _requests_store[_request_key(tenant_id, request_id)] = req
    _append_audit(request_id, actor_id=actor, action="created", to_status="draft")
    return ProcurementRequestSchema.model_validate(req)


def list_procurement_requests(
    tenant_id: int,
    status: str | None = None,
    requester_id: str | None = None,
) -> list[ProcurementListItemSchema]:
    with _requests_lock:
        rows = [v for k, v in _requests_store.items() if v.get("tenant_id") == tenant_id]
    if status:
        rows = [r for r in rows if r["status"] == status]
    if requester_id:
        rows = [r for r in rows if r["requester_id"] == requester_id]
    return [_to_list_item(r) for r in rows]


def get_procurement_request(tenant_id: int, request_id: str) -> ProcurementRequestSchema | None:
    req = _requests_store.get(_request_key(tenant_id, request_id))
    if req is None:
        return None
    return ProcurementRequestSchema.model_validate(req)


def update_procurement_request(
    tenant_id: int, request_id: str, payload: ProcurementRequestUpdateSchema, actor: str
) -> ProcurementRequestSchema | None:
    key = _request_key(tenant_id, request_id)
    with _requests_lock:
        req = _requests_store.get(key)
        if req is None:
            return None
        if payload.title is not None:
            req["title"] = payload.title
        if payload.description is not None:
            req["description"] = payload.description
        if payload.priority is not None:
            req["priority"] = payload.priority
        if payload.needed_by_date is not None:
            req["needed_by_date"] = payload.needed_by_date
        req["updated_at"] = _now_iso()
        _requests_store[key] = req
    _append_audit(request_id, actor_id=actor, action="updated")
    return ProcurementRequestSchema.model_validate(req)


def submit_procurement_request(tenant_id: int, request_id: str, actor: str) -> ProcurementRequestSchema | None:
    key = _request_key(tenant_id, request_id)
    with _requests_lock:
        req = _requests_store.get(key)
        if req is None:
            return None
        if req["status"] not in _REQUEST_STATUS_TRANSITIONS or "submitted" not in _REQUEST_STATUS_TRANSITIONS[req["status"]]:
            raise ValueError(f"Cannot submit request with status '{req['status']}'")
        from_status = req["status"]
        now = _now_iso()
        req["status"] = "submitted"
        req["submitted_at"] = now
        req["updated_at"] = now
        _requests_store[key] = req
    _append_audit(request_id, actor_id=actor, action="submitted", from_status=from_status, to_status="submitted")
    # A-015.2 — emit Brain Core signal for approval automation
    _emit_procurement_event(
        tenant_id=tenant_id,
        event_type="procurement.request_submitted",
        aggregate_id=tenant_id,
        payload={
            "request_id": request_id,
            "department_id": req.get("department_id"),
            "title": req.get("title"),
            "estimated_total": req.get("estimated_total"),
            "priority": req.get("priority"),
            "status": "submitted",
            "source_entity_type": "procurement_request",
            "source_entity_id": request_id,
        },
    )
    return ProcurementRequestSchema.model_validate(req)


def update_procurement_status(
    tenant_id: int, request_id: str, payload: ProcurementStatusUpdateSchema, actor: str
) -> ProcurementRequestSchema | None:
    key = _request_key(tenant_id, request_id)
    with _requests_lock:
        req = _requests_store.get(key)
        if req is None:
            return None
        current = req["status"]
        allowed = _REQUEST_STATUS_TRANSITIONS.get(current, set())
        if payload.status not in allowed:
            raise ValueError(f"Transition '{current}' → '{payload.status}' is not allowed")
        from_status = current
        req["status"] = payload.status
        req["updated_at"] = _now_iso()
        _requests_store[key] = req
    _append_audit(request_id, actor_id=actor, action="status_changed",
                  from_status=from_status, to_status=payload.status,
                  metadata={"comment": payload.comment})
    # A-015.2 — emit events for approval lifecycle transitions
    if payload.status in {"approved", "rejected"}:
        _emit_procurement_event(
            tenant_id=tenant_id,
            event_type=f"procurement.{payload.status}",
            aggregate_id=tenant_id,
            payload={
                "request_id": request_id,
                "status": payload.status,
                "actor": actor,
                "comment": payload.comment,
                "source_entity_type": "procurement_request",
                "source_entity_id": request_id,
            },
        )
    return ProcurementRequestSchema.model_validate(req)


def get_approval_steps(tenant_id: int, request_id: str) -> list[ApprovalStepSchema]:
    # Ensure request belongs to this tenant
    req = _requests_store.get(_request_key(tenant_id, request_id))
    if req is None:
        return []
    steps = _approvals_store.get(request_id, [])
    # Auto-generate default approval chain if empty
    if not steps:
        steps = [
            {
                "step_id": str(_uuid.uuid4()),
                "request_id": request_id,
                "sequence": 1,
                "approver_id": "dept_head",
                "approver_name": "Department Head",
                "status": "pending",
                "decision_at": None,
                "comment": None,
            },
            {
                "step_id": str(_uuid.uuid4()),
                "request_id": request_id,
                "sequence": 2,
                "approver_id": "finance_director",
                "approver_name": "Finance Director",
                "status": "pending",
                "decision_at": None,
                "comment": None,
            },
        ]
        _approvals_store[request_id] = steps
    return [ApprovalStepSchema.model_validate(s) for s in steps]


def get_audit_trail(tenant_id: int, request_id: str) -> list[ProcurementAuditEntrySchema]:
    req = _requests_store.get(_request_key(tenant_id, request_id))
    if req is None:
        return []
    entries = _audit_store.get(request_id, [])
    return [ProcurementAuditEntrySchema.model_validate(e) for e in entries]


def get_request_order(tenant_id: int, request_id: str) -> ProcurementOrderSchema | None:
    req = _requests_store.get(_request_key(tenant_id, request_id))
    if req is None:
        return None
    for order in _orders_store.values():
        if order["request_id"] == request_id and order.get("tenant_id") == tenant_id:
            return ProcurementOrderSchema.model_validate(order)
    return None


def create_procurement_order(
    tenant_id: int, payload: ProcurementOrderCreateSchema, actor: str
) -> ProcurementOrderSchema:
    order_id = str(_uuid.uuid4())
    now = _now_iso()
    # Resolve vendor name
    vendor_rows = list_entities_for_tenant("procurement_vendors", tenant_id)
    vendor_name = payload.vendor_id
    for v in vendor_rows:
        if str(v.get("id")) == payload.vendor_id or v.get("vendor_code") == payload.vendor_id:
            vendor_name = str(v.get("name", payload.vendor_id))
            break
    # Calculate total from linked request items
    total_amount = 0.0
    req = _requests_store.get(_request_key(tenant_id, payload.request_id))
    if req:
        total_amount = float(req.get("estimated_total", 0))
    order = {
        "order_id": order_id,
        "request_id": payload.request_id,
        "vendor_id": payload.vendor_id,
        "vendor_name": vendor_name,
        "order_number": payload.order_number,
        "order_date": now,
        "expected_delivery_date": payload.expected_delivery_date,
        "total_amount": total_amount,
        "currency": "KZT",
        "status": "issued",
        "tenant_id": tenant_id,
    }
    _orders_store[order_id] = order
    _append_audit(payload.request_id, actor_id=actor, action="order_created",
                  metadata={"order_id": order_id, "order_number": payload.order_number})
    # A-015.2 — emit po_issued event
    _emit_procurement_event(
        tenant_id=tenant_id,
        event_type="procurement.po_issued",
        aggregate_id=tenant_id,
        payload={
            "request_id": payload.request_id,
            "order_id": order_id,
            "order_number": payload.order_number,
            "vendor_id": payload.vendor_id,
            "total_amount": total_amount,
            "source_entity_type": "procurement_order",
            "source_entity_id": order_id,
        },
    )
    return ProcurementOrderSchema.model_validate(order)


def fulfill_procurement_request(tenant_id: int, request_id: str, actor: str) -> ProcurementOrderSchema | None:
    key = _request_key(tenant_id, request_id)
    with _requests_lock:
        req = _requests_store.get(key)
        if req is None:
            return None
        allowed = _REQUEST_STATUS_TRANSITIONS.get(req["status"], set())
        if "fulfilled" not in allowed:
            raise ValueError(f"Cannot fulfill request with status '{req['status']}'")
        from_status = req["status"]
        req["status"] = "fulfilled"
        req["updated_at"] = _now_iso()
        _requests_store[key] = req
    _append_audit(request_id, actor_id=actor, action="fulfilled",
                  from_status=from_status, to_status="fulfilled")
    return get_request_order(tenant_id, request_id)


def get_procurement_dashboard_summary(tenant_id: int) -> ProcurementDashboardSummarySchema:
    with _requests_lock:
        rows = [v for v in _requests_store.values() if v.get("tenant_id") == tenant_id]
    status_breakdown: dict[str, int] = {
        "draft": 0, "submitted": 0, "under_review": 0,
        "approved": 0, "rejected": 0, "ordered": 0, "fulfilled": 0,
    }
    total_ordered_value = 0.0
    overdue = 0
    now_str = _now_iso()
    for r in rows:
        s = r.get("status", "draft")
        if s in status_breakdown:
            status_breakdown[s] += 1
        if s == "ordered":
            total_ordered_value += float(r.get("estimated_total", 0))
        nbd = r.get("needed_by_date")
        if nbd and s not in ("fulfilled", "cancelled", "rejected") and nbd < now_str:
            overdue += 1
    pending_approvals = sum(1 for r in rows if r.get("status") in ("submitted", "under_review"))
    return ProcurementDashboardSummarySchema(
        total_requests=len(rows),
        status_breakdown=status_breakdown,
        total_pending_approvals=pending_approvals,
        total_ordered_value=total_ordered_value,
        overdue_requests=overdue,
        last_updated=_now_iso(),
    )


# ---------------------------------------------------------------------------
# A-015.2 — Procurement Approval Automation helpers
# ---------------------------------------------------------------------------


def ensure_procurement_approval_action(
    tenant_id: int, request_id: str, actor: str
) -> dict:
    """Idempotently transition a submitted procurement request to under_review
    and ensure its approval steps exist.

    Returns ``{"idempotent": False, "steps": [...]}`` on first call and
    ``{"idempotent": True, "steps": [...]}`` if already under_review or further.

    Raises ValueError if tenant_id is invalid or the request is not found.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    req_data = _requests_store.get(_request_key(tenant_id, request_id))
    if req_data is None:
        raise ValueError(f"Procurement request '{request_id}' not found for tenant {tenant_id}")

    already_progressed = req_data["status"] in {"under_review", "approved", "rejected", "ordered", "fulfilled", "cancelled"}
    if already_progressed:
        steps = get_approval_steps(tenant_id, request_id)
        return {"idempotent": True, "steps": [s.model_dump() for s in steps]}

    # Transition submitted → under_review
    update_procurement_status(
        tenant_id,
        request_id,
        ProcurementStatusUpdateSchema(status="under_review"),
        actor,
    )
    steps = get_approval_steps(tenant_id, request_id)
    return {"idempotent": False, "steps": [s.model_dump() for s in steps]}


def ensure_po_on_approved_request(
    tenant_id: int, request_id: str, actor: str
) -> dict | None:
    """Idempotently create a PO order for an approved procurement request.

    Returns the order dict (new or existing) or None if the request is not in
    ``approved`` status (e.g. rejected).  Does NOT raise for non-approved status
    so that callers can treat the None result as a no-op.

    Raises ValueError if tenant_id is invalid or request is not found.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    req_data = _requests_store.get(_request_key(tenant_id, request_id))
    if req_data is None:
        raise ValueError(f"Procurement request '{request_id}' not found for tenant {tenant_id}")

    if req_data["status"] != "approved":
        return None

    # Idempotency check — return existing order if already issued
    existing = get_request_order(tenant_id, request_id)
    if existing is not None:
        return {"order_id": existing.order_id, "idempotent": True, "order": existing.model_dump()}

    # Auto-generate a PO order number
    order_number = f"PO-{tenant_id}-{request_id[:8].upper()}"
    order = create_procurement_order(
        tenant_id,
        ProcurementOrderCreateSchema(
            request_id=request_id,
            vendor_id="system",
            order_number=order_number,
        ),
        actor,
    )
    return {"order_id": order.order_id, "idempotent": False, "order": order.model_dump()}