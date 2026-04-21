from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.housing.schemas import (
    HousingRequestCreateSchema,
    HousingRequestSchema,
    HousingRequestStatus,
    HousingRequestStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "submitted": {"in_review", "approved", "rejected"},
    "in_review": {"approved", "rejected"},
    "approved": {"completed"},
    "rejected": set(),
    "completed": set(),
}


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="housing_request",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_housing_requests(
    tenant_id: int,
    status: HousingRequestStatus | None = None,
    student_id: int | None = None,
) -> list[HousingRequestSchema]:
    rows = list_entities_for_tenant("housing_requests", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [HousingRequestSchema.model_validate(r) for r in rows]


def create_housing_request(
    tenant_id: int,
    request: HousingRequestCreateSchema,
    actor: str,
) -> HousingRequestSchema:
    created = create_entity_for_tenant(
        "housing_requests",
        {
            "student_id": int(request.student_id),
            "request_type": request.request_type,
            "dormitory": request.dormitory.strip(),
            "room_preference": (request.room_preference or "any").strip() or "any",
            "status": "submitted",
            "manager_id": (request.manager_id or "housing-office").strip() or "housing-office",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("housing", "request", "create"),
        path="/internal/housing/requests",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "request_type": request.request_type,
        },
        tenant_id=tenant_id,
    )
    return HousingRequestSchema.model_validate(created)


def update_housing_request_status(
    tenant_id: int,
    request_id: int,
    payload: HousingRequestStatusUpdateSchema,
    actor: str,
) -> HousingRequestSchema:
    rows = list_entities_for_tenant("housing_requests", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == request_id), None)
    if existing is None:
        raise ValueError(f"request {request_id} not found")

    current_status = str(existing.get("status") or "submitted")
    if payload.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{payload.status}' is not allowed")

    updated = update_entity_for_tenant(
        "housing_requests",
        request_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "request_type": str(existing.get("request_type") or "assignment"),
            "dormitory": str(existing.get("dormitory") or "unknown"),
            "room_preference": str(existing.get("room_preference") or "any"),
            "status": payload.status,
            "manager_id": str(existing.get("manager_id") or "housing-office"),
            "notes": (payload.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("housing", "request", "status_update"),
        path=f"/internal/housing/requests/{request_id}/status",
        metadata={
            "resource_id": str(request_id),
            "old_status": current_status,
            "new_status": payload.status,
        },
        tenant_id=tenant_id,
    )
    return HousingRequestSchema.model_validate(updated)
