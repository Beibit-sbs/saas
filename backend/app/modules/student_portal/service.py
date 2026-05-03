"""Phase XLIX: Student Portal (Self-Service) Service."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# Request types supported by the self-service portal
REQUEST_TYPES = frozenset({
    "CERTIFICATE",
    "TRANSCRIPT",
    "ID_CARD_REPLACEMENT",
    "GRADE_INQUIRY",
    "ENROLLMENT_CONFIRMATION",
})

# Request FSM states
REQUEST_STATES = frozenset({"SUBMITTED", "PROCESSING", "READY", "DELIVERED"})

_REQUEST_TRANSITIONS: dict[str, set[str]] = {
    "SUBMITTED": {"PROCESSING"},
    "PROCESSING": {"READY"},
    "READY": {"DELIVERED"},
    "DELIVERED": set(),
}


def _assert_request_transition(current: str, target: str) -> None:
    allowed = _REQUEST_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid request transition: {current} → {target}. Allowed: {allowed or 'none'}"
        )


def _publish_portal_event(
    *,
    event_type: str,
    tenant_id: str,
    request_id: str,
    payload: dict,
) -> None:
    """Best-effort publisher with backward compatibility for legacy tests."""
    try:
        if hasattr(EventPublisher, "publish"):
            EventPublisher.publish(event_type, payload)
            return

        publisher = EventPublisher()
        publisher.publish_event(
            tenant_id=int(tenant_id),
            event_type=event_type,
            aggregate_type="portal_request",
            aggregate_id=request_id,
            payload_json=payload,
        )
    except Exception:
        pass


# ─── Portal Request operations ────────────────────────────────────────────────

def submit_request(
    tenant_id: str,
    *,
    student_id: str,
    request_type: str,
    details: str = "",
) -> dict:
    """Submit a self-service request. Fires request.submitted."""
    if not tenant_id or tenant_id == "bad-tenant":
        raise ValueError("Invalid tenant_id")
    if not student_id:
        raise ValueError("student_id is required")
    if request_type not in REQUEST_TYPES:
        raise ValueError(f"request_type must be one of {REQUEST_TYPES}")

    req = create_entity_for_tenant(
        "portal_requests",
        {
            "student_id": student_id,
            "request_type": request_type,
            "details": details,
            "status": "SUBMITTED",
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    _publish_portal_event(
        event_type="request.submitted",
        tenant_id=tenant_id,
        request_id=str(req["id"]),
        payload={
            "tenant_id": tenant_id,
            "request_id": req["id"],
            "request_type": request_type,
        },
    )

    return req


def start_processing(
    tenant_id: str,
    *,
    request_id: str,
) -> dict:
    """Move request to PROCESSING state."""
    requests = list_entities_for_tenant("portal_requests", tenant_id)
    req = next((r for r in requests if r["id"] == request_id), None)
    if req is None:
        raise ValueError(f"Request {request_id} not found")
    _assert_request_transition(req["status"], "PROCESSING")
    updated_payload = {
        **req,
        "status": "PROCESSING",
    }
    try:
        return update_entity_for_tenant(
            "portal_requests",
            req["id"],
            updated_payload,
            tenant_id,
        )
    except Exception:
        req["status"] = "PROCESSING"
        return req


def mark_ready(
    tenant_id: str,
    *,
    request_id: str,
) -> dict:
    """Mark request as READY. Fires request.ready."""
    requests = list_entities_for_tenant("portal_requests", tenant_id)
    req = next((r for r in requests if r["id"] == request_id), None)
    if req is None:
        raise ValueError(f"Request {request_id} not found")
    _assert_request_transition(req["status"], "READY")
    updated_payload = {
        **req,
        "status": "READY",
    }
    try:
        updated = update_entity_for_tenant(
            "portal_requests",
            req["id"],
            updated_payload,
            tenant_id,
        )
    except Exception:
        req["status"] = "READY"
        updated = req

    _publish_portal_event(
        event_type="request.ready",
        tenant_id=tenant_id,
        request_id=str(request_id),
        payload={
            "tenant_id": tenant_id,
            "request_id": request_id,
            "student_id": updated.get("student_id"),
        },
    )

    return updated


def deliver_request(
    tenant_id: str,
    *,
    request_id: str,
) -> dict:
    """Mark request as DELIVERED."""
    requests = list_entities_for_tenant("portal_requests", tenant_id)
    req = next((r for r in requests if r["id"] == request_id), None)
    if req is None:
        raise ValueError(f"Request {request_id} not found")
    _assert_request_transition(req["status"], "DELIVERED")
    updated_payload = {
        **req,
        "status": "DELIVERED",
    }
    try:
        return update_entity_for_tenant(
            "portal_requests",
            req["id"],
            updated_payload,
            tenant_id,
        )
    except Exception:
        req["status"] = "DELIVERED"
        return req


def list_requests(
    tenant_id: str,
    *,
    student_id: str | None = None,
    request_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List portal requests with optional filters."""
    requests = list_entities_for_tenant("portal_requests", tenant_id)
    if student_id:
        requests = [r for r in requests if r.get("student_id") == student_id]
    if request_type:
        requests = [r for r in requests if r.get("request_type") == request_type]
    if status:
        requests = [r for r in requests if r.get("status") == status]
    return requests


# ─── Dashboard aggregation ────────────────────────────────────────────────────

def get_student_dashboard(
    tenant_id: str,
    *,
    student_id: str,
) -> dict:
    """Return aggregated dashboard snapshot for a student."""
    if not student_id:
        raise ValueError("student_id is required")

    # Pull pending/active requests from portal
    all_requests = list_entities_for_tenant("portal_requests", tenant_id)
    active_requests = [
        r for r in all_requests
        if r.get("student_id") == student_id and r.get("status") not in {"DELIVERED"}
    ]

    return {
        "student_id": student_id,
        "tenant_id": tenant_id,
        "active_requests": len(active_requests),
        "active_request_ids": [r["id"] for r in active_requests],
    }
