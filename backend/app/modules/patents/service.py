"""Phase XLV — Patents sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

PATENT_STATES: frozenset[str] = frozenset(
    {"IDEA", "FILED", "UNDER_REVIEW", "GRANTED", "REJECTED", "LICENSED"}
)

_PATENT_FSM: dict[str, frozenset[str]] = {
    "IDEA": frozenset({"FILED"}),
    "FILED": frozenset({"UNDER_REVIEW"}),
    "UNDER_REVIEW": frozenset({"GRANTED", "REJECTED"}),
    "GRANTED": frozenset({"LICENSED"}),
}


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_patent(tenant_id: int, patent_id: str) -> dict:
    for r in list_entities_for_tenant(tenant_id, "patents"):
        if r.get("id") == patent_id:
            return r
    raise ValueError(f"Patent {patent_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    if target not in _PATENT_FSM.get(current, frozenset()):
        raise ValueError(f"Cannot transition patent from {current} to {target}")


def create_patent(tenant_id: int, *, title: str, inventors: list[str]) -> dict:
    _validate_tenant(tenant_id)
    if not title:
        raise ValueError("title is required")
    if not inventors:
        raise ValueError("inventors is required")
    row = create_entity_for_tenant(
        tenant_id,
        "patents",
        {"title": title, "inventors": inventors, "status": "IDEA", "tenant_id": tenant_id},
    )
    return {"patent_id": row["id"], "status": "IDEA"}


def file_patent(tenant_id: int, *, patent_id: str) -> dict:
    _validate_tenant(tenant_id)
    patent = _get_patent(tenant_id, patent_id)
    _assert_transition(patent["status"], "FILED")
    patent["status"] = "FILED"
    _fire(tenant_id, "patent.filed", {"patent_id": patent_id})
    return {"patent_id": patent_id, "status": "FILED"}


def start_review(tenant_id: int, *, patent_id: str) -> dict:
    _validate_tenant(tenant_id)
    patent = _get_patent(tenant_id, patent_id)
    _assert_transition(patent["status"], "UNDER_REVIEW")
    patent["status"] = "UNDER_REVIEW"
    return {"patent_id": patent_id, "status": "UNDER_REVIEW"}


def grant_patent(tenant_id: int, *, patent_id: str) -> dict:
    _validate_tenant(tenant_id)
    patent = _get_patent(tenant_id, patent_id)
    _assert_transition(patent["status"], "GRANTED")
    patent["status"] = "GRANTED"
    _fire(tenant_id, "patent.granted", {"patent_id": patent_id})
    return {"patent_id": patent_id, "status": "GRANTED"}


def reject_patent(tenant_id: int, *, patent_id: str) -> dict:
    _validate_tenant(tenant_id)
    patent = _get_patent(tenant_id, patent_id)
    _assert_transition(patent["status"], "REJECTED")
    patent["status"] = "REJECTED"
    return {"patent_id": patent_id, "status": "REJECTED"}


def license_patent(tenant_id: int, *, patent_id: str, licensee: str) -> dict:
    _validate_tenant(tenant_id)
    if not licensee:
        raise ValueError("licensee is required")
    patent = _get_patent(tenant_id, patent_id)
    _assert_transition(patent["status"], "LICENSED")
    patent["status"] = "LICENSED"
    _fire(tenant_id, "patent.licensed", {"patent_id": patent_id, "licensee": licensee})
    return {"patent_id": patent_id, "status": "LICENSED"}


def list_patents(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "patents")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows
