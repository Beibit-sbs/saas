from __future__ import annotations

import logging

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.alumni.schemas import (
    AlumniRecordCreateSchema,
    AlumniRecordSchema,
    AlumniStatus,
    AlumniRecordStatusUpdateSchema,
)
from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher

logger = logging.getLogger("app.modules.alumni")


def _record_outcome(entity_id: object, outcome_type: str, actor_id: str) -> None:
    try:
        from app.modules.brain_core import service as brain_core_service  # noqa: PLC0415
        brain_core_service.record_dispatch_outcome(
            entity_id=entity_id,
            outcome_type=outcome_type,
            actor_id=str(actor_id),
        )
    except Exception:
        logger.exception("alumni outcome failed entity_id=%s outcome=%s", entity_id, outcome_type)


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        logger.exception("alumni metric failed metric=%s", metric)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "active": {"engaged", "donor", "inactive"},
    "engaged": {"donor", "inactive"},
    "donor": {"engaged", "inactive"},
    "inactive": {"active"},
}

# Max active (active/engaged/donor) alumni records per student per engagement_type
_ENGAGEMENT_TYPE_MAX_ACTIVE: dict[str, int] = {
    "mentoring": 1,
    "event": 3,
    "donation": 5,
    "referral": 2,
}

# Active statuses that count toward cap
_ACTIVE_ALUMNI_STATUSES: frozenset[str] = frozenset({"active", "engaged", "donor"})

# ---------------------------------------------------------------------------
# W96: Graduation gate — only graduated students may have alumni records
# ---------------------------------------------------------------------------
_ALUMNI_ELIGIBLE_STUDENT_STATUSES: frozenset[str] = frozenset({"graduated"})


def _check_student_has_graduated_for_alumni_record(
    *,
    tenant_id: int,
    student_id: int,
) -> None:
    """Cross-entity guard: alumni_records × students.status.

    An alumni record may only be created for a student whose status is 'graduated'.
    Creating an alumni record for an active, enrolled, withdrawn, or suspended student
    creates a false entry in the alumni registry — misrepresenting institutional completion
    rates and exposing the institution to accreditation and reputational risk.

    FAIL-CLOSED: If the student lookup fails (any exception), alumni record creation is
    BLOCKED. Cannot verify graduation without student data.
    """
    try:
        all_students = list_entities_for_tenant("students", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Alumni record creation blocked for student_id={student_id}: "
            f"student lookup failed — {exc}. Cannot verify graduation status."
        ) from exc

    student_records = [
        row for row in all_students
        if str(row.get("id") or "") == str(student_id)
        or str(row.get("student_id") or "") == str(student_id)
    ]
    if not student_records:
        raise DomainValidationError(
            f"Alumni record creation blocked for student_id={student_id}: "
            f"no student record found. Graduation status cannot be verified."
        )

    has_graduated = any(
        str(row.get("status") or "").strip().lower()
        in _ALUMNI_ELIGIBLE_STUDENT_STATUSES
        for row in student_records
    )
    if not has_graduated:
        found_statuses = list(
            {str(row.get("status") or "unknown") for row in student_records}
        )
        raise DomainValidationError(
            f"Alumni record creation blocked for student_id={student_id}: "
            f"student has not graduated. Current status: {found_statuses}. "
            f"Alumni records require graduation status to prevent false registry entries."
        )


def _check_engagement_cap(
    *,
    tenant_id: int,
    student_id: int,
    engagement_type: str,
) -> None:
    """Cross-entity guard: alumni_records cap per student per engagement_type.

    An alumni record may only be created if the student hasn't reached the cap
    for this engagement type. The cap prevents phantom engagement inflation:
    - mentoring: max 1
    - event: max 3
    - donation: max 5
    - referral: max 2

    Phantom engagement inflation (e.g., 50+ event records for 1 student) corrupts
    engagement analytics and Brain Core decision making.

    FAIL-CLOSED: If the alumni records lookup fails (any exception), record creation is
    BLOCKED. Cannot verify cap without alumni data.
    """
    try:
        existing_rows = list_entities_for_tenant("alumni_records", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Alumni record creation blocked for student_id={student_id}, "
            f"engagement_type='{engagement_type}': "
            f"alumni lookup failed — {exc}. Cannot verify engagement cap."
        ) from exc

    max_active = _ENGAGEMENT_TYPE_MAX_ACTIVE.get(engagement_type, 1)
    active_count = sum(
        1
        for r in existing_rows
        if int(r.get("student_id") or 0) == int(student_id)
        and str(r.get("engagement_type") or "").strip().lower() == str(engagement_type).strip().lower()
        and str(r.get("status") or "") in _ACTIVE_ALUMNI_STATUSES
    )

    if active_count >= max_active:
        raise DomainValidationError(
            f"Alumni record creation blocked for student_id={student_id}: "
            f"already has {active_count} active '{engagement_type}' alumni records; "
            f"max={max_active}. Phantom engagement tracking is prevented."
        )


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="alumni_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _ensure_engagement_event(
    tenant_id: int,
    record_id: int,
    record_data: dict,
) -> None:
    """Idempotent: create an alumni_engagement_events entity when record transitions to engaged."""
    existing = list_entities_for_tenant("alumni_engagement_events", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "alumni_engagement"
            and str(rec.get("source_entity_id")) == str(record_id)
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "alumni_engagement_events",
        {
            "student_id": int(record_data.get("student_id") or 0),
            "record_id": record_id,
            "engagement_type": str(record_data.get("engagement_type") or "event"),
            "graduation_year": int(record_data.get("graduation_year") or 2000),
            "status": "recorded",
            "integration_source": "alumni_engagement",
            "source_entity_id": str(record_id),
        },
        tenant_id,
    )


def list_alumni_records(
    tenant_id: int,
    status: AlumniStatus | None = None,
    student_id: int | None = None,
) -> list[AlumniRecordSchema]:
    rows = list_entities_for_tenant("alumni_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [AlumniRecordSchema.model_validate(r) for r in rows]


def create_alumni_record(
    tenant_id: int,
    request: AlumniRecordCreateSchema,
    actor: str,
) -> AlumniRecordSchema:
    # W96: Cross-entity guard — student must have graduated to receive an alumni record
    _check_student_has_graduated_for_alumni_record(
        tenant_id=tenant_id,
        student_id=int(request.student_id),
    )

    # W109: Cross-entity guard — engagement cap per student per type
    _check_engagement_cap(
        tenant_id=tenant_id,
        student_id=int(request.student_id),
        engagement_type=request.engagement_type,
    )

    created = create_entity_for_tenant(
        "alumni_records",
        {
            "student_id": int(request.student_id),
            "graduation_year": int(request.graduation_year),
            "status": "active",
            "engagement_type": request.engagement_type,
            "employer": (request.employer or "unknown").strip() or "unknown",
            "contact_email": (request.contact_email or "unknown@example.com").strip()
            or "unknown@example.com",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("alumni", "record", "create"),
        path="/internal/alumni/records",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "graduation_year": str(request.graduation_year),
        },
        tenant_id=tenant_id,
    )

    try:
        _record_outcome(created.get("id"), "alumni_record_created", str(actor or "system"))
    except Exception:
        logger.exception("alumni create outcome failed")
    try:
        _metric(tenant_id, "alumni_records_created")
    except Exception:
        logger.exception("alumni create metric failed")

    return AlumniRecordSchema.model_validate(created)


def update_alumni_status(
    tenant_id: int,
    record_id: int,
    request: AlumniRecordStatusUpdateSchema,
    actor: str,
) -> AlumniRecordSchema:
    rows = list_entities_for_tenant("alumni_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        raise ValueError(f"record {record_id} not found")

    current_status = str(existing.get("status") or "active")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    updated = update_entity_for_tenant(
        "alumni_records",
        record_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "graduation_year": int(existing.get("graduation_year") or 2000),
            "status": request.status,
            "engagement_type": str(existing.get("engagement_type") or "event"),
            "employer": str(existing.get("employer") or "unknown"),
            "contact_email": str(existing.get("contact_email") or "unknown@example.com"),
            "notes": (request.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("alumni", "record", "status_update"),
        path=f"/internal/alumni/records/{record_id}/status",
        metadata={
            "resource_id": str(record_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    if request.status == "engaged":
        _ensure_engagement_event(
            tenant_id=tenant_id,
            record_id=record_id,
            record_data=updated,
        )

    if request.status in _DISENGAGEMENT_TRIGGER_STATUSES:
        try:
            _emit_alumni_engagement_risk_signal(
                tenant_id=tenant_id,
                record_id=record_id,
                student_id=int(existing.get("student_id") or 0),
                from_status=current_status,
                to_status=request.status,
            )
        except Exception:  # noqa: BLE001
            pass

    # W58 — idempotent disengagement risk alert
    if request.status in _ALUMNI_INACTIVE_RISK_STATUSES:
        _ensure_alumni_disengagement_risk_alert(tenant_id, record_id, dict(updated))

    try:
        _record_outcome(record_id, "alumni_record_status_updated", str(actor or "system"))
    except Exception:
        logger.exception("alumni update outcome failed")
    try:
        _metric(tenant_id, "alumni_records_updated")
    except Exception:
        logger.exception("alumni update metric failed")

    return AlumniRecordSchema.model_validate(updated)


# ---------------------------------------------------------------------------
# Brain-readiness: signal emitter + context snapshot
# ---------------------------------------------------------------------------

_DISENGAGEMENT_TRIGGER_STATUSES: frozenset[str] = frozenset({"inactive"})

# ---------------------------------------------------------------------------
# W58 — alumni disengagement risk constants
# ---------------------------------------------------------------------------
_ALUMNI_ENGAGEMENT_TYPE_MAX_ACTIVE: dict[str, int] = _ENGAGEMENT_TYPE_MAX_ACTIVE
_ALUMNI_INACTIVE_RISK_STATUSES: frozenset[str] = frozenset({"inactive"})


def _ensure_alumni_disengagement_risk_alert(tenant_id: int, record_id: int, record_data: dict) -> None:
    """Idempotent: create alumni_disengagement_risk_alerts record and publish event.

    Uses integration_source='alumni_disengagement_queue' + source_entity_id.
    """
    existing = [
        r for r in list_entities_for_tenant("alumni_disengagement_risk_alerts", tenant_id)
        if str(r.get("integration_source")) == "alumni_disengagement_queue"
        and str(r.get("source_entity_id")) == str(record_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "alumni_disengagement_risk_alerts",
        {
            "record_id": record_id,
            "student_id": record_data.get("student_id"),
            "engagement_type": record_data.get("engagement_type"),
            "graduation_year": record_data.get("graduation_year"),
            "status": record_data.get("status"),
            "alert_level": "warning",
            "risk_status": "active",
            "integration_source": "alumni_disengagement_queue",
            "source_entity_id": str(record_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.alumni.disengagement_risk_detected",
        aggregate_type="alumni_records",
        aggregate_id=record_id,
        payload_json={
            "record_id": record_id,
            "student_id": record_data.get("student_id"),
            "engagement_type": record_data.get("engagement_type"),
            "graduation_year": record_data.get("graduation_year"),
        },
    )


def _emit_alumni_engagement_risk_signal(
    *,
    tenant_id: int,
    record_id: int,
    student_id: int,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for alumni engagement risk."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="alumni.engagement.risk_detected",
        aggregate_type="alumni_record",
        aggregate_id=record_id,
        payload_json={
            "record_id": record_id,
            "student_id": student_id,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "alumni",
            "source_entity_type": "alumni_record",
            "source_entity_id": str(record_id),
        },
    )


def get_alumni_brain_context(tenant_id: int) -> dict:
    """Return aggregated alumni context snapshot for Brain Core."""
    rows = list_entities_for_tenant("alumni_records", tenant_id)
    total = len(rows)
    by_status: dict[str, int] = {}
    by_engagement: dict[str, int] = {}
    for r in rows:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        et = str(r.get("engagement_type") or "unknown")
        by_engagement[et] = by_engagement.get(et, 0) + 1

    inactive = by_status.get("inactive", 0)
    risk_level = "high" if (total > 0 and inactive / total > 0.4) else ("medium" if inactive > 0 else "low")

    return {
        "module": "alumni",
        "tenant_id": tenant_id,
        "total_records": total,
        "by_status": by_status,
        "by_engagement_type": by_engagement,
        "inactive_count": inactive,
        "risk_level": risk_level,
    }
