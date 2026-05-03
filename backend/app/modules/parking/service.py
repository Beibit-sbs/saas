"""Phase XLIV — Parking Module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── state machines ───────────────────────────────────────────────────────────

PERMIT_STATES: frozenset[str] = frozenset({"PENDING", "ACTIVE", "EXPIRED", "REVOKED"})
SESSION_STATES: frozenset[str] = frozenset({"OPEN", "CLOSED"})

_PERMIT_FSM: dict[str, frozenset[str]] = {
    "PENDING": frozenset({"ACTIVE", "REVOKED"}),
    "ACTIVE": frozenset({"EXPIRED", "REVOKED"}),
}

CAPACITY_WARNING_THRESHOLD: float = 0.85  # 85% occupancy triggers brain signal


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


def _get(tenant_id: int, table: str, entity_id: str) -> dict:
    rows = list_entities_for_tenant(tenant_id, table)
    for r in rows:
        if r.get("id") == entity_id:
            return r
    raise ValueError(f"{table} entity {entity_id!r} not found")


def _assert_permit_transition(current: str, target: str) -> None:
    allowed = _PERMIT_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition permit from {current} to {target}")


# ─── Parking Lots ─────────────────────────────────────────────────────────────

def create_lot(tenant_id: int, *, name: str, capacity: int) -> dict:
    _validate_tenant(tenant_id)
    if not name:
        raise ValueError("name is required")
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    row = create_entity_for_tenant(
        tenant_id,
        "parking_lots",
        {"name": name, "capacity": capacity, "occupancy": 0, "tenant_id": tenant_id},
    )
    return {"lot_id": row["id"], "name": name, "capacity": capacity}


def list_lots(tenant_id: int) -> list[dict]:
    _validate_tenant(tenant_id)
    return list_entities_for_tenant(tenant_id, "parking_lots")


# ─── Parking Permits ──────────────────────────────────────────────────────────

def apply_permit(
    tenant_id: int,
    *,
    holder_id: str,
    lot_id: str,
    vehicle_plate: str,
    valid_from: str,
    valid_until: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not holder_id:
        raise ValueError("holder_id is required")
    if not lot_id:
        raise ValueError("lot_id is required")
    if not vehicle_plate:
        raise ValueError("vehicle_plate is required")
    if not valid_from or not valid_until:
        raise ValueError("valid_from and valid_until are required")
    row = create_entity_for_tenant(
        tenant_id,
        "parking_permits",
        {
            "holder_id": holder_id,
            "lot_id": lot_id,
            "vehicle_plate": vehicle_plate,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "status": "PENDING",
            "tenant_id": tenant_id,
        },
    )
    return {"permit_id": row["id"], "status": "PENDING"}


def approve_permit(tenant_id: int, *, permit_id: str) -> dict:
    _validate_tenant(tenant_id)
    permit = _get(tenant_id, "parking_permits", permit_id)
    _assert_permit_transition(permit["status"], "ACTIVE")
    permit["status"] = "ACTIVE"
    _fire(tenant_id, "parking.permit_issued", {"permit_id": permit_id, "holder_id": permit.get("holder_id")})
    return {"permit_id": permit_id, "status": "ACTIVE"}


def revoke_permit(tenant_id: int, *, permit_id: str, reason: str = "") -> dict:
    _validate_tenant(tenant_id)
    permit = _get(tenant_id, "parking_permits", permit_id)
    if permit["status"] == "REVOKED":
        raise ValueError("Permit already revoked")
    _assert_permit_transition(permit["status"], "REVOKED")
    permit["status"] = "REVOKED"
    return {"permit_id": permit_id, "status": "REVOKED"}


def expire_permit(tenant_id: int, *, permit_id: str) -> dict:
    _validate_tenant(tenant_id)
    permit = _get(tenant_id, "parking_permits", permit_id)
    _assert_permit_transition(permit["status"], "EXPIRED")
    permit["status"] = "EXPIRED"
    return {"permit_id": permit_id, "status": "EXPIRED"}


def list_permits(tenant_id: int, *, holder_id: str | None = None, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "parking_permits")
    if holder_id:
        rows = [r for r in rows if r.get("holder_id") == holder_id]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


# ─── Parking Sessions ─────────────────────────────────────────────────────────

def open_session(tenant_id: int, *, permit_id: str, lot_id: str, spot: str = "") -> dict:
    _validate_tenant(tenant_id)
    if not permit_id:
        raise ValueError("permit_id is required")
    if not lot_id:
        raise ValueError("lot_id is required")
    # verify permit is ACTIVE
    permit = _get(tenant_id, "parking_permits", permit_id)
    if permit["status"] != "ACTIVE":
        raise ValueError(f"Permit {permit_id!r} is not ACTIVE (status={permit['status']!r})")
    row = create_entity_for_tenant(
        tenant_id,
        "parking_sessions",
        {"permit_id": permit_id, "lot_id": lot_id, "spot": spot, "status": "OPEN", "tenant_id": tenant_id},
    )
    _check_lot_capacity(tenant_id, lot_id=lot_id)
    return {"session_id": row["id"], "status": "OPEN"}


def close_session(tenant_id: int, *, session_id: str) -> dict:
    _validate_tenant(tenant_id)
    session = _get(tenant_id, "parking_sessions", session_id)
    if session["status"] != "OPEN":
        raise ValueError(f"Session already in state {session['status']!r}")
    session["status"] = "CLOSED"
    return {"session_id": session_id, "status": "CLOSED"}


def _check_lot_capacity(tenant_id: int, *, lot_id: str) -> None:
    """Fire parking.lot_full or parking.capacity_risk if occupancy is high."""
    sessions = list_entities_for_tenant(tenant_id, "parking_sessions")
    open_sessions = [s for s in sessions if s.get("lot_id") == lot_id and s.get("status") == "OPEN"]
    lots = list_entities_for_tenant(tenant_id, "parking_lots")
    lot = next((l for l in lots if l.get("id") == lot_id), None)
    if lot is None:
        return
    capacity = lot.get("capacity", 1)
    occupancy = len(open_sessions)
    ratio = occupancy / capacity if capacity > 0 else 1.0
    if ratio >= 1.0:
        _fire(tenant_id, "parking.lot_full", {"lot_id": lot_id, "occupancy": occupancy, "capacity": capacity})
    elif ratio >= CAPACITY_WARNING_THRESHOLD:
        _fire(tenant_id, "parking.capacity_risk", {"lot_id": lot_id, "occupancy": occupancy, "capacity": capacity})


# ─── Violations ───────────────────────────────────────────────────────────────

def record_violation(
    tenant_id: int,
    *,
    vehicle_plate: str,
    lot_id: str,
    violation_type: str,
    fine_amount: float = 0.0,
) -> dict:
    _validate_tenant(tenant_id)
    if not vehicle_plate:
        raise ValueError("vehicle_plate is required")
    if not violation_type:
        raise ValueError("violation_type is required")
    row = create_entity_for_tenant(
        tenant_id,
        "parking_violations",
        {
            "vehicle_plate": vehicle_plate,
            "lot_id": lot_id,
            "violation_type": violation_type,
            "fine_amount": fine_amount,
            "tenant_id": tenant_id,
        },
    )
    _fire(
        tenant_id,
        "parking.violation_recorded",
        {"violation_id": row["id"], "vehicle_plate": vehicle_plate, "type": violation_type},
    )
    return {"violation_id": row["id"], "vehicle_plate": vehicle_plate}


def list_violations(tenant_id: int, *, vehicle_plate: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "parking_violations")
    if vehicle_plate:
        rows = [r for r in rows if r.get("vehicle_plate") == vehicle_plate]
    return rows
