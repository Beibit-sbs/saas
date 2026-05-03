"""Phase XLIII — Access Control sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

CARD_STATES: frozenset[str] = frozenset({"ACTIVE", "SUSPENDED", "REVOKED"})

REPEATED_DENIAL_THRESHOLD: int = 3

_CARD_FSM: dict[str, frozenset[str]] = {
    "ACTIVE": frozenset({"SUSPENDED", "REVOKED"}),
    "SUSPENDED": frozenset({"ACTIVE", "REVOKED"}),
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        EventPublisher().publish_event(
            tenant_id=int(tenant_id),
            event_type=event_type,
            aggregate_type="access_control",
            aggregate_id=str(payload.get("card_id") or ""),
            payload_json=payload,
        )
    except Exception:
        pass


def _get_card(tenant_id: int, card_id: str) -> dict:
    rows = list_entities_for_tenant("access_cards", tenant_id)
    for r in rows:
        if r.get("id") == card_id:
            return r
    raise ValueError(f"Card {card_id!r} not found")


def _assert_card_transition(current: str, target: str) -> None:
    allowed = _CARD_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition card from {current} to {target}")


# ─── public API ───────────────────────────────────────────────────────────────

def issue_card(
    tenant_id: int,
    *,
    holder_id: str,
    zones: list[str],
) -> dict:
    _validate_tenant(tenant_id)
    if not holder_id:
        raise ValueError("holder_id is required")
    if not zones:
        raise ValueError("zones must not be empty")
    row = create_entity_for_tenant(
        "access_cards",
        {"holder_id": holder_id, "zones": zones, "status": "ACTIVE", "tenant_id": tenant_id},
        tenant_id,
    )
    _fire(tenant_id, "card.issued", {"card_id": row["id"], "holder_id": holder_id, "zones": zones})
    return {"card_id": row["id"], "holder_id": holder_id, "status": "ACTIVE", "zones": zones}


def suspend_card(tenant_id: int, *, card_id: str, reason: str = "") -> dict:
    _validate_tenant(tenant_id)
    card = _get_card(tenant_id, card_id)
    _assert_card_transition(card["status"], "SUSPENDED")
    card["status"] = "SUSPENDED"
    _fire(tenant_id, "card.suspended", {"card_id": card_id, "reason": reason})
    return {"card_id": card_id, "status": "SUSPENDED"}


def reactivate_card(tenant_id: int, *, card_id: str) -> dict:
    _validate_tenant(tenant_id)
    card = _get_card(tenant_id, card_id)
    _assert_card_transition(card["status"], "ACTIVE")
    card["status"] = "ACTIVE"
    return {"card_id": card_id, "status": "ACTIVE"}


def revoke_card(tenant_id: int, *, card_id: str) -> dict:
    _validate_tenant(tenant_id)
    card = _get_card(tenant_id, card_id)
    if card["status"] == "REVOKED":
        raise ValueError("Card already revoked")
    _assert_card_transition(card["status"], "REVOKED")
    card["status"] = "REVOKED"
    return {"card_id": card_id, "status": "REVOKED"}


def attempt_access(
    tenant_id: int,
    *,
    card_id: str,
    zone: str,
) -> dict:
    """Grant or deny access; fires event; checks for security anomaly."""
    _validate_tenant(tenant_id)
    if not zone:
        raise ValueError("zone is required")

    card = _get_card(tenant_id, card_id)

    # deny if card not active
    if card["status"] != "ACTIVE":
        _fire(tenant_id, "access.denied", {"card_id": card_id, "zone": zone, "reason": "card_inactive"})
        _check_security_anomaly(tenant_id, card_id=card_id, zone=zone)
        return {"granted": False, "reason": "card_inactive"}

    # deny if zone not permitted
    allowed_zones = card.get("zones", [])
    if zone not in allowed_zones:
        _fire(tenant_id, "access.denied", {"card_id": card_id, "zone": zone, "reason": "zone_not_permitted"})
        _check_security_anomaly(tenant_id, card_id=card_id, zone=zone)
        return {"granted": False, "reason": "zone_not_permitted"}

    # grant
    create_entity_for_tenant(
        "access_logs",
        {"card_id": card_id, "zone": zone, "result": "GRANTED", "tenant_id": tenant_id},
        tenant_id,
    )
    _fire(tenant_id, "access.granted", {"card_id": card_id, "zone": zone})
    return {"granted": True}


def _check_security_anomaly(tenant_id: int, *, card_id: str, zone: str) -> None:
    """Fire security.anomaly if card has >= REPEATED_DENIAL_THRESHOLD recent denials."""
    logs = list_entities_for_tenant("access_logs", tenant_id)
    denials = [
        lg for lg in logs
        if lg.get("card_id") == card_id and lg.get("result") == "DENIED"
    ]
    create_entity_for_tenant(
        "access_logs",
        {"card_id": card_id, "zone": zone, "result": "DENIED", "tenant_id": tenant_id},
        tenant_id,
    )
    if len(denials) + 1 >= REPEATED_DENIAL_THRESHOLD:
        _fire(tenant_id, "security.anomaly", {"card_id": card_id, "denial_count": len(denials) + 1})


def list_cards(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("access_cards", tenant_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


def list_access_logs(tenant_id: int, *, card_id: str | None = None, zone: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("access_logs", tenant_id)
    if card_id:
        rows = [r for r in rows if r.get("card_id") == card_id]
    if zone:
        rows = [r for r in rows if r.get("zone") == zone]
    return rows
