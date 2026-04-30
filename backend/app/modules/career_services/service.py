from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.career_services.schemas import (
    CareerOpportunityCreateSchema,
    CareerOpportunitySchema,
    CareerOpportunityStatus,
    CareerOpportunityStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_review", "closed", "archived"},
    "in_review": {"closed", "archived", "open"},
    "closed": {"archived"},
    "archived": set(),
}

# ---------------------------------------------------------------------------
# W95: Active enrollment gate — students must be actively enrolled to use
# institutional career placement services
# ---------------------------------------------------------------------------
_CAREER_ACCESS_ENROLLMENT_STATUSES: frozenset[str] = frozenset(
    {"enrolled", "active", "registered"}
)

# Matching engine: max concurrent "open" opportunities per student per type
_OPPORTUNITY_TYPE_MAX_OPEN: dict[str, int] = {
    "internship": 2,
    "job": 3,
    "mentorship": 5,
    "work_study": 1,
}

# ---------------------------------------------------------------------------
# Pipeline capacity caps: max allowed in-review opportunities per student
# ---------------------------------------------------------------------------
_OPPORTUNITY_PIPELINE_MAX_REVIEW: dict[str, int] = {
    "internship": 3,
    "job": 4,
    "mentorship": 2,
    "work_study": 1,
}

# ---------------------------------------------------------------------------
# Opportunity statuses that indicate stalled/at-risk state
# ---------------------------------------------------------------------------
_STALLED_OPPORTUNITY_STATUSES: frozenset[str] = frozenset({"in_review"})

# ---------------------------------------------------------------------------
# Opportunity statuses that trigger stalled opportunity alerts
# ---------------------------------------------------------------------------
_STALLED_RISK_STATUSES: frozenset[str] = frozenset({"in_review"})


def _check_student_is_actively_enrolled_for_career_opportunity(
    *,
    tenant_id: int,
    student_id: int,
    opportunity_type: str,
) -> None:
    """Cross-entity guard: career_opportunities × enrollments.

    A student must have at least one active enrollment record before creating
    a career opportunity. Students who have withdrawn, been dropped, or completed
    their program without active re-enrollment are not entitled to use the
    institutional career placement platform.

    FAIL-CLOSED: If the enrollments lookup fails (any exception), the opportunity
    creation is BLOCKED. This prevents a query fault from silently allowing
    disqualified students through.

    Real-world invariant: Only actively-enrolled students use institutional
    career services. Expelled or withdrawn students retain no placement entitlement.
    """
    try:
        all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Career opportunity creation blocked for student_id={student_id} "
            f"(opportunity_type='{opportunity_type}'): enrollment lookup failed — {exc}. "
            f"Cannot verify active enrollment status."
        ) from exc

    student_enrollments = [
        row for row in all_enrollments
        if str(row.get("student_id") or "") == str(student_id)
        or (lambda v: v is not None and int(v) == int(student_id))(
            _safe_int(row.get("student_id"))
        )
    ]
    if not student_enrollments:
        raise DomainValidationError(
            f"Career opportunity creation blocked for student_id={student_id} "
            f"(opportunity_type='{opportunity_type}'): no enrollment records found. "
            f"Active enrollment required to access institutional career placement services."
        )

    has_active = any(
        str(row.get("status") or row.get("enrollment_status") or "").strip().lower()
        in _CAREER_ACCESS_ENROLLMENT_STATUSES
        for row in student_enrollments
    )
    if not has_active:
        found_statuses = list(
            {str(row.get("status") or row.get("enrollment_status") or "unknown")
             for row in student_enrollments}
        )
        raise DomainValidationError(
            f"Career opportunity creation blocked for student_id={student_id} "
            f"(opportunity_type='{opportunity_type}'): student is not actively enrolled. "
            f"Current enrollment statuses: {found_statuses}. "
            f"Career placement services require active enrollment (enrolled/active/registered)."
        )


def _safe_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="career_opportunity",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _ensure_placement_record(tenant_id: int, opportunity_id: int, opportunity_data: dict) -> None:
    """Idempotent: create a career_placement_records entry when an opportunity moves to in_review."""
    existing = list_entities_for_tenant("career_placement_records", tenant_id)
    for rec in existing:
        if (
            rec.get("integration_source") == "career_matching"
            and int(rec.get("source_entity_id") or 0) == opportunity_id
        ):
            return  # already exists
    create_entity_for_tenant(
        "career_placement_records",
        {
            "student_id": int(opportunity_data.get("student_id") or 0),
            "opportunity_id": opportunity_id,
            "company": str(opportunity_data.get("company") or "Unknown"),
            "opportunity_type": str(opportunity_data.get("opportunity_type") or "internship"),
            "status": "pending_review",
            "integration_source": "career_matching",
            "source_entity_id": opportunity_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_stalled_opportunity_alert_record(tenant_id: int, opportunity_id: int, opportunity_data: dict) -> None:
    """Idempotent cross-module side effect: create career_stalled_opportunity_alerts record.

    Uses integration_source + source_entity_id to prevent duplicates.
    Publishes 'campus.career_services.opportunity_stalled_risk_detected' event.
    """
    existing = [
        r for r in list_entities_for_tenant("career_stalled_opportunity_alerts", tenant_id)
        if str(r.get("integration_source")) == "career_services_stalled_queue"
        and str(r.get("source_entity_id")) == str(opportunity_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "career_stalled_opportunity_alerts",
        {
            "opportunity_id": opportunity_id,
            "student_id": opportunity_data.get("student_id"),
            "opportunity_type": opportunity_data.get("opportunity_type"),
            "company": opportunity_data.get("company"),
            "status": opportunity_data.get("status"),
            "alert_level": "warning",
            "risk_status": "active",
            "integration_source": "career_services_stalled_queue",
            "source_entity_id": str(opportunity_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    from app.platform.events.publisher import EventPublisher
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.career_services.opportunity_stalled_risk_detected",
        aggregate_type="career_opportunity",
        aggregate_id=opportunity_id,
        payload_json={
            "opportunity_id": opportunity_id,
            "student_id": opportunity_data.get("student_id"),
            "opportunity_type": opportunity_data.get("opportunity_type"),
            "company": opportunity_data.get("company"),
        },
    )


def list_career_opportunities(
    tenant_id: int,
    status: CareerOpportunityStatus | None = None,
    student_id: int | None = None,
) -> list[CareerOpportunitySchema]:
    rows = list_entities_for_tenant("career_opportunities", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [CareerOpportunitySchema.model_validate(r) for r in rows]


def create_career_opportunity(
    tenant_id: int,
    request: CareerOpportunityCreateSchema,
    actor: str,
) -> CareerOpportunitySchema:
    # W95: Cross-entity guard — student must be actively enrolled to use career services
    _check_student_is_actively_enrolled_for_career_opportunity(
        tenant_id=tenant_id,
        student_id=int(request.student_id),
        opportunity_type=request.opportunity_type,
    )

    # Matching engine: enforce concurrent open cap per student per type
    max_open = _OPPORTUNITY_TYPE_MAX_OPEN.get(request.opportunity_type, 3)
    open_count = sum(
        1
        for r in list_entities_for_tenant("career_opportunities", tenant_id)
        if int(r.get("student_id") or 0) == int(request.student_id)
        and str(r.get("opportunity_type") or "") == request.opportunity_type
        and str(r.get("status") or "") == "open"
    )
    if open_count >= max_open:
        raise ValueError(
            f"student_id={request.student_id} already has {open_count} open "
            f"'{request.opportunity_type}' opportunities; max={max_open}"
        )

    # Pipeline cap: enforce max concurrent in_review opportunities per student per type
    max_review = _OPPORTUNITY_PIPELINE_MAX_REVIEW.get(request.opportunity_type, 3)
    review_count = sum(
        1
        for r in list_entities_for_tenant("career_opportunities", tenant_id)
        if int(r.get("student_id") or 0) == int(request.student_id)
        and str(r.get("opportunity_type") or "") == request.opportunity_type
        and str(r.get("status") or "") in _STALLED_OPPORTUNITY_STATUSES
    )
    if review_count >= max_review:
        raise ValueError(
            f"student_id={request.student_id} pipeline cap reached for '{request.opportunity_type}' opportunities"
        )

    created = create_entity_for_tenant(
        "career_opportunities",
        {
            "student_id": int(request.student_id),
            "title": request.title.strip(),
            "company": request.company.strip(),
            "opportunity_type": request.opportunity_type,
            "status": "open",
            "owner_id": (request.owner_id or "career-team").strip() or "career-team",
            "start_date": (request.start_date or "unscheduled").strip() or "unscheduled",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("career_services", "opportunity", "create"),
        path="/internal/career-services/opportunities",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "company": request.company,
        },
        tenant_id=tenant_id,
    )
    return CareerOpportunitySchema.model_validate(created)


def update_career_opportunity_status(
    tenant_id: int,
    opportunity_id: int,
    request: CareerOpportunityStatusUpdateSchema,
    actor: str,
) -> CareerOpportunitySchema:
    rows = list_entities_for_tenant("career_opportunities", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == opportunity_id), None)
    if existing is None:
        raise ValueError(f"opportunity {opportunity_id} not found")

    current_status = str(existing.get("status") or "open")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    updated = update_entity_for_tenant(
        "career_opportunities",
        opportunity_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "title": str(existing.get("title") or "Untitled"),
            "company": str(existing.get("company") or "Unknown"),
            "opportunity_type": str(existing.get("opportunity_type") or "internship"),
            "status": request.status,
            "owner_id": str(existing.get("owner_id") or "career-team"),
            "start_date": str(existing.get("start_date") or "unscheduled"),
            "notes": (request.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("career_services", "opportunity", "status_update"),
        path=f"/internal/career-services/opportunities/{opportunity_id}/status",
        metadata={
            "resource_id": str(opportunity_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    if request.status == "in_review":
        _ensure_placement_record(tenant_id, opportunity_id, existing)

    if request.status in _AT_RISK_TRIGGER_STATUSES:
        try:
            _emit_career_opportunity_at_risk_signal(
                tenant_id=tenant_id,
                opportunity_id=opportunity_id,
                student_id=int(existing.get("student_id") or 0),
                from_status=current_status,
                to_status=request.status,
            )
        except Exception:  # noqa: BLE001
            pass

    return CareerOpportunitySchema.model_validate(updated)


# ---------------------------------------------------------------------------
# Brain-readiness: signal emitter + context snapshot
# ---------------------------------------------------------------------------

_AT_RISK_TRIGGER_STATUSES: frozenset[str] = frozenset({"archived"})


def _emit_career_opportunity_at_risk_signal(
    *,
    tenant_id: int,
    opportunity_id: int,
    student_id: int,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for career placement risk."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="career_services.opportunity.at_risk",
        aggregate_type="career_opportunity",
        aggregate_id=opportunity_id,
        payload_json={
            "opportunity_id": opportunity_id,
            "student_id": student_id,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "career_services",
            "source_entity_type": "career_opportunity",
            "source_entity_id": str(opportunity_id),
        },
    )


def get_career_services_brain_context(tenant_id: int) -> dict:
    """Return aggregated career services context snapshot for Brain Core."""
    rows = list_entities_for_tenant("career_opportunities", tenant_id)
    total = len(rows)
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for r in rows:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        ot = str(r.get("opportunity_type") or "unknown")
        by_type[ot] = by_type.get(ot, 0) + 1

    archived = by_status.get("archived", 0)
    risk_level = "high" if (total > 0 and archived / total > 0.5) else ("medium" if archived > 0 else "low")

    return {
        "module": "career_services",
        "tenant_id": tenant_id,
        "total_opportunities": total,
        "by_status": by_status,
        "by_type": by_type,
        "archived_count": archived,
        "risk_level": risk_level,
    }
