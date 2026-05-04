"""Phase XLIII — Access Control sub-module."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
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


def _audit(tenant_id: int, actor: str, action: str, path: str, metadata: dict) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=path,
            client_ip="service",
            entity="access_control",
            metadata=metadata,
            tenant_id=tenant_id,
        )
    except Exception:
        pass


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        pass


def _record_outcome(card_id: str, outcome_type: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            card_id,
            payload={
                "outcome_type": outcome_type,
                "source_module": "access_control",
                "card_id": card_id,
            },
            actor=actor,
        )
    except Exception:
        pass


def _looks_like_table_rows(rows: object, table: str) -> bool:
    if not isinstance(rows, list):
        return False
    if not rows:
        return False
    if not all(isinstance(r, dict) for r in rows):
        return False
    if table == "access_cards":
        return any(("status" in r) or ("zones" in r) or ("holder_id" in r) for r in rows)
    if table == "access_logs":
        return any(("result" in r) or ("zone" in r) or ("card_id" in r) for r in rows)
    return True


def _list_rows(table: str, tenant_id: int) -> list[dict]:
    rows = list_entities_for_tenant(table, tenant_id)
    if _looks_like_table_rows(rows, table):
        return rows
    try:
        fallback_rows = list_entities_for_tenant(tenant_id, table)  # type: ignore[arg-type]
    except Exception:
        return rows if isinstance(rows, list) else []
    if _looks_like_table_rows(fallback_rows, table):
        return fallback_rows
    return rows if isinstance(rows, list) else []


def _create_row(table: str, payload: dict, tenant_id: int) -> dict:
    try:
        return create_entity_for_tenant(table, payload, tenant_id)
    except TypeError:
        return create_entity_for_tenant(tenant_id, table, payload)  # type: ignore[arg-type]


def _get_card(tenant_id: int, card_id: str) -> dict:
    rows = _list_rows("access_cards", tenant_id)
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
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    if not holder_id:
        raise ValueError("holder_id is required")
    if not zones:
        raise ValueError("zones must not be empty")
    row = _create_row(
        "access_cards",
        {"holder_id": holder_id, "zones": zones, "status": "ACTIVE", "tenant_id": tenant_id},
        tenant_id,
    )
    _fire(tenant_id, "card.issued", {"card_id": row["id"], "holder_id": holder_id, "zones": zones})
    _audit(
        tenant_id,
        actor,
        build_audit_action("access_control", "card", "issue"),
        f"/internal/access-control/cards/{row['id']}/issue",
        {"card_id": row["id"], "holder_id": holder_id},
    )
    _metric(tenant_id, "access_cards_issued", 1)
    return {"card_id": row["id"], "holder_id": holder_id, "status": "ACTIVE", "zones": zones}


def suspend_card(tenant_id: int, *, card_id: str, reason: str = "", actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    card = _get_card(tenant_id, card_id)
    _assert_card_transition(card["status"], "SUSPENDED")
    card["status"] = "SUSPENDED"
    _fire(tenant_id, "card.suspended", {"card_id": card_id, "reason": reason})
    _audit(
        tenant_id,
        actor,
        build_audit_action("access_control", "card", "suspend"),
        f"/internal/access-control/cards/{card_id}/suspend",
        {"card_id": card_id, "reason": reason},
    )
    _metric(tenant_id, "access_cards_suspended", 1)
    return {"card_id": card_id, "status": "SUSPENDED"}


def reactivate_card(tenant_id: int, *, card_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    card = _get_card(tenant_id, card_id)
    _assert_card_transition(card["status"], "ACTIVE")
    card["status"] = "ACTIVE"
    _audit(
        tenant_id,
        actor,
        build_audit_action("access_control", "card", "reactivate"),
        f"/internal/access-control/cards/{card_id}/reactivate",
        {"card_id": card_id},
    )
    _metric(tenant_id, "access_cards_reactivated", 1)
    return {"card_id": card_id, "status": "ACTIVE"}


def revoke_card(tenant_id: int, *, card_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    card = _get_card(tenant_id, card_id)
    if card["status"] == "REVOKED":
        raise ValueError("Card already revoked")
    _assert_card_transition(card["status"], "REVOKED")
    card["status"] = "REVOKED"
    _record_outcome(card_id, "card_revoked", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("access_control", "card", "revoke"),
        f"/internal/access-control/cards/{card_id}/revoke",
        {"card_id": card_id},
    )
    _metric(tenant_id, "access_cards_revoked", 1)
    return {"card_id": card_id, "status": "REVOKED"}


def attempt_access(
    tenant_id: int,
    *,
    card_id: str,
    zone: str,
    actor: str = "system",
) -> dict:
    """Grant or deny access; fires event; checks for security anomaly."""
    _validate_tenant(tenant_id)
    if not zone:
        raise ValueError("zone is required")

    card = _get_card(tenant_id, card_id)

    # deny if card not active
    if card["status"] != "ACTIVE":
        _fire(tenant_id, "access.denied", {"card_id": card_id, "zone": zone, "reason": "card_inactive"})
        _record_outcome(card_id, "access_denied", actor)
        _metric(tenant_id, "access_denied", 1)
        _check_security_anomaly(tenant_id, card_id=card_id, zone=zone, actor=actor)
        return {"granted": False, "reason": "card_inactive"}

    # deny if zone not permitted
    allowed_zones = card.get("zones", [])
    if zone not in allowed_zones:
        _fire(tenant_id, "access.denied", {"card_id": card_id, "zone": zone, "reason": "zone_not_permitted"})
        _record_outcome(card_id, "access_denied", actor)
        _metric(tenant_id, "access_denied", 1)
        _check_security_anomaly(tenant_id, card_id=card_id, zone=zone, actor=actor)
        return {"granted": False, "reason": "zone_not_permitted"}

    # grant
    _create_row(
        "access_logs",
        {"card_id": card_id, "zone": zone, "result": "GRANTED", "tenant_id": tenant_id},
        tenant_id,
    )
    _fire(tenant_id, "access.granted", {"card_id": card_id, "zone": zone})
    _record_outcome(card_id, "access_granted", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("access_control", "access", "grant"),
        f"/internal/access-control/cards/{card_id}/access",
        {"card_id": card_id, "zone": zone, "result": "GRANTED"},
    )
    _metric(tenant_id, "access_granted", 1)
    return {"granted": True}


def _check_security_anomaly(tenant_id: int, *, card_id: str, zone: str, actor: str = "system") -> None:
    """Fire security.anomaly if card has >= REPEATED_DENIAL_THRESHOLD recent denials."""
    logs = _list_rows("access_logs", tenant_id)
    denials = [
        lg for lg in logs
        if lg.get("card_id") == card_id and lg.get("result") == "DENIED"
    ]
    _create_row(
        "access_logs",
        {"card_id": card_id, "zone": zone, "result": "DENIED", "tenant_id": tenant_id},
        tenant_id,
    )
    if len(denials) + 1 >= REPEATED_DENIAL_THRESHOLD:
        _fire(tenant_id, "security.anomaly", {"card_id": card_id, "denial_count": len(denials) + 1})
        _audit(
            tenant_id,
            actor,
            build_audit_action("access_control", "security", "anomaly"),
            f"/internal/access-control/cards/{card_id}/security-anomaly",
            {"card_id": card_id, "denial_count": len(denials) + 1},
        )
        _metric(tenant_id, "access_security_anomalies", 1)


def list_cards(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = _list_rows("access_cards", tenant_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


def list_access_logs(tenant_id: int, *, card_id: str | None = None, zone: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = _list_rows("access_logs", tenant_id)
    if card_id:
        rows = [r for r in rows if r.get("card_id") == card_id]
    if zone:
        rows = [r for r in rows if r.get("zone") == zone]
    return rows
