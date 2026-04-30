"""Phase XI-XI1: Facilities Work Orders service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.facilities_work_orders.schemas import (
    WO_ALLOWED_TRANSITIONS,
    MaintenanceRequestCreateSchema,
    MaintenanceRequestSchema,
    MaintenanceRequestStatus,
    MaintenanceRequestStatusUpdateSchema,
    WorkOrderCreateSchema,
    WorkOrderPriority,
    WorkOrderSchema,
    WorkOrderStatus,
    WorkOrderStatusUpdateSchema,
    WorkOrderType,
)
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

_PRIORITY_MAX_OPEN: dict[str, int] = {
    "critical": 3,
    "high": 10,
    "medium": 20,
    "low": 50,
}
_OPEN_STATUSES_WO: frozenset[str] = frozenset({"open", "in_progress", "on_hold"})

# ---------------------------------------------------------------------------
# Queue delay caps: max allowed delayed work orders per priority level
# ---------------------------------------------------------------------------
_WORK_ORDER_QUEUE_MAX_DELAYED: dict[str, int] = {
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 20,
}

# ---------------------------------------------------------------------------
# Work order statuses that indicate delayed/overdue state
# ---------------------------------------------------------------------------
_DELAYED_WORK_ORDER_STATUSES: frozenset[str] = frozenset({"on_hold"})

# ---------------------------------------------------------------------------
# Work order statuses that trigger overdue alerts
# ---------------------------------------------------------------------------
_OVERDUE_RISK_STATUSES: frozenset[str] = frozenset({"on_hold"})

# ---------------------------------------------------------------------------
# Work order closure statuses that must pass cross-entity safety validation
# ---------------------------------------------------------------------------
_CLOSURE_STATUSES: frozenset[str] = frozenset({"completed", "cancelled"})

# ---------------------------------------------------------------------------
# Blocking security incident conditions for facility closure decisions
# ---------------------------------------------------------------------------
_BLOCKING_SECURITY_INCIDENT_STATUSES: frozenset[str] = frozenset({"open", "investigating"})
_BLOCKING_SECURITY_INCIDENT_SEVERITIES: frozenset[str] = frozenset({"high", "critical"})

# ---------------------------------------------------------------------------
# W122: cross-entity guard — facility safety check before work order creation
# ---------------------------------------------------------------------------
_FACILITY_SAFE_STATUSES: frozenset[str] = frozenset({"open", "investigating"})
_FACILITY_BLOCKING_SEVERITIES: frozenset[str] = frozenset({"high", "critical"})


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="facilities_work_orders",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _check_facility_clear_for_work_order(*, tenant_id: int, facility_code: str) -> None:
    """W122 fail-closed guard: block work order creation when facility has active high-severity
    security incident.

    5 hardening questions:
    1. Dangerous action      : create_work_order dispatches maintenance technician to facility
    2. Real-world constraint : facilities with active high-severity security incidents are unsafe
    3. External entity       : security_incidents
    4. Validate BEFORE       : create_entity_for_tenant("facilities_work_orders", ...)
    5. Bad outcome prevented : maintenance staff dispatched into an active security incident zone
    """
    normalized = str(facility_code or "").strip()
    if not normalized:
        raise DomainValidationError(
            "Cannot create work order: facility_code is missing or empty — "
            "facility safety validation cannot be enforced"
        )

    try:
        incidents = list_entities_for_tenant("security_incidents", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot create work order for facility_code='{normalized}': "
            "security_incidents lookup failed — facility safety cannot be verified (fail-closed)"
        ) from exc

    blocking_codes: list[str] = []
    for incident in incidents:
        incident_facility = str(incident.get("facility_code") or "").strip().lower()
        if incident_facility != normalized.lower():
            continue
        incident_status = str(incident.get("status") or "").strip().lower()
        incident_severity = str(incident.get("severity") or "").strip().lower()
        if (
            incident_status in _FACILITY_SAFE_STATUSES
            and incident_severity in _FACILITY_BLOCKING_SEVERITIES
        ):
            code = str(incident.get("incident_code") or incident.get("id") or "unknown")
            blocking_codes.append(code)

    if blocking_codes:
        raise DomainValidationError(
            f"Cannot create work order for facility_code='{normalized}': "
            f"active high-severity security incident(s) exist "
            f"({', '.join(blocking_codes)}). Resolve security incidents before dispatching maintenance"
        )


# --- Work Orders ---

def list_work_orders(
    tenant_id: int,
    status: WorkOrderStatus | None = None,
    priority: WorkOrderPriority | None = None,
    work_type: WorkOrderType | None = None,
) -> list[WorkOrderSchema]:
    rows = list_entities_for_tenant("facilities_work_orders", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if priority is not None:
        rows = [r for r in rows if str(r.get("priority") or "") == priority]
    if work_type is not None:
        rows = [r for r in rows if str(r.get("work_type") or "") == work_type]
    return [WorkOrderSchema.model_validate(r) for r in rows]


def get_work_order(tenant_id: int, order_id: int) -> WorkOrderSchema | None:
    rows = list_entities_for_tenant("facilities_work_orders", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == order_id), None)
    if row is None:
        return None
    return WorkOrderSchema.model_validate(row)


def create_work_order(
    tenant_id: int,
    request: WorkOrderCreateSchema,
    actor: str,
) -> WorkOrderSchema:
    # W122 cross-entity guard: verify facility has no active high-severity security incidents
    _check_facility_clear_for_work_order(
        tenant_id=tenant_id,
        facility_code=request.facility_code,
    )

    # SLA cap: limit open work orders per priority.
    cap = _PRIORITY_MAX_OPEN.get(str(request.priority or ""))
    if cap is not None:
        existing_rows = list_entities_for_tenant("facilities_work_orders", tenant_id)
        open_count = sum(
            1 for r in existing_rows
            if str(r.get("priority") or "") == request.priority
            and r.get("status") in _OPEN_STATUSES_WO
        )
        if open_count >= cap:
            raise ValueError(
                f"Open work order SLA cap exceeded for priority '{request.priority}': "
                f"limit={cap}, current={open_count}"
            )

    # Delay queue cap: limit delayed work orders per priority
    delay_cap = _WORK_ORDER_QUEUE_MAX_DELAYED.get(str(request.priority or ""))
    if delay_cap is not None:
        existing_rows = list_entities_for_tenant("facilities_work_orders", tenant_id)
        delayed_count = sum(
            1 for r in existing_rows
            if str(r.get("priority") or "") == request.priority
            and str(r.get("status") or "") in _DELAYED_WORK_ORDER_STATUSES
        )
        if delayed_count >= delay_cap:
            raise ValueError(
                f"work order delay queue cap reached for priority '{request.priority}'"
            )

    created = create_entity_for_tenant(
        "facilities_work_orders",
        {
            "order_code": request.order_code.strip(),
            "facility_code": request.facility_code.strip(),
            "title": request.title.strip(),
            "work_type": request.work_type,
            "priority": request.priority,
            "assigned_to": request.assigned_to,
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("facilities_work_orders", "order", "create"),
        path="/internal/facilities/work-orders",
        metadata={"resource_id": str(created.get("id")), "order_code": request.order_code},
        tenant_id=tenant_id,
    )
    if request.priority == "critical":
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="facilities.work_order.critical_priority",
            aggregate_type="facilities_work_orders",
            aggregate_id=str(created.get("id") or "unknown"),
            payload_json={
                "order_code": request.order_code,
                "facility_code": request.facility_code,
                "priority": request.priority,
            },
        )
    if request.assigned_to:
        _ensure_sla_assignment_record(created, tenant_id)
    return WorkOrderSchema.model_validate(created)


def _ensure_sla_assignment_record(order: dict, tenant_id: int) -> None:
    """Idempotent: create an SLA assignment tracking record when a work order has an assignee."""
    order_id = str(order.get("id") or "")
    existing = list_entities_for_tenant("facilities_sla_assignment_records", tenant_id)
    for row in existing:
        if (
            str(row.get("integration_source") or "") == "facilities_assignment"
            and str(row.get("source_entity_id") or "") == order_id
        ):
            return
    create_entity_for_tenant(
        "facilities_sla_assignment_records",
        {
            "order_id": order_id,
            "order_code": str(order.get("order_code") or ""),
            "facility_code": str(order.get("facility_code") or ""),
            "priority": str(order.get("priority") or ""),
            "assigned_to": str(order.get("assigned_to") or ""),
            "status": "active",
            "integration_source": "facilities_assignment",
            "source_entity_id": order_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_overdue_work_order_alert_record(tenant_id: int, order_id: int, order_data: dict) -> None:
    """Idempotent cross-module side effect: create facilities_overdue_work_order_alerts record.

    Uses integration_source + source_entity_id to prevent duplicates.
    Publishes 'campus.facilities.work_order_overdue_risk_detected' event.
    """
    existing = [
        r for r in list_entities_for_tenant("facilities_overdue_work_order_alerts", tenant_id)
        if str(r.get("integration_source")) == "facilities_overdue_queue"
        and str(r.get("source_entity_id")) == str(order_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "facilities_overdue_work_order_alerts",
        {
            "order_id": order_id,
            "order_code": order_data.get("order_code"),
            "facility_code": order_data.get("facility_code"),
            "priority": order_data.get("priority"),
            "status": order_data.get("status"),
            "alert_level": "warning",
            "risk_status": "active",
            "integration_source": "facilities_overdue_queue",
            "source_entity_id": str(order_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.facilities.work_order_overdue_risk_detected",
        aggregate_type="facilities_work_orders",
        aggregate_id=order_id,
        payload_json={
            "order_id": order_id,
            "order_code": order_data.get("order_code"),
            "facility_code": order_data.get("facility_code"),
            "priority": order_data.get("priority"),
        },
    )


def _check_no_blocking_security_incidents(
    *,
    tenant_id: int,
    order_id: int,
    facility_code: str | None,
    target_status: str,
) -> None:
    """Fail-closed guard for work order closure under active security incidents.

    Closing (completed/cancelled) a facilities work order is blocked when the same
    facility has active high-severity security incidents.
    """
    if target_status not in _CLOSURE_STATUSES:
        return

    facility = str(facility_code or "").strip()
    if not facility:
        raise DomainValidationError(
            f"Cannot transition work order {order_id} to '{target_status}': "
            "facility_code is missing, safety incident validation cannot be enforced"
        )

    try:
        incidents = list_entities_for_tenant("security_incidents", tenant_id)
    except Exception as exc:  # pragma: no cover - exercised in tests via monkeypatch
        raise DomainValidationError(
            "Cannot transition work order to closed state: security_incidents query failed. "
            "Safety validation must be enforced before closure"
        ) from exc

    blocking_codes: list[str] = []
    normalized_facility = facility.lower()
    for incident in incidents:
        incident_facility = str(incident.get("facility_code") or "").strip().lower()
        if incident_facility != normalized_facility:
            continue
        incident_status = str(incident.get("status") or "").strip().lower()
        incident_severity = str(incident.get("severity") or "").strip().lower()
        if (
            incident_status in _BLOCKING_SECURITY_INCIDENT_STATUSES
            and incident_severity in _BLOCKING_SECURITY_INCIDENT_SEVERITIES
        ):
            code = str(incident.get("incident_code") or incident.get("id") or "unknown")
            blocking_codes.append(code)

    if blocking_codes:
        raise DomainValidationError(
            f"Cannot transition work order {order_id} to '{target_status}' for facility '{facility}': "
            "active high-severity security incidents exist "
            f"({', '.join(blocking_codes)}). Resolve incidents before closure"
        )


def update_work_order_status(
    tenant_id: int,
    order_id: int,
    request: WorkOrderStatusUpdateSchema,
    actor: str,
) -> WorkOrderSchema | None:
    rows = list_entities_for_tenant("facilities_work_orders", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == order_id), None)
    if existing is None:
        return None
    current_status = str(existing.get("status") or "open")
    allowed = WO_ALLOWED_TRANSITIONS.get(current_status, [])
    if request.status not in allowed:
        raise ValueError(
            f"Transition from '{current_status}' to '{request.status}' is not allowed. "
            f"Allowed: {allowed}"
        )

    _check_no_blocking_security_incidents(
        tenant_id=tenant_id,
        order_id=order_id,
        facility_code=str(existing.get("facility_code") or ""),
        target_status=request.status,
    )

    updated = update_entity_for_tenant(
        "facilities_work_orders", order_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("facilities_work_orders", "order", "status_update"),
        path=f"/internal/facilities/work-orders/{order_id}/status",
        metadata={"resource_id": str(order_id), "new_status": request.status},
        tenant_id=tenant_id,
    )

    # Trigger overdue alert if status transitions to risk set
    if request.status in _OVERDUE_RISK_STATUSES:
        _ensure_overdue_work_order_alert_record(tenant_id, order_id, dict(updated))

    return WorkOrderSchema.model_validate(updated)


# --- Maintenance Requests ---

def list_maintenance_requests(
    tenant_id: int,
    status: MaintenanceRequestStatus | None = None,
) -> list[MaintenanceRequestSchema]:
    rows = list_entities_for_tenant("facilities_maintenance_requests", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [MaintenanceRequestSchema.model_validate(r) for r in rows]


def get_maintenance_request(tenant_id: int, req_id: int) -> MaintenanceRequestSchema | None:
    rows = list_entities_for_tenant("facilities_maintenance_requests", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == req_id), None)
    if row is None:
        return None
    return MaintenanceRequestSchema.model_validate(row)


def create_maintenance_request(
    tenant_id: int,
    request: MaintenanceRequestCreateSchema,
    actor: str,
) -> MaintenanceRequestSchema:
    created = create_entity_for_tenant(
        "facilities_maintenance_requests",
        {
            "request_code": request.request_code.strip(),
            "facility_code": request.facility_code.strip(),
            "issue_type": request.issue_type,
            "severity": request.severity,
            "notes": request.notes,
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("facilities_work_orders", "maintenance_request", "create"),
        path="/internal/facilities/maintenance-requests",
        metadata={"resource_id": str(created.get("id")), "request_code": request.request_code},
        tenant_id=tenant_id,
    )
    return MaintenanceRequestSchema.model_validate(created)


def update_maintenance_request_status(
    tenant_id: int,
    req_id: int,
    request: MaintenanceRequestStatusUpdateSchema,
    actor: str,
) -> MaintenanceRequestSchema | None:
    rows = list_entities_for_tenant("facilities_maintenance_requests", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == req_id), None)
    if existing is None:
        return None
    updated = update_entity_for_tenant(
        "facilities_maintenance_requests", req_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("facilities_work_orders", "maintenance_request", "status_update"),
        path=f"/internal/facilities/maintenance-requests/{req_id}/status",
        metadata={"resource_id": str(req_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return MaintenanceRequestSchema.model_validate(updated)
