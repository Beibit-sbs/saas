"""Phase XLV — Conference Management sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

PAPER_STATES: frozenset[str] = frozenset(
    {"ABSTRACT", "FULL_PAPER", "REVIEWED", "ACCEPTED", "REJECTED", "PRESENTED"}
)

_PAPER_FSM: dict[str, frozenset[str]] = {
    "ABSTRACT": frozenset({"FULL_PAPER"}),
    "FULL_PAPER": frozenset({"REVIEWED"}),
    "REVIEWED": frozenset({"ACCEPTED", "REJECTED"}),
    "ACCEPTED": frozenset({"PRESENTED"}),
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


def _get_paper(tenant_id: int, paper_id: str) -> dict:
    for r in list_entities_for_tenant(tenant_id, "conference_papers"):
        if r.get("id") == paper_id:
            return r
    raise ValueError(f"Paper {paper_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    if target not in _PAPER_FSM.get(current, frozenset()):
        raise ValueError(f"Cannot transition paper from {current} to {target}")


def create_conference(tenant_id: int, *, name: str, venue: str, date: str) -> dict:
    _validate_tenant(tenant_id)
    if not name:
        raise ValueError("name is required")
    if not date:
        raise ValueError("date is required")
    row = create_entity_for_tenant(
        tenant_id,
        "conferences",
        {"name": name, "venue": venue, "date": date, "tenant_id": tenant_id},
    )
    return {"conference_id": row["id"], "name": name}


def submit_abstract(tenant_id: int, *, conference_id: str, title: str, author_id: str) -> dict:
    _validate_tenant(tenant_id)
    if not title:
        raise ValueError("title is required")
    if not author_id:
        raise ValueError("author_id is required")
    row = create_entity_for_tenant(
        tenant_id,
        "conference_papers",
        {
            "conference_id": conference_id,
            "title": title,
            "author_id": author_id,
            "status": "ABSTRACT",
            "tenant_id": tenant_id,
        },
    )
    return {"paper_id": row["id"], "status": "ABSTRACT"}


def submit_full_paper(tenant_id: int, *, paper_id: str, content: str) -> dict:
    _validate_tenant(tenant_id)
    if not content:
        raise ValueError("content is required")
    paper = _get_paper(tenant_id, paper_id)
    _assert_transition(paper["status"], "FULL_PAPER")
    paper["status"] = "FULL_PAPER"
    return {"paper_id": paper_id, "status": "FULL_PAPER"}


def review_paper(tenant_id: int, *, paper_id: str) -> dict:
    _validate_tenant(tenant_id)
    paper = _get_paper(tenant_id, paper_id)
    _assert_transition(paper["status"], "REVIEWED")
    paper["status"] = "REVIEWED"
    return {"paper_id": paper_id, "status": "REVIEWED"}


def accept_paper(tenant_id: int, *, paper_id: str) -> dict:
    _validate_tenant(tenant_id)
    paper = _get_paper(tenant_id, paper_id)
    _assert_transition(paper["status"], "ACCEPTED")
    paper["status"] = "ACCEPTED"
    _fire(tenant_id, "conference.paper_accepted", {"paper_id": paper_id, "title": paper.get("title")})
    return {"paper_id": paper_id, "status": "ACCEPTED"}


def reject_paper(tenant_id: int, *, paper_id: str) -> dict:
    _validate_tenant(tenant_id)
    paper = _get_paper(tenant_id, paper_id)
    _assert_transition(paper["status"], "REJECTED")
    paper["status"] = "REJECTED"
    return {"paper_id": paper_id, "status": "REJECTED"}


def schedule_presentation(tenant_id: int, *, paper_id: str, slot: str) -> dict:
    _validate_tenant(tenant_id)
    if not slot:
        raise ValueError("slot is required")
    paper = _get_paper(tenant_id, paper_id)
    _assert_transition(paper["status"], "PRESENTED")
    paper["status"] = "PRESENTED"
    _fire(tenant_id, "conference.presentation_scheduled", {"paper_id": paper_id, "slot": slot})
    return {"paper_id": paper_id, "status": "PRESENTED", "slot": slot}


def list_papers(tenant_id: int, *, conference_id: str | None = None, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "conference_papers")
    if conference_id:
        rows = [r for r in rows if r.get("conference_id") == conference_id]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


def evaluate_conference_management_readiness(
    tenant_id: int,
    conference_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for conference workflows."""
    _validate_tenant(tenant_id)
    payload = conference_payload or {}

    required_evidence = [
        "conference_id",
        "speaker_plan",
        "venue_plan",
        "schedule_plan",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    speaker_gap = bool(payload.get("speaker_evidence_gap"))
    venue_schedule_risk = bool(payload.get("venue_or_schedule_risk"))

    if missing_evidence:
        classification = "CONFERENCE_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_conference_inputs"
        rationale = "Conference readiness evidence is incomplete."
    elif speaker_gap:
        classification = "SPEAKER_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "request_speaker_evidence_for_manual_review"
        rationale = "Speaker evidence is required before approval."
    elif venue_schedule_risk:
        classification = "VENUE_OR_SCHEDULE_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "escalate_venue_schedule_risk_to_manual_review"
        rationale = "Venue or schedule risk requires operator review."
    elif payload.get("approval_packet_ready"):
        classification = "READY_FOR_MANUAL_EVENT_APPROVAL"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "route_conference_packet_for_manual_approval"
        rationale = "Conference approval packet is complete for human review."
    else:
        classification = "READY_FOR_CONFERENCE_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_conference_review"
        rationale = "Conference inputs are sufficient for deterministic review."

    return {
        "tenant_id": tenant_id,
        "module": "conference_management",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_PLAN",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_CONFERENCE",
            "AUTO_BOOK_VENUE",
            "AUTO_PUBLISH_EVENT",
        ],
        "human_review_required": True,
        "next_recommended_step": next_step,
        "rationale_notes": rationale,
        "safety_flags": {
            "tenant_scoped": True,
            "deterministic": True,
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_kpi_claim": True,
            "no_brain_claim": True,
            "no_autonomous_execution": True,
            "no_external_provider_call": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }
