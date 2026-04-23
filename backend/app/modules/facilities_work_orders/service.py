"""Phase XI-XI1: Facilities Work Orders service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.facilities_work_orders.schemas import (
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
    return WorkOrderSchema.model_validate(created)


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
