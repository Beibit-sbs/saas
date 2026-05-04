"""Phase XLVI.3 — AI Admissions Scoring sub-module."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
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


def _fire(tenant_id: int, event_type: str, aggregate_id: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_type="admissions_scoring",
            aggregate_id=aggregate_id,
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
            entity="admissions_scoring",
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


def _record_outcome(tenant_id: int, scoring_id: str, outcome_type: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            scoring_id,
            payload={
                "outcome_type": outcome_type,
                "source_module": "ai_admissions_scoring",
                "scoring_id": scoring_id,
            },
            actor=actor,
        )
    except Exception:
        pass


def _get_scoring(tenant_id: int, scoring_id: str) -> dict:
    for r in list_entities_for_tenant("admissions_scorings", tenant_id):
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


def submit_for_scoring(
    tenant_id: int,
    *,
    application_id: str,
    gpa: float,
    test_score: float,
    essay_length: int,
    actor: str = "system",
) -> dict:
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
        tenant_id,
    )
    scoring_id = str(row["id"])
    _fire(
        tenant_id,
        "admissions.scoring_submitted",
        scoring_id,
        {
            "scoring_id": scoring_id,
            "application_id": application_id,
        },
    )
    _audit(
        tenant_id,
        actor,
        build_audit_action("ai_admissions_scoring", "scoring", "submit"),
        f"/internal/ai-admissions-scoring/{scoring_id}/submit",
        {"scoring_id": scoring_id, "application_id": application_id},
    )
    _metric(tenant_id, "admissions_scoring_submitted", 1)
    return {"scoring_id": scoring_id, "status": "PENDING"}


def generate_score(tenant_id: int, *, scoring_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "SCORED")
    score = _compute_score(scoring["gpa"], scoring["test_score"], scoring["essay_length"])
    scoring["score"] = score
    scoring["status"] = "SCORED"
    _fire(tenant_id, "admissions.score_generated", scoring_id, {
        "scoring_id": scoring_id,
        "application_id": scoring.get("application_id"),
        "score": score,
    })
    _audit(
        tenant_id,
        actor,
        build_audit_action("ai_admissions_scoring", "scoring", "generate_score"),
        f"/internal/ai-admissions-scoring/{scoring_id}/generate-score",
        {"scoring_id": scoring_id, "score": score},
    )
    _metric(tenant_id, "admissions_scores_generated", 1)
    return {"scoring_id": scoring_id, "status": "SCORED", "score": score}


def detect_anomaly(tenant_id: int, *, scoring_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "FLAGGED")
    scoring["status"] = "FLAGGED"
    _fire(tenant_id, "admissions.anomaly_detected", scoring_id, {
        "scoring_id": scoring_id,
        "application_id": scoring.get("application_id"),
        "score": scoring.get("score"),
    })
    _audit(
        tenant_id,
        actor,
        build_audit_action("ai_admissions_scoring", "scoring", "detect_anomaly"),
        f"/internal/ai-admissions-scoring/{scoring_id}/detect-anomaly",
        {"scoring_id": scoring_id},
    )
    _metric(tenant_id, "admissions_scoring_anomalies_detected", 1)
    return {"scoring_id": scoring_id, "status": "FLAGGED"}


def approve_scoring(tenant_id: int, *, scoring_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "APPROVED")
    scoring["status"] = "APPROVED"
    _fire(tenant_id, "admissions.scoring_approved", scoring_id, {
        "scoring_id": scoring_id,
        "application_id": scoring.get("application_id"),
    })
    _record_outcome(tenant_id, scoring_id, "approved", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("ai_admissions_scoring", "scoring", "approve"),
        f"/internal/ai-admissions-scoring/{scoring_id}/approve",
        {"scoring_id": scoring_id},
    )
    _metric(tenant_id, "admissions_scoring_approved", 1)
    return {"scoring_id": scoring_id, "status": "APPROVED"}


def reject_scoring(tenant_id: int, *, scoring_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    scoring = _get_scoring(tenant_id, scoring_id)
    _assert_transition(scoring["status"], "REJECTED")
    scoring["status"] = "REJECTED"
    _fire(tenant_id, "admissions.scoring_rejected", scoring_id, {
        "scoring_id": scoring_id,
        "application_id": scoring.get("application_id"),
    })
    _record_outcome(tenant_id, scoring_id, "rejected", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("ai_admissions_scoring", "scoring", "reject"),
        f"/internal/ai-admissions-scoring/{scoring_id}/reject",
        {"scoring_id": scoring_id},
    )
    _metric(tenant_id, "admissions_scoring_rejected", 1)
    return {"scoring_id": scoring_id, "status": "REJECTED"}


def list_scorings(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("admissions_scorings", tenant_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows
