"""Phase XLIII — Visitor Management sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

VISIT_STATES: frozenset[str] = frozenset(
    {"REQUESTED", "APPROVED", "CHECKED_IN", "CHECKED_OUT", "EXPIRED"}
)

_TERMINAL_STATES: frozenset[str] = frozenset({"CHECKED_OUT", "EXPIRED"})

_VISIT_FSM: dict[str, frozenset[str]] = {
    "REQUESTED": frozenset({"APPROVED", "EXPIRED"}),
    "APPROVED": frozenset({"CHECKED_IN", "EXPIRED"}),
    "CHECKED_IN": frozenset({"CHECKED_OUT"}),
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_visit(tenant_id: int, visit_id: str) -> dict:
    rows = list_entities_for_tenant(tenant_id, "visit_requests")
    for r in rows:
        if r.get("id") == visit_id:
            return r
    raise ValueError(f"Visit {visit_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    allowed = _VISIT_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition visit from {current} to {target}")


# ─── public API ───────────────────────────────────────────────────────────────

def register_visitor(
    tenant_id: int,
    *,
    name: str,
    host_id: str,
    purpose: str = "",
    visit_date: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not name:
        raise ValueError("name is required")
    if not host_id:
        raise ValueError("host_id is required")
    if not visit_date:
        raise ValueError("visit_date is required")
    row = create_entity_for_tenant(
        tenant_id,
        "visit_requests",
        {
            "name": name,
            "host_id": host_id,
            "purpose": purpose,
            "visit_date": visit_date,
            "status": "REQUESTED",
            "badge_id": None,
            "tenant_id": tenant_id,
        },
    )
    return {"visit_id": row["id"], "status": "REQUESTED"}


def approve_visit(tenant_id: int, *, visit_id: str) -> dict:
    _validate_tenant(tenant_id)
    visit = _get_visit(tenant_id, visit_id)
    _assert_transition(visit["status"], "APPROVED")
    visit["status"] = "APPROVED"
    return {"visit_id": visit_id, "status": "APPROVED"}


def check_in_visitor(tenant_id: int, *, visit_id: str, badge_number: str) -> dict:
    _validate_tenant(tenant_id)
    if not badge_number:
        raise ValueError("badge_number is required")
    visit = _get_visit(tenant_id, visit_id)
    _assert_transition(visit["status"], "CHECKED_IN")
    visit["status"] = "CHECKED_IN"
    visit["badge_id"] = badge_number
    _fire(tenant_id, "visitor.arrived", {"visit_id": visit_id, "badge": badge_number})
    return {"visit_id": visit_id, "status": "CHECKED_IN", "badge": badge_number}


def check_out_visitor(tenant_id: int, *, visit_id: str) -> dict:
    _validate_tenant(tenant_id)
    visit = _get_visit(tenant_id, visit_id)
    _assert_transition(visit["status"], "CHECKED_OUT")
    visit["status"] = "CHECKED_OUT"
    return {"visit_id": visit_id, "status": "CHECKED_OUT"}


def expire_visit(tenant_id: int, *, visit_id: str) -> dict:
    _validate_tenant(tenant_id)
    visit = _get_visit(tenant_id, visit_id)
    if visit["status"] in _TERMINAL_STATES:
        raise ValueError(f"Visit already in terminal state {visit['status']}")
    _assert_transition(visit["status"], "EXPIRED")
    visit["status"] = "EXPIRED"
    return {"visit_id": visit_id, "status": "EXPIRED"}


def record_unauthorized_attempt(tenant_id: int, *, visitor_name: str, zone: str) -> dict:
    _validate_tenant(tenant_id)
    if not visitor_name:
        raise ValueError("visitor_name is required")
    _fire(tenant_id, "visitor.unauthorized_attempt", {"visitor": visitor_name, "zone": zone})
    row = create_entity_for_tenant(
        tenant_id,
        "visit_logs",
        {"visitor_name": visitor_name, "zone": zone, "event": "UNAUTHORIZED_ATTEMPT", "tenant_id": tenant_id},
    )
    return {"log_id": row["id"], "event": "UNAUTHORIZED_ATTEMPT"}


def list_visits(
    tenant_id: int,
    *,
    status: str | None = None,
    host_id: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "visit_requests")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if host_id:
        rows = [r for r in rows if r.get("host_id") == host_id]
    return rows
