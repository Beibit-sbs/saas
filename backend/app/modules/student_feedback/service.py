"""Student Feedback Module service — Phase XL.

FSM формы обратной связи:
  OPEN → COLLECTING → CLOSED → ANALYZED

Операции:
  create_feedback_form(tenant_id, *, course_id, title, anonymous=True)
  open_collecting(tenant_id, *, form_id)
  submit_feedback(tenant_id, *, form_id, student_id, rating, comment="", anonymous=True)
  close_form(tenant_id, *, form_id)
  analyze_form(tenant_id, *, form_id)
  get_form_analytics(tenant_id, *, form_id)
  list_forms(tenant_id, *, course_id=None, status=None)

Анонимность:
  При anonymous=True student_id заменяется SHA-256 хешем (salt = tenant_id).
  PII в базе не хранится.

События:
  feedback.submitted
  feedback.analysis_complete
  feedback.low_satisfaction       (при avg_rating < 3.0)

Константы:
  LOW_SATISFACTION_THRESHOLD = 3.0
  SATISFACTION_MAX = 5.0
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

FEEDBACK_STATES = frozenset({"OPEN", "COLLECTING", "CLOSED", "ANALYZED"})
LOW_SATISFACTION_THRESHOLD: float = 3.0
SATISFACTION_MAX: float = 5.0

_FEEDBACK_FSM: dict[str, list[str]] = {
    "OPEN": ["COLLECTING"],
    "COLLECTING": ["CLOSED"],
    "CLOSED": ["ANALYZED"],
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher(tenant_id=tenant_id)
        pub.publish_event(event_type=event_type, payload=payload)
    except Exception:
        pass


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _get_form(tenant_id: int, form_id: str) -> dict:
    forms = list_entities_for_tenant("feedback_forms", tenant_id=tenant_id)
    form = next((f for f in forms if str(f.get("id", "")) == str(form_id)), None)
    if form is None:
        raise LookupError(f"Feedback form {form_id} not found for tenant {tenant_id}")
    return form


def _assert_transition(form: dict, target: str) -> None:
    current = form.get("status", "")
    allowed = _FEEDBACK_FSM.get(current, [])
    if target not in allowed:
        raise ValueError(
            f"Cannot transition feedback form from '{current}' to '{target}'. "
            f"Allowed: {allowed}"
        )


def _anonymize(student_id: str, tenant_id: int) -> str:
    """Return SHA-256 hex digest of student_id salted with tenant_id. No PII stored."""
    raw = f"{tenant_id}:{student_id}".encode()
    return hashlib.sha256(raw).hexdigest()


# ─── create_feedback_form ─────────────────────────────────────────────────────

def create_feedback_form(
    tenant_id: int,
    *,
    course_id: str,
    title: str,
    anonymous: bool = True,
) -> dict:
    _validate_tenant(tenant_id)
    if not course_id:
        raise ValueError("course_id is required")
    if not title:
        raise ValueError("title is required")

    form = create_entity_for_tenant(
        "feedback_forms",
        tenant_id=tenant_id,
        data={
            "course_id": course_id,
            "title": title,
            "anonymous": anonymous,
            "status": "OPEN",
            "created_at": _utc_now(),
            "tenant_id": tenant_id,
        },
    )
    return {"form_id": form.get("id"), "status": "OPEN", "course_id": course_id, "anonymous": anonymous}


# ─── open_collecting ──────────────────────────────────────────────────────────

def open_collecting(tenant_id: int, *, form_id: str) -> dict:
    _validate_tenant(tenant_id)
    form = _get_form(tenant_id, form_id)
    _assert_transition(form, "COLLECTING")

    return {"form_id": form_id, "status": "COLLECTING"}


# ─── submit_feedback ──────────────────────────────────────────────────────────

def submit_feedback(
    tenant_id: int,
    *,
    form_id: str,
    student_id: str,
    rating: float,
    comment: str = "",
    anonymous: bool = True,
) -> dict:
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if not (1.0 <= rating <= SATISFACTION_MAX):
        raise ValueError(f"rating must be between 1.0 and {SATISFACTION_MAX}")

    form = _get_form(tenant_id, form_id)
    if form.get("status") != "COLLECTING":
        raise ValueError("Feedback form must be in COLLECTING status to accept responses")

    student_hash = _anonymize(student_id, tenant_id) if anonymous else student_id

    response = create_entity_for_tenant(
        "feedback_responses",
        tenant_id=tenant_id,
        data={
            "form_id": form_id,
            "student_hash": student_hash,
            "rating": rating,
            "comment": comment,
            "submitted_at": _utc_now(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "feedback.submitted", {
        "form_id": form_id,
        "response_id": response.get("id"),
        "rating": rating,
        "anonymous": anonymous,
        "tenant_id": tenant_id,
    })

    return {"response_id": response.get("id"), "form_id": form_id, "rating": rating}


# ─── close_form ───────────────────────────────────────────────────────────────

def close_form(tenant_id: int, *, form_id: str) -> dict:
    _validate_tenant(tenant_id)
    form = _get_form(tenant_id, form_id)
    _assert_transition(form, "CLOSED")

    return {"form_id": form_id, "status": "CLOSED"}


# ─── analyze_form ─────────────────────────────────────────────────────────────

def analyze_form(tenant_id: int, *, form_id: str) -> dict:
    _validate_tenant(tenant_id)
    form = _get_form(tenant_id, form_id)
    _assert_transition(form, "ANALYZED")

    responses = list_entities_for_tenant("feedback_responses", tenant_id=tenant_id)
    form_responses = [r for r in responses if str(r.get("form_id", "")) == str(form_id)]

    response_count = len(form_responses)
    avg_rating = (
        sum(float(r.get("rating", 0)) for r in form_responses) / response_count
        if response_count > 0
        else 0.0
    )

    analytics = create_entity_for_tenant(
        "feedback_analytics",
        tenant_id=tenant_id,
        data={
            "form_id": form_id,
            "course_id": form.get("course_id"),
            "avg_rating": avg_rating,
            "response_count": response_count,
            "analyzed_at": _utc_now(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "feedback.analysis_complete", {
        "form_id": form_id,
        "course_id": form.get("course_id"),
        "avg_rating": avg_rating,
        "response_count": response_count,
        "analytics_id": analytics.get("id"),
        "tenant_id": tenant_id,
    })

    if avg_rating < LOW_SATISFACTION_THRESHOLD and response_count > 0:
        _fire(tenant_id, "feedback.low_satisfaction", {
            "form_id": form_id,
            "course_id": form.get("course_id"),
            "avg_rating": avg_rating,
            "threshold": LOW_SATISFACTION_THRESHOLD,
            "tenant_id": tenant_id,
        })

    return {
        "form_id": form_id,
        "status": "ANALYZED",
        "avg_rating": avg_rating,
        "response_count": response_count,
        "analytics_id": analytics.get("id"),
        "low_satisfaction_alert": avg_rating < LOW_SATISFACTION_THRESHOLD and response_count > 0,
    }


# ─── get_form_analytics ───────────────────────────────────────────────────────

def get_form_analytics(tenant_id: int, *, form_id: str) -> dict:
    _validate_tenant(tenant_id)
    analytics = list_entities_for_tenant("feedback_analytics", tenant_id=tenant_id)
    record = next((a for a in analytics if str(a.get("form_id", "")) == str(form_id)), None)
    if record is None:
        raise LookupError(f"No analytics found for form {form_id}")
    return record


# ─── list_forms ───────────────────────────────────────────────────────────────

def list_forms(
    tenant_id: int,
    *,
    course_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    forms = list_entities_for_tenant("feedback_forms", tenant_id=tenant_id)
    if course_id:
        forms = [f for f in forms if str(f.get("course_id", "")) == str(course_id)]
    if status:
        forms = [f for f in forms if f.get("status") == status]
    return forms
