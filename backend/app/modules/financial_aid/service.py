from __future__ import annotations

from uuid import uuid4

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.financial_aid.schemas import (
    AidStatus,
    FinancialAidRecordCreateSchema,
    FinancialAidRecordSchema,
    FinancialAidRecordStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_AID_TYPE_MAX_AMOUNT: dict[str, float] = {
    "scholarship": 50_000.0,
    "grant": 25_000.0,
    "tuition_discount": 30_000.0,
    "stipend": 5_000.0,
}

# W39: cap on concurrent active (pending/approved) records per aid_type
_AID_TYPE_MAX_ACTIVE: dict[str, int] = {
    "scholarship": 200,
    "grant": 150,
    "tuition_discount": 100,
    "stipend": 300,
}

_ACTIVE_AID_STATUSES: frozenset[str] = frozenset({"pending", "approved"})

# W64: statuses indicating disbursement risk
_DISBURSEMENT_RISK_STATUSES: frozenset[str] = frozenset({"approved"})

# W39: high-value amount threshold requiring a disbursement watch record
_HIGH_VALUE_AID_THRESHOLD: dict[str, float] = {
    "scholarship": 20_000.0,
    "grant": 10_000.0,
    "tuition_discount": 15_000.0,
    "stipend": 3_000.0,
}

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected"},
    "approved": {"disbursed", "rejected"},
    "disbursed": set(),
    "rejected": set(),
}

# W83: transitions that require the student to have an active enrollment (SAP rule).
# Disbursing aid to a non-enrolled student violates Title IV SAP requirements.
_DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT: frozenset[str] = frozenset({"disbursed"})

# Enrollment statuses considered active for SAP purposes.
_SAP_ACTIVE_ENROLLMENT_STATUSES: frozenset[str] = frozenset({"enrolled", "active", "registered"})


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="financial_aid_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _emit_financial_aid_warning_signal(
    *,
    tenant_id: int,
    record_id: int,
    student_id: int,
    aid_type: str,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for student-success/financial risk scenarios."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="financial_aid.warning.detected",
        aggregate_type="financial_aid_record",
        aggregate_id=record_id,
        payload_json={
            "record_id": record_id,
            "student_id": student_id,
            "aid_type": aid_type,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "financial_aid",
            "source_entity_type": "financial_aid_record",
            "source_entity_id": str(record_id),
        },
    )


def list_financial_aid_records(
    tenant_id: int,
    status: AidStatus | None = None,
    student_id: int | None = None,
) -> list[FinancialAidRecordSchema]:
    rows = list_entities_for_tenant("financial_aid_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [FinancialAidRecordSchema.model_validate(r) for r in rows]


def create_financial_aid_record(
    tenant_id: int,
    request: FinancialAidRecordCreateSchema,
    actor: str,
) -> FinancialAidRecordSchema:
    # W112: Cross-entity guard — student must have active enrollment (Title IV SAP)
    _check_student_enrollment_for_aid_creation(
        tenant_id=tenant_id,
        student_id=int(request.student_id),
        aid_type=request.aid_type,
    )

    max_allowed = _AID_TYPE_MAX_AMOUNT.get(request.aid_type)
    if max_allowed is not None and float(request.amount) > max_allowed:
        raise ValueError(
            f"aid_type='{request.aid_type}' exceeds maximum amount={max_allowed}; "
            f"got {request.amount}"
        )

    # W39: count-cap guard
    cap = _AID_TYPE_MAX_ACTIVE.get(request.aid_type, 200)
    existing = list_entities_for_tenant("financial_aid_records", tenant_id)
    active_count = sum(
        1
        for r in existing
        if str(r.get("aid_type") or "") == request.aid_type
        and str(r.get("status") or "") in _ACTIVE_AID_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active financial aid cap ({cap}) reached for aid_type '{request.aid_type}'"
        )

    created = create_entity_for_tenant(
        "financial_aid_records",
        {
            "student_id": int(request.student_id),
            "aid_type": request.aid_type,
            "amount": float(request.amount),
            "currency": request.currency.upper(),
            "status": "pending",
            "term": request.term.strip(),
            "reviewer_id": (request.reviewer_id or "aid-office").strip() or "aid-office",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("financial_aid", "record", "create"),
        path="/internal/financial-aid/records",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "aid_type": request.aid_type,
        },
        tenant_id=tenant_id,
    )

    # W39: side-effect watch record for high-value aid
    high_val_threshold = _HIGH_VALUE_AID_THRESHOLD.get(request.aid_type)
    if high_val_threshold is not None and float(request.amount) >= high_val_threshold:
        _ensure_disbursement_watch_record(
            tenant_id=tenant_id,
            record_id=int(created.get("id") or 0),
            aid_data={
                "student_id": request.student_id,
                "aid_type": request.aid_type,
                "amount": float(request.amount),
                "term": request.term,
            },
        )

    # W64: disbursement risk alert for active-status aid
    if str(created.get("status") or "pending") in _DISBURSEMENT_RISK_STATUSES:
        _ensure_disbursement_risk_alert_record(
            tenant_id=tenant_id,
            record_id=int(created.get("id") or 0),
            aid_data={
                "student_id": request.student_id,
                "aid_type": request.aid_type,
                "amount": float(request.amount),
                "term": request.term,
            },
        )

    return FinancialAidRecordSchema.model_validate(created)


def _ensure_disbursement_risk_alert_record(
    tenant_id: int,
    record_id: int,
    aid_data: dict,
) -> None:
    """Idempotent: create financial_aid_disbursement_risk_alerts when disbursement risk detected."""
    from app.platform.events.publisher import EventPublisher

    existing = list_entities_for_tenant("financial_aid_disbursement_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "disbursement_risk"
            and str(rec.get("source_entity_id")) == str(record_id)
        ):
            return
    create_entity_for_tenant(
        "financial_aid_disbursement_risk_alerts",
        {
            "aid_record_id": record_id,
            "student_id": int(aid_data.get("student_id") or 0),
            "aid_type": str(aid_data.get("aid_type") or ""),
            "amount": float(aid_data.get("amount") or 0.0),
            "term": str(aid_data.get("term") or ""),
            "alert_status": "open",
            "integration_source": "disbursement_risk",
            "source_entity_id": str(record_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.financial_aid.disbursement_risk_detected",
        aggregate_type="financial_aid_records",
        aggregate_id=str(record_id),
        payload_json={
            "aid_record_id": record_id,
            "student_id": int(aid_data.get("student_id") or 0),
            "aid_type": str(aid_data.get("aid_type") or ""),
            "amount": float(aid_data.get("amount") or 0.0),
            "term": str(aid_data.get("term") or ""),
            "source_module": "financial_aid",
            "source_entity_type": "financial_aid_records",
            "source_entity_id": str(record_id),
        },
    )


def _ensure_disbursement_watch_record(
    tenant_id: int,
    record_id: int,
    aid_data: dict,
) -> None:
    """Idempotent: create a financial_aid_disbursement_watches entry for high-value aid."""
    existing = list_entities_for_tenant("financial_aid_disbursement_watches", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "financial_aid_watch"
            and str(rec.get("source_entity_id")) == str(record_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "financial_aid_disbursement_watches",
        {
            "aid_record_id": record_id,
            "student_id": int(aid_data.get("student_id") or 0),
            "aid_type": str(aid_data.get("aid_type") or ""),
            "amount": float(aid_data.get("amount") or 0.0),
            "term": str(aid_data.get("term") or ""),
            "watch_status": "active",
            "integration_source": "financial_aid_watch",
            "source_entity_id": str(record_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _check_student_enrollment_for_aid_creation(
    *,
    tenant_id: int,
    student_id: int,
    aid_type: str,
) -> None:
    """Cross-entity guard: financial_aid_records × enrollments by student_id.

    A financial aid record may only be created when the student has at least one
    active enrollment (status: enrolled, active, registered). Creating aid records
    for non-enrolled students violates Title IV SAP (Satisfactory Academic Progress)
    requirements and exposes the institution to federal financial aid audit failures.

    FAIL-CLOSED: If enrollment lookup fails (any exception), aid creation is BLOCKED.
    Cannot grant financial commitments without verifying enrollment eligibility.
    """
    try:
        all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Financial aid creation blocked for student_id={student_id} "
            f"(aid_type='{aid_type}'): enrollment lookup failed \u2014 {exc}. "
            f"Cannot verify Title IV SAP compliance without enrollment data."
        ) from exc

    student_enrollments = [
        row for row in all_enrollments
        if _safe_int(row.get("student_id")) == student_id
    ]

    if not student_enrollments:
        raise DomainValidationError(
            f"Financial aid creation blocked for student_id={student_id} "
            f"(aid_type='{aid_type}'): no enrollment records found. "
            f"Title IV SAP requires active enrollment before aid may be granted."
        )

    has_active = any(
        str(row.get("status") or "").strip().lower() in _SAP_ACTIVE_ENROLLMENT_STATUSES
        for row in student_enrollments
    )
    if not has_active:
        statuses = sorted({str(row.get("status") or "unknown") for row in student_enrollments})
        raise DomainValidationError(
            f"Financial aid creation blocked for student_id={student_id} "
            f"(aid_type='{aid_type}'): no active enrollment found. "
            f"Existing enrollment statuses: {statuses}. "
            f"Required: enrolled/active/registered (Title IV SAP)."
        )


def _check_student_has_active_enrollment(tenant_id: int, student_id: int, term: str) -> None:
    """Cross-entity guard: financial_aid_records × enrollments.status (SAP rule).

    Disbursement is blocked when the student has no active enrollment records.
    Satisfactory Academic Progress (SAP) rules under Title IV require a student
    to be enrolled at time of disbursement. Disbursing to a withdrawn or fully-dropped
    student creates federal compliance liability and audit failures.

    FAIL-CLOSED: If no enrollment records exist at all for the student, disbursement
    is BLOCKED (cannot verify SAP compliance). This is a hard requirement, not a safe-skip.
    """
    all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
    student_enrollments = [
        row for row in all_enrollments
        if _safe_int(row.get("student_id")) == student_id
    ]
    if not student_enrollments:
        # FAIL-CLOSED: cannot verify enrollment → cannot disburse
        raise ValueError(
            f"Disbursement blocked for student_id={student_id}: no enrollment records found "
            f"(term='{term}'). Cannot verify Title IV SAP compliance without enrollment data. "
            f"Disbursement requires at least one active enrollment."
        )

    has_active = any(
        str(row.get("status") or "").strip().lower() in _SAP_ACTIVE_ENROLLMENT_STATUSES
        for row in student_enrollments
    )
    if not has_active:
        statuses = list({str(row.get("status") or "unknown") for row in student_enrollments})
        raise ValueError(
            f"Disbursement blocked for student_id={student_id}: no active enrollment found "
            f"(term='{term}'). Existing enrollment statuses: {statuses}. "
            f"Title IV SAP rules require active enrollment at time of disbursement."
        )


def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def update_financial_aid_status(
    tenant_id: int,
    record_id: int,
    request: FinancialAidRecordStatusUpdateSchema,
    actor: str,
) -> FinancialAidRecordSchema:
    rows = list_entities_for_tenant("financial_aid_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        raise ValueError(f"record {record_id} not found")

    current_status = str(existing.get("status") or "pending")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    if request.status in _DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT:
        _check_student_has_active_enrollment(
            tenant_id,
            _safe_int(existing.get("student_id")) or 0,
            str(existing.get("term") or ""),
        )

    updated = update_entity_for_tenant(
        "financial_aid_records",
        record_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "aid_type": str(existing.get("aid_type") or "scholarship"),
            "amount": float(existing.get("amount") or 0),
            "currency": str(existing.get("currency") or "USD"),
            "status": request.status,
            "term": str(existing.get("term") or "unknown"),
            "reviewer_id": str(existing.get("reviewer_id") or "aid-office"),
            "notes": (request.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("financial_aid", "record", "status_update"),
        path=f"/internal/financial-aid/records/{record_id}/status",
        metadata={
            "resource_id": str(record_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    if request.status == "rejected":
        _emit_financial_aid_warning_signal(
            tenant_id=tenant_id,
            record_id=record_id,
            student_id=int(updated.get("student_id") or 0),
            aid_type=str(updated.get("aid_type") or "unknown"),
            from_status=current_status,
            to_status=request.status,
        )

    if request.status == "disbursed":
        _ensure_disbursement_record(tenant_id, record_id, updated)

    return FinancialAidRecordSchema.model_validate(updated)


def _ensure_disbursement_record(
    tenant_id: int, aid_record_id: int, aid_record: dict
) -> None:
    """Idempotent: creates one disbursement record per approved→disbursed transition."""
    existing = list_entities_for_tenant("financial_aid_disbursements", tenant_id)
    already_exists = any(
        str(r.get("integration_source")) == "financial_aid_disbursement"
        and str(r.get("source_entity_id")) == str(aid_record_id)
        for r in existing
    )
    if already_exists:
        return
    disbursement_code = f"DISB-{uuid4().hex[:8].upper()}"
    create_entity_for_tenant(
        "financial_aid_disbursements",
        {
            "disbursement_code": disbursement_code,
            "aid_record_id": aid_record_id,
            "student_id": int(aid_record.get("student_id") or 0),
            "aid_type": str(aid_record.get("aid_type") or "scholarship"),
            "amount": float(aid_record.get("amount") or 0),
            "currency": str(aid_record.get("currency") or "USD"),
            "term": str(aid_record.get("term") or "unknown"),
            "status": "processed",
            "integration_source": "financial_aid_disbursement",
            "source_entity_id": str(aid_record_id),
        },
        tenant_id,
    )
