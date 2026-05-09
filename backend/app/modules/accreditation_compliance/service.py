"""A-023.1 — Accreditation Compliance sub-module service skeleton (L2).

Manages accreditation bodies, standards registration, evidence submissions,
and review cycles for institutional compliance within the multi-tenant
university platform.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ---------------------------------------------------------------------------
# FSM — Accreditation Cycle
# ---------------------------------------------------------------------------

CYCLE_STATES: frozenset[str] = frozenset(
    {"PLANNED", "EVIDENCE_COLLECTION", "SELF_STUDY", "PEER_REVIEW", "DECISION", "ACCREDITED", "DEFERRED", "DENIED"}
)

_CYCLE_FSM: dict[str, frozenset[str]] = {
    "PLANNED":             frozenset({"EVIDENCE_COLLECTION"}),
    "EVIDENCE_COLLECTION": frozenset({"SELF_STUDY"}),
    "SELF_STUDY":          frozenset({"PEER_REVIEW"}),
    "PEER_REVIEW":         frozenset({"DECISION"}),
    "DECISION":            frozenset({"ACCREDITED", "DEFERRED", "DENIED"}),
    "DEFERRED":            frozenset({"EVIDENCE_COLLECTION"}),   # re-entry allowed
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


def _get_cycle(tenant_id: int, cycle_id: str) -> dict:
    for row in list_entities_for_tenant(tenant_id, "accreditation_cycles"):
        if row.get("id") == cycle_id:
            return row
    raise ValueError(f"Accreditation cycle {cycle_id!r} not found for tenant {tenant_id}")


def _assert_transition(current: str, target: str) -> None:
    allowed = _CYCLE_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition cycle from {current!r} to {target!r}. "
            f"Allowed: {sorted(allowed)}"
        )


# ---------------------------------------------------------------------------
# Accreditation Body management
# ---------------------------------------------------------------------------


def register_body(
    tenant_id: int,
    *,
    name: str,
    country: str,
    scope: str,
) -> dict:
    """Register an accreditation body recognised by this tenant."""
    _validate_tenant(tenant_id)
    if not name:
        raise ValueError("name is required")
    if not scope:
        raise ValueError("scope (e.g. 'Engineering', 'Business') is required")

    row = create_entity_for_tenant(
        tenant_id,
        "accreditation_bodies",
        {"name": name, "country": country or "", "scope": scope, "tenant_id": tenant_id},
    )
    return {"body_id": row["id"], "name": name, "scope": scope}


def list_bodies(tenant_id: int) -> list[dict]:
    """List accreditation bodies registered for this tenant."""
    _validate_tenant(tenant_id)
    return list_entities_for_tenant(tenant_id, "accreditation_bodies")


# ---------------------------------------------------------------------------
# Accreditation Cycle management
# ---------------------------------------------------------------------------


def create_cycle(
    tenant_id: int,
    *,
    body_id: str,
    program_id: str,
    target_year: int,
) -> dict:
    """Open a new accreditation cycle for a program."""
    _validate_tenant(tenant_id)
    if not body_id:
        raise ValueError("body_id is required")
    if not program_id:
        raise ValueError("program_id is required")
    if target_year < 2000:
        raise ValueError("target_year seems invalid")

    row = create_entity_for_tenant(
        tenant_id,
        "accreditation_cycles",
        {
            "body_id": body_id,
            "program_id": program_id,
            "target_year": target_year,
            "status": "PLANNED",
            "tenant_id": tenant_id,
        },
    )
    return {"cycle_id": row["id"], "status": "PLANNED"}


def advance_cycle(tenant_id: int, *, cycle_id: str, target_status: str) -> dict:
    """Advance a cycle through its FSM states."""
    _validate_tenant(tenant_id)
    if target_status not in CYCLE_STATES:
        raise ValueError(f"Unknown status {target_status!r}")
    cycle = _get_cycle(tenant_id, cycle_id)
    _assert_transition(cycle["status"], target_status)
    cycle["status"] = target_status

    if target_status == "ACCREDITED":
        _fire(
            tenant_id,
            "accreditation.granted",
            {"cycle_id": cycle_id, "program_id": cycle.get("program_id")},
        )
    elif target_status == "DENIED":
        _fire(
            tenant_id,
            "accreditation.denied",
            {"cycle_id": cycle_id, "program_id": cycle.get("program_id")},
        )

    return {"cycle_id": cycle_id, "status": target_status}


# ---------------------------------------------------------------------------
# Evidence submission
# ---------------------------------------------------------------------------


def submit_evidence(
    tenant_id: int,
    *,
    cycle_id: str,
    standard_ref: str,
    description: str,
    artifact_url: str | None = None,
) -> dict:
    """Record an evidence artefact for a specific accreditation standard."""
    _validate_tenant(tenant_id)
    if not cycle_id:
        raise ValueError("cycle_id is required")
    if not standard_ref:
        raise ValueError("standard_ref is required")
    if not description:
        raise ValueError("description is required")

    # Verify cycle exists and is in an evidence-accepting state
    cycle = _get_cycle(tenant_id, cycle_id)
    if cycle["status"] not in {"EVIDENCE_COLLECTION", "SELF_STUDY"}:
        raise ValueError(
            f"Cannot submit evidence for cycle in state {cycle['status']!r}"
        )

    row = create_entity_for_tenant(
        tenant_id,
        "accreditation_evidence",
        {
            "cycle_id": cycle_id,
            "standard_ref": standard_ref,
            "description": description,
            "artifact_url": artifact_url or "",
            "tenant_id": tenant_id,
        },
    )
    return {"evidence_id": row["id"], "cycle_id": cycle_id, "standard_ref": standard_ref}


def list_evidence(tenant_id: int, *, cycle_id: str) -> list[dict]:
    """List all evidence items for a given accreditation cycle."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "accreditation_evidence")
    return [r for r in rows if r.get("cycle_id") == cycle_id]


def list_cycles(
    tenant_id: int,
    *,
    status: str | None = None,
    program_id: str | None = None,
) -> list[dict]:
    """List accreditation cycles with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "accreditation_cycles")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if program_id:
        rows = [r for r in rows if r.get("program_id") == program_id]
    return rows
