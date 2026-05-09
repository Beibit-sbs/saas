"""A-023.1 — Research Grants sub-module service skeleton (L2).

Provides grant lifecycle management: application → review → award → active → closed.
Tenant-scoped; no real DB calls — entity API delegates to university_core tables.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ---------------------------------------------------------------------------
# FSM
# ---------------------------------------------------------------------------

GRANT_STATES: frozenset[str] = frozenset(
    {"DRAFT", "SUBMITTED", "UNDER_REVIEW", "AWARDED", "REJECTED", "ACTIVE", "CLOSED"}
)

_GRANT_FSM: dict[str, frozenset[str]] = {
    "DRAFT":        frozenset({"SUBMITTED"}),
    "SUBMITTED":    frozenset({"UNDER_REVIEW"}),
    "UNDER_REVIEW": frozenset({"AWARDED", "REJECTED"}),
    "AWARDED":      frozenset({"ACTIVE"}),
    "ACTIVE":       frozenset({"CLOSED"}),
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_grant(tenant_id: int, grant_id: str) -> dict:
    for row in list_entities_for_tenant(tenant_id, "research_grants"):
        if row.get("id") == grant_id:
            return row
    raise ValueError(f"Grant {grant_id!r} not found for tenant {tenant_id}")


def _assert_transition(current: str, target: str) -> None:
    allowed = _GRANT_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition grant from {current!r} to {target!r}. "
            f"Allowed: {sorted(allowed)}"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_grant(
    tenant_id: int,
    *,
    title: str,
    pi_id: str,
    funding_agency: str,
    requested_amount: float,
) -> dict:
    """Register a new grant application in DRAFT state."""
    _validate_tenant(tenant_id)
    if not title:
        raise ValueError("title is required")
    if not pi_id:
        raise ValueError("pi_id (principal investigator) is required")
    if not funding_agency:
        raise ValueError("funding_agency is required")
    if requested_amount <= 0:
        raise ValueError("requested_amount must be positive")

    row = create_entity_for_tenant(
        tenant_id,
        "research_grants",
        {
            "title": title,
            "pi_id": pi_id,
            "funding_agency": funding_agency,
            "requested_amount": requested_amount,
            "awarded_amount": None,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"grant_id": row["id"], "status": "DRAFT"}


def submit_grant(tenant_id: int, *, grant_id: str) -> dict:
    """Submit a DRAFT grant application for review."""
    _validate_tenant(tenant_id)
    grant = _get_grant(tenant_id, grant_id)
    _assert_transition(grant["status"], "SUBMITTED")
    grant["status"] = "SUBMITTED"
    _fire(tenant_id, "research_grant.submitted", {"grant_id": grant_id, "title": grant.get("title")})
    return {"grant_id": grant_id, "status": "SUBMITTED"}


def start_review(tenant_id: int, *, grant_id: str, reviewer_id: str) -> dict:
    """Move grant into UNDER_REVIEW state and assign a reviewer."""
    _validate_tenant(tenant_id)
    if not reviewer_id:
        raise ValueError("reviewer_id is required")
    grant = _get_grant(tenant_id, grant_id)
    _assert_transition(grant["status"], "UNDER_REVIEW")
    grant["status"] = "UNDER_REVIEW"
    grant["reviewer_id"] = reviewer_id
    return {"grant_id": grant_id, "status": "UNDER_REVIEW"}


def award_grant(tenant_id: int, *, grant_id: str, awarded_amount: float) -> dict:
    """Record award decision and amount."""
    _validate_tenant(tenant_id)
    if awarded_amount <= 0:
        raise ValueError("awarded_amount must be positive")
    grant = _get_grant(tenant_id, grant_id)
    _assert_transition(grant["status"], "AWARDED")
    grant["status"] = "AWARDED"
    grant["awarded_amount"] = awarded_amount
    _fire(
        tenant_id,
        "research_grant.awarded",
        {"grant_id": grant_id, "awarded_amount": awarded_amount, "pi_id": grant.get("pi_id")},
    )
    return {"grant_id": grant_id, "status": "AWARDED", "awarded_amount": awarded_amount}


def reject_grant(tenant_id: int, *, grant_id: str, reason: str) -> dict:
    """Record rejection with a mandatory reason."""
    _validate_tenant(tenant_id)
    if not reason:
        raise ValueError("reason is required for rejection")
    grant = _get_grant(tenant_id, grant_id)
    _assert_transition(grant["status"], "REJECTED")
    grant["status"] = "REJECTED"
    grant["rejection_reason"] = reason
    return {"grant_id": grant_id, "status": "REJECTED"}


def activate_grant(tenant_id: int, *, grant_id: str) -> dict:
    """Activate an AWARDED grant (funds transferred, work begins)."""
    _validate_tenant(tenant_id)
    grant = _get_grant(tenant_id, grant_id)
    _assert_transition(grant["status"], "ACTIVE")
    grant["status"] = "ACTIVE"
    _fire(tenant_id, "research_grant.activated", {"grant_id": grant_id})
    return {"grant_id": grant_id, "status": "ACTIVE"}


def close_grant(tenant_id: int, *, grant_id: str) -> dict:
    """Close an ACTIVE grant at project end."""
    _validate_tenant(tenant_id)
    grant = _get_grant(tenant_id, grant_id)
    _assert_transition(grant["status"], "CLOSED")
    grant["status"] = "CLOSED"
    _fire(tenant_id, "research_grant.closed", {"grant_id": grant_id})
    return {"grant_id": grant_id, "status": "CLOSED"}


def list_grants(
    tenant_id: int,
    *,
    status: str | None = None,
    pi_id: str | None = None,
) -> list[dict]:
    """List grants for the tenant with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "research_grants")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if pi_id:
        rows = [r for r in rows if r.get("pi_id") == pi_id]
    return rows
