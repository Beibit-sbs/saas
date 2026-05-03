"""Phase XLV — Publications sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

PUB_STATES: frozenset[str] = frozenset(
    {"DRAFT", "SUBMITTED", "PEER_REVIEW", "ACCEPTED", "REJECTED", "PUBLISHED"}
)

_PUB_FSM: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"SUBMITTED"}),
    "SUBMITTED": frozenset({"PEER_REVIEW"}),
    "PEER_REVIEW": frozenset({"ACCEPTED", "REJECTED"}),
    "ACCEPTED": frozenset({"PUBLISHED"}),
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


def _get_pub(tenant_id: int, pub_id: str) -> dict:
    for r in list_entities_for_tenant(tenant_id, "publications"):
        if r.get("id") == pub_id:
            return r
    raise ValueError(f"Publication {pub_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    if target not in _PUB_FSM.get(current, frozenset()):
        raise ValueError(f"Cannot transition publication from {current} to {target}")


def create_publication(tenant_id: int, *, title: str, authors: list[str], journal: str = "") -> dict:
    _validate_tenant(tenant_id)
    if not title:
        raise ValueError("title is required")
    if not authors:
        raise ValueError("authors is required")
    row = create_entity_for_tenant(
        tenant_id,
        "publications",
        {"title": title, "authors": authors, "journal": journal, "status": "DRAFT", "tenant_id": tenant_id},
    )
    return {"pub_id": row["id"], "status": "DRAFT"}


def submit_publication(tenant_id: int, *, pub_id: str) -> dict:
    _validate_tenant(tenant_id)
    pub = _get_pub(tenant_id, pub_id)
    _assert_transition(pub["status"], "SUBMITTED")
    pub["status"] = "SUBMITTED"
    _fire(tenant_id, "publication.submitted", {"pub_id": pub_id})
    return {"pub_id": pub_id, "status": "SUBMITTED"}


def start_peer_review(tenant_id: int, *, pub_id: str) -> dict:
    _validate_tenant(tenant_id)
    pub = _get_pub(tenant_id, pub_id)
    _assert_transition(pub["status"], "PEER_REVIEW")
    pub["status"] = "PEER_REVIEW"
    return {"pub_id": pub_id, "status": "PEER_REVIEW"}


def accept_publication(tenant_id: int, *, pub_id: str) -> dict:
    _validate_tenant(tenant_id)
    pub = _get_pub(tenant_id, pub_id)
    _assert_transition(pub["status"], "ACCEPTED")
    pub["status"] = "ACCEPTED"
    _fire(tenant_id, "publication.accepted", {"pub_id": pub_id})
    return {"pub_id": pub_id, "status": "ACCEPTED"}


def reject_publication(tenant_id: int, *, pub_id: str) -> dict:
    _validate_tenant(tenant_id)
    pub = _get_pub(tenant_id, pub_id)
    _assert_transition(pub["status"], "REJECTED")
    pub["status"] = "REJECTED"
    return {"pub_id": pub_id, "status": "REJECTED"}


def publish_publication(tenant_id: int, *, pub_id: str) -> dict:
    _validate_tenant(tenant_id)
    pub = _get_pub(tenant_id, pub_id)
    _assert_transition(pub["status"], "PUBLISHED")
    pub["status"] = "PUBLISHED"
    _fire(tenant_id, "publication.published", {"pub_id": pub_id, "title": pub.get("title")})
    return {"pub_id": pub_id, "status": "PUBLISHED"}


def add_citation(tenant_id: int, *, pub_id: str, cited_by: str) -> dict:
    _validate_tenant(tenant_id)
    if not cited_by:
        raise ValueError("cited_by is required")
    row = create_entity_for_tenant(
        tenant_id,
        "citations",
        {"pub_id": pub_id, "cited_by": cited_by, "tenant_id": tenant_id},
    )
    _fire(tenant_id, "publication.citation_added", {"pub_id": pub_id, "cited_by": cited_by})
    return {"citation_id": row["id"]}


def list_publications(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "publications")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows
