from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
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

# Maximum simultaneous active (submitted/in_review/approved) requests per student per request_type
_REQUEST_TYPE_MAX_ACTIVE: dict[str, int] = {
    "assignment": 1,
    "transfer": 2,
    "maintenance": 3,
    "checkout": 1,
}

_ACTIVE_REQUEST_STATUSES: frozenset[str] = frozenset({"submitted", "in_review", "approved"})

# W86: statuses that constitute an active room occupancy (student physically assigned to a room)
_ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES: frozenset[str] = frozenset({"assigned", "active"})

# W65: statuses indicating maintenance backlog risk
_MAINTENANCE_RISK_STATUSES: frozenset[str] = frozenset({"submitted", "in_review"})

# ---------------------------------------------------------------------------
# W108: Room assignment availability guard
# A room must be active and available for student assignment.
# Blocked if room is maintenance/closed/reserved or already occupied.
# ---------------------------------------------------------------------------
_ASSIGNABLE_ROOM_STATUSES: frozenset[str] = frozenset({"active"})
_ASSIGNABLE_ROOM_OCCUPANCY: frozenset[str] = frozenset({"available"})


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


def _emit_housing_status_signal(
    *,
    tenant_id: int,
    request_id: int,
    student_id: int,
    request_type: str,
    dormitory: str,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for housing-related student risk."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="housing.status.risk_detected",
        aggregate_type="housing_request",
        aggregate_id=request_id,
        payload_json={
            "request_id": request_id,
            "student_id": student_id,
            "request_type": request_type,
            "dormitory": dormitory,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "housing",
            "source_entity_type": "housing_request",
            "source_entity_id": str(request_id),
        },
    )


def _ensure_maintenance_risk_alert_record(
    tenant_id: int,
    request_id: int,
    request_data: dict,
) -> None:
    """Idempotent: create housing_maintenance_risk_alerts when maintenance backlog risk detected."""
    from app.platform.events.publisher import EventPublisher

    existing = list_entities_for_tenant("housing_maintenance_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "maintenance_risk"
            and str(rec.get("source_entity_id")) == str(request_id)
        ):
            return
    create_entity_for_tenant(
        "housing_maintenance_risk_alerts",
        {
            "request_id": request_id,
            "student_id": int(request_data.get("student_id") or 0),
            "dormitory": str(request_data.get("dormitory") or ""),
            "request_type": str(request_data.get("request_type") or "maintenance"),
            "alert_status": "open",
            "integration_source": "maintenance_risk",
            "source_entity_id": str(request_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.housing.maintenance_overdue_risk_detected",
        aggregate_type="housing_requests",
        aggregate_id=str(request_id),
        payload_json={
            "request_id": request_id,
            "student_id": int(request_data.get("student_id") or 0),
            "dormitory": str(request_data.get("dormitory") or ""),
            "request_type": str(request_data.get("request_type") or "maintenance"),
            "source_module": "housing",
            "source_entity_type": "housing_requests",
            "source_entity_id": str(request_id),
        },
    )


def _check_room_is_assignable(
    *,
    tenant_id: int,
    room_code: str,
) -> None:
    """W108: Cross-entity guard — housing_room_assignments × housing_rooms.

    A student can only be assigned to a room that exists AND has:
    - status = 'active' (not 'maintenance', 'closed', 'reserved')
    - occupancy = 'available' (not 'occupied', 'reserved')

    Assigning to inactive/occupied/non-existent rooms:
      - Doubles occupancy (two students in one room)
      - Assigns to non-functional rooms (maintenance, renovations)
      - Creates phantom housing records during unavailability
      - Triggers cascade failures in housing utilisation analytics

    FAIL-CLOSED: if room lookup fails (any exception), the assignment is BLOCKED.
    """
    try:
        all_rooms = list_entities_for_tenant("housing_rooms", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Room assignment blocked for room_code='{room_code}': "
            f"room lookup failed — {exc}. Cannot verify room availability."
        ) from exc

    matching = [
        row for row in all_rooms
        if str(row.get("room_code") or "").strip().lower() == str(room_code).strip().lower()
    ]

    if not matching:
        raise DomainValidationError(
            f"Room assignment blocked for room_code='{room_code}': "
            "room not found. Students can only be assigned to existing rooms."
        )

    room = matching[0]
    room_status = str(room.get("status") or "").strip().lower()
    room_occupancy = str(room.get("occupancy") or "").strip().lower()

    if room_status not in _ASSIGNABLE_ROOM_STATUSES:
        raise DomainValidationError(
            f"Room assignment blocked for room_code='{room_code}': "
            f"room status is '{room_status}' — not available for assignment. "
            f"Only rooms with status '{sorted(_ASSIGNABLE_ROOM_STATUSES)[0]}' accept assignments."
        )

    if room_occupancy not in _ASSIGNABLE_ROOM_OCCUPANCY:
        raise DomainValidationError(
            f"Room assignment blocked for room_code='{room_code}': "
            f"room occupancy is '{room_occupancy}' — not available. "
            f"Only rooms with occupancy 'available' can be assigned."
        )


def _ensure_room_assignment_record(
    tenant_id: int,
    request_id: int,
    request_data: dict,
) -> None:
    """Idempotent: create a room_assignment_records entity when a housing request is approved."""
    existing = list_entities_for_tenant("room_assignment_records", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "housing_approval"
            and str(rec.get("source_entity_id")) == str(request_id)
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "room_assignment_records",
        {
            "student_id": int(request_data.get("student_id") or 0),
            "request_id": request_id,
            "dormitory": str(request_data.get("dormitory") or "unknown"),
            "room_preference": str(request_data.get("room_preference") or "any"),
            "request_type": str(request_data.get("request_type") or "assignment"),
            "status": "assigned",
            "integration_source": "housing_approval",
            "source_entity_id": str(request_id),
        },
        tenant_id,
    )


def _check_no_active_room_assignment(tenant_id: int, student_id: int, request_id: int) -> None:
    """W86: Cross-entity guard — housing_requests × room_assignment_records.

    A housing request cannot be APPROVED if the student already has an active room
    assignment (status in {assigned, active}).  Approving a second assignment would
    create double-occupancy: one student physically in two rooms simultaneously,
    causing inventory corruption and duplicate billing.

    HARDENING: the guard blocks unconditionally when an active record exists.
    No silent fallback — a query error propagates as DomainValidationError so the
    approval is never silently granted on a broken data path.
    """
    from app.core.module_helpers.service_validation import DomainValidationError

    try:
        existing_assignments = list_entities_for_tenant("room_assignment_records", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot approve housing request: room_assignment_records query failed. "
            f"Cannot verify student_id={student_id} has no active assignment. "
            f"Reason: {exc}"
        ) from exc

    for rec in existing_assignments:
        if (
            int(rec.get("student_id") or 0) == student_id
            and str(rec.get("status") or "") in _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES
        ):
            raise DomainValidationError(
                f"Cannot approve housing request_id={request_id}: "
                f"student_id={student_id} already has an active room assignment "
                f"(record_id={rec.get('id')}, status={rec.get('status')!r}). "
                f"A student cannot occupy two rooms simultaneously. "
                f"Check out the existing assignment before approving a new one."
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
    # Enforce cap: max active requests per student per request_type
    max_active = _REQUEST_TYPE_MAX_ACTIVE.get(request.request_type, 1)
    existing_rows = list_entities_for_tenant("housing_requests", tenant_id)
    active_count = sum(
        1
        for r in existing_rows
        if int(r.get("student_id") or 0) == int(request.student_id)
        and str(r.get("request_type") or "") == request.request_type
        and str(r.get("status") or "") in _ACTIVE_REQUEST_STATUSES
    )
    if active_count >= max_active:
        raise ValueError(
            f"student_id={request.student_id} already has {active_count} active"
            f" '{request.request_type}' requests; max={max_active}"
        )

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

    # W65: maintenance backlog risk alert
    if (
        request.request_type == "maintenance"
        and str(created.get("status") or "submitted") in _MAINTENANCE_RISK_STATUSES
    ):
        _ensure_maintenance_risk_alert_record(
            tenant_id=tenant_id,
            request_id=int(created.get("id") or 0),
            request_data={
                "student_id": request.student_id,
                "dormitory": request.dormitory,
                "request_type": request.request_type,
            },
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

    # W86: Cross-entity guard — block approval if student already has active room assignment
    if payload.status == "approved":
        _check_no_active_room_assignment(
            tenant_id=tenant_id,
            student_id=int(existing.get("student_id") or 0),
            request_id=request_id,
        )

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

    if payload.status in {"rejected", "in_review"}:
        _emit_housing_status_signal(
            tenant_id=tenant_id,
            request_id=request_id,
            student_id=int(updated.get("student_id") or 0),
            request_type=str(updated.get("request_type") or "unknown"),
            dormitory=str(updated.get("dormitory") or "unknown"),
            from_status=current_status,
            to_status=payload.status,
        )

    if payload.status == "approved":
        _ensure_room_assignment_record(tenant_id, request_id, updated)

    return HousingRequestSchema.model_validate(updated)


def create_room_assignment(
    payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    """W108: Create a room assignment with availability check.
    
    Guard ensures room exists, is active, and has available occupancy
    before creating the assignment record.
    """
    # W108: Room availability guard — no assignment during maintenance/occupied
    room_code = str(payload.get("room_code") or "").strip()
    if room_code:
        _check_room_is_assignable(tenant_id=tenant_id, room_code=room_code)
    return create_entity_for_tenant("housing_room_assignments", payload, tenant_id)
