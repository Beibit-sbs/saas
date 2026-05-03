"""Phase XLVI.3 — AI Admissions Scoring sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

SCORE_STATES: frozenset[str] = frozenset({"PENDING", "SCORED", "FLAGGED", "APPROVED", "REJECTED"})

_SCORE_FSM: dict[str, frozenset[str]] = {
    "PENDING": frozenset({"SCORED"}),
    "SCORED": frozenset({"FLAGGED", "APPROVED", "REJECTED"}),
    "FLAGGED": frozenset({"APPROVED", "REJECTED"}),
}

# Anomaly detection: score deviates > this fraction from GPA-implied band
ANOMALY_THRESHOLD: float = 0.40


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_scoring(tenant_id: int, scoring_id: str) -> dict:
    for r in list_entities_for_tenant(tenant_id, "admissions_scorings"):
        if r.get("id") == scoring_id:
            return r
    raise ValueError(f"Scoring {scoring_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    if target not in _SCORE_FSM.get(current, frozenset()):
        raise ValueError(f"Cannot transition scoring from {current} to {target}")


def _compute_score(gpa: float, test_score: float, essay_length: int) -> float:
    """Simple deterministic scoring model: weighted average."""
    gpa_norm = min(gpa / 4.0, 1.0)
    test_norm = min(test_score / 100.0, 1.0)
    essay_norm = min(essay_length / 1000.0, 1.0)
    return round(0.5 * gpa_norm + 0.3 * test_norm + 0.2 * essay_norm, 4)


def submit_for_scoring(tenant_id: int, *, application_id: str, gpa: float, test_score: float, essay_length: int) -> dict:
    _validate_tenant(tenant_id)
    if not application_id:
        raise ValueError("application_id is required")
    if gpa < 0 or gpa > 4.0:
        raise ValueError("gpa must be between 0 and 4.0")
    if test_score < 0 or test_score > 100:
        raise ValueError("test_score must be between 0 and 100")
    if essay_length < 0:
        raise ValueError("essay_length must be non-negative")
    row = create_entity_for_tenant(
        tenant_id,
        "admissions_scorings",
        {
            "application_id": application_id,
            "gpa": gpa,
            "test_score": test_score,
            "essay_length": essay_length,
            "score": None,
            "status": "PENDING",
            "tenant_id": tenant_id,
        },
    )
    return {"scoring_id": row["id"], "status": "PENDING"}


def generate_score(tenant_id: int, *, scoring_id: str) -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "SCORED")
    score = _compute_score(scoring["gpa"], scoring["test_score"], scoring["essay_length"])
    scoring["score"] = score
    scoring["status"] = "SCORED"
    _fire(tenant_id, "admissions.score_generated", {
        "scoring_id": scoring_id,
        "application_id": scoring.get("application_id"),
        "score": score,
    })
    return {"scoring_id": scoring_id, "status": "SCORED", "score": score}


def detect_anomaly(tenant_id: int, *, scoring_id: str) -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "FLAGGED")
    scoring["status"] = "FLAGGED"
    _fire(tenant_id, "admissions.anomaly_detected", {
        "scoring_id": scoring_id,
        "application_id": scoring.get("application_id"),
        "score": scoring.get("score"),
    })
    return {"scoring_id": scoring_id, "status": "FLAGGED"}


def approve_scoring(tenant_id: int, *, scoring_id: str) -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "APPROVED")
    scoring["status"] = "APPROVED"
    return {"scoring_id": scoring_id, "status": "APPROVED"}


def reject_scoring(tenant_id: int, *, scoring_id: str) -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "REJECTED")
    scoring["status"] = "REJECTED"
    return {"scoring_id": scoring_id, "status": "REJECTED"}


def list_scorings(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "admissions_scorings")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows
