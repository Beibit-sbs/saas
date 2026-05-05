"""Phase VIII-1: Scholarship service."""
from __future__ import annotations

import logging
from uuid import uuid4

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)

logger = logging.getLogger("app.modules.scholarship")


def _record_outcome(entity_id: object, outcome_type: str, actor_id: str) -> None:
    try:
        from app.modules.brain_core import service as brain_core_service  # noqa: PLC0415

        brain_core_service.record_dispatch_outcome(
            entity_id=entity_id,
            outcome_type=outcome_type,
            actor_id=str(actor_id),
        )
    except Exception:
        logger.exception("scholarship outcome failed entity_id=%s outcome=%s", entity_id, outcome_type)


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        logger.exception("scholarship metric failed metric=%s", metric)

# Minimum GPA per scholarship type for eligibility enforcement
_GPA_MINIMUMS: dict[str, float] = {
    "merit": 3.0,
    "athletic": 2.5,
}

_SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE: dict[str, int] = {
    "pending": 300,
    "under_review": 200,
    "approved": 500,
    "rejected": 1000,
    "withdrawn": 800,
}
_ACTIVE_APPLICATION_STATUSES = frozenset({"pending", "under_review", "approved"})
_AWARD_REVOCATION_RISK_STATUSES = frozenset({"revoked"})

# ---------------------------------------------------------------------------
# W102: Scholarship enrollment eligibility guard
# A scholarship application may only be submitted for a student with an active
# enrollment record. Institutional scholarships require active enrollment —
# disbursing funds to non-enrolled students is financial fraud / audit violation.
# ---------------------------------------------------------------------------
_SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES: frozenset[str] = frozenset(
    {"enrolled", "active", "registered"}
)


def _check_student_is_enrolled_for_scholarship(
    *,
    tenant_id: int,
    student_id: str,
    scholarship_type: str,
) -> None:
    """W102: Cross-entity guard — scholarship_applications × enrollments.

    A student must have at least one active enrollment record before any
    scholarship application can be submitted on their behalf.

    Real-world invariant: institutional scholarships are tied to enrollment
    status. Approving or submitting a scholarship for a non-enrolled student
    (withdrawn, expelled, or never enrolled) causes:
      - Financial disbursement to an ineligible recipient
      - Federal financial aid audit violation (Title IV exposure)
      - Irrecoverable grant clawback risk

    FAIL-CLOSED: if the enrollments query fails (any exception), the application
    is BLOCKED. An unknown enrollment state must never default to eligible.
    """
    try:
        all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
        all_students = list_entities_for_tenant("students", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Scholarship application blocked for student_id='{student_id}' "
            f"(scholarship_type='{scholarship_type}'): enrollment lookup failed — {exc}. "
            "Cannot verify active enrollment status."
        ) from exc

    normalized_sid = str(student_id).strip()
    # Two-step lookup: text student_id → integer DB id → enrollment FK
    matching_students = [
        r for r in all_students
        if str(r.get("student_id") or "").strip() == normalized_sid
    ]

    student_str_ids = {
        str(r.get("student_id") or "").strip().lower()
        for r in matching_students
        if str(r.get("student_id") or "").strip()
    }

    def _enrollment_matches(row: dict[str, object]) -> bool:
        raw_student_id = row.get("student_id")
        try:
            row_student_db_id = int(raw_student_id or 0)
        except (TypeError, ValueError):
            row_student_db_id = None
        if row_student_db_id is not None and row_student_db_id in student_db_ids:
            return True
        return str(raw_student_id or "").strip().lower() in student_str_ids

    if matching_students:
        student_db_ids = {int(r.get("id") or 0) for r in matching_students}
        student_enrollments = [
            row for row in all_enrollments
            if _enrollment_matches(row)
        ]
    else:
        student_enrollments = [
            row
            for row in all_enrollments
            if str(row.get("student_id") or "").strip() == normalized_sid
        ]

    if not student_enrollments:
        raise DomainValidationError(
            f"Scholarship application blocked for student_id='{student_id}' "
            f"(scholarship_type='{scholarship_type}'): no enrollment records found. "
            "Active enrollment is required to apply for institutional scholarships."
        )

    has_active = any(
        str(row.get("status") or row.get("enrollment_status") or "").strip().lower()
        in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES
        for row in student_enrollments
    )
    if not has_active:
        found_statuses = list(
            {str(row.get("status") or row.get("enrollment_status") or "unknown")
             for row in student_enrollments}
        )
        raise DomainValidationError(
            f"Scholarship application blocked for student_id='{student_id}' "
            f"(scholarship_type='{scholarship_type}'): student is not actively enrolled. "
            f"Current enrollment statuses: {found_statuses}. "
            "Scholarship eligibility requires active enrollment (enrolled/active/registered)."
        )



def list_scholarship_applications(
    tenant_id: int,
    status: str | None = None,
    scholarship_type: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("scholarship_applications", tenant_id)
    status_filter = str(status or "").strip().lower()
    type_filter = str(scholarship_type or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        if type_filter and str(row.get("scholarship_type") or "").strip().lower() != type_filter:
            continue
        result.append(row)
    return result


def create_scholarship_application(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    scholarship_type = str(payload.get("scholarship_type") or "").strip().lower()
    gpa = float(payload.get("gpa") or 0.0)
    min_gpa = _GPA_MINIMUMS.get(scholarship_type)
    if min_gpa is not None and gpa < min_gpa:
        raise ValueError(
            f"scholarship_type='{scholarship_type}' requires gpa >= {min_gpa}; got {gpa}"
        )

    # W102: Enrollment guard — must have active enrollment before scholarship application
    student_id = str(payload.get("student_id") or "").strip()
    _check_student_is_enrolled_for_scholarship(
        tenant_id=tenant_id,
        student_id=student_id,
        scholarship_type=scholarship_type,
    )

    app_status = str(payload.get("status") or "pending").strip().lower()
    existing_apps = list_entities_for_tenant("scholarship_applications", tenant_id)
    active_app_count = sum(
        1 for r in existing_apps
        if str(r.get("status") or "").strip().lower() in _ACTIVE_APPLICATION_STATUSES
    )
    app_cap = _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE.get(app_status, 300)
    if active_app_count >= app_cap:
        raise ValueError("scholarship_application active cap reached")
    record = create_entity_for_tenant("scholarship_applications", payload, tenant_id)

    _record_outcome(
        record.get("id"),
        "scholarship_application_created",
        str(payload.get("student_id") or "system"),
    )
    _metric(tenant_id, "scholarship_applications_created")

    if str(payload.get("status") or "").strip().lower() == "approved":
        student_id = str(payload.get("student_id") or "")
        _ensure_award_for_approved_application(tenant_id, student_id, scholarship_type, payload)

    return record


def _ensure_award_for_approved_application(
    tenant_id: int,
    student_id: str,
    scholarship_type: str,
    source_payload: dict[str, object],
) -> None:
    """Idempotent: creates a scholarship award when an application is approved, if none exists."""
    awards = list_entities_for_tenant("scholarship_awards", tenant_id)
    has_active_award = any(
        str(row.get("student_id") or "") == student_id
        and str(row.get("scholarship_type") or "").strip().lower() == scholarship_type
        and str(row.get("status") or "").strip().lower() in {"active", "pending"}
        for row in awards
    )
    if has_active_award:
        return

    award_code = f"AUTO-{uuid4().hex[:8].upper()}"
    gpa = float(source_payload.get("gpa") or 0.0)
    amount = float(source_payload.get("requested_amount") or 0.0)
    create_entity_for_tenant(
        "scholarship_awards",
        {
            "award_code": award_code,
            "student_id": student_id,
            "scholarship_type": scholarship_type,
            "status": "active",
            "amount": amount,
            "gpa_threshold": _GPA_MINIMUMS.get(scholarship_type, 2.0),
            "current_gpa": gpa,
            "notes": "Auto-created from approved application",
            "integration_source": "scholarship_application_approval",
        },
        tenant_id,
    )



def list_scholarship_awards(
    tenant_id: int,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("scholarship_awards", tenant_id)
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        at_risk = _is_award_at_risk(row)
        result.append({**row, "at_risk": at_risk})
    return result


def _is_award_at_risk(row: dict[str, object]) -> bool:
    try:
        current_gpa = float(row.get("current_gpa") or 0)
        gpa_threshold = float(row.get("gpa_threshold") or 2.5)
    except (TypeError, ValueError):
        return False
    if current_gpa < gpa_threshold:
        return True
    if str(row.get("status") or "").strip().lower() == "at_risk":
        return True
    return False


def create_scholarship_award(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    """Create award and emit signal if award is at risk."""
    record = create_entity_for_tenant("scholarship_awards", payload, tenant_id)

    _record_outcome(
        record.get("id"),
        "scholarship_award_created",
        str(payload.get("student_id") or "system"),
    )
    _metric(tenant_id, "scholarship_awards_created")

    at_risk = _is_award_at_risk(record)
    enriched = {**record, "at_risk": at_risk}

    if at_risk:
        record_id = int(record.get("id") or 0)
        try:
            current_gpa = float(record.get("current_gpa") or 0.0)
        except (TypeError, ValueError):
            current_gpa = 0.0
        try:
            gpa_threshold = float(record.get("gpa_threshold") or 0.0)
        except (TypeError, ValueError):
            gpa_threshold = 0.0
        risk_level = "high" if current_gpa < gpa_threshold else "medium"
        # Persist alert projection before emitting events to keep downstream views consistent.
        _ensure_revocation_alert_record(record_id, tenant_id)
        try:
            EventPublisher().publish_event(
                tenant_id=tenant_id,
                event_type="scholarship.award.at_risk_detected",
                aggregate_type="scholarship_award",
                aggregate_id=str(record_id),
                payload_json={
                    "award_id": str(record_id),
                    "award_code": record.get("award_code"),
                    "student_id": record.get("student_id"),
                    "current_gpa": record.get("current_gpa"),
                    "gpa_threshold": record.get("gpa_threshold"),
                    "status": record.get("status"),
                    "risk_level": risk_level,
                    "reason": "scholarship_gpa_threshold_breach",
                    "evidence": {
                        "current_gpa": record.get("current_gpa"),
                        "gpa_threshold": record.get("gpa_threshold"),
                        "status": record.get("status"),
                    },
                    "correlation_id": f"scholarship-award-risk:{tenant_id}:{record_id}",
                    "source_entity_type": "scholarship_award",
                    "source_entity_id": str(record_id),
                },
            )
        except Exception:
            # Fire-and-forget: award and alert are already persisted.
            pass

    return enriched


def _ensure_revocation_alert_record(award_id: int, tenant_id: int) -> None:
    existing = list_entities_for_tenant("scholarship_revocation_alerts", tenant_id)
    already = any(
        r.get("integration_source") == "scholarship_revocation_queue"
        and str(r.get("source_entity_id") or "") == str(award_id)
        for r in existing
    )
    if already:
        return
    alert_payload: dict[str, object] = {
        "award_id": award_id,
        "alert_status": "open",
        "integration_source": "scholarship_revocation_queue",
        "source_entity_id": str(award_id),
        "tenant_id": tenant_id,
    }
    create_entity_for_tenant("scholarship_revocation_alerts", alert_payload, tenant_id)


def get_scholarship_brain_context(tenant_id: int) -> dict[str, object]:
    applications = list_entities_for_tenant("scholarship_applications", tenant_id)
    awards = list_entities_for_tenant("scholarship_awards", tenant_id)

    total_applications = len(applications)
    pending_applications = sum(
        1 for r in applications if str(r.get("status") or "").strip().lower() == "pending"
    )
    total_awards = len(awards)
    at_risk_awards = sum(1 for r in awards if _is_award_at_risk(r))

    at_risk_rate = round(at_risk_awards / total_awards, 4) if total_awards > 0 else 0.0

    if at_risk_rate >= 0.25:
        retention_health = "critical"
    elif at_risk_rate >= 0.10:
        retention_health = "at_risk"
    else:
        retention_health = "healthy"

    return {
        "module": "scholarship",
        "tenant_id": tenant_id,
        "total_applications": total_applications,
        "pending_applications": pending_applications,
        "total_awards": total_awards,
        "at_risk_awards": at_risk_awards,
        "at_risk_rate": at_risk_rate,
        "retention_health": retention_health,
    }
