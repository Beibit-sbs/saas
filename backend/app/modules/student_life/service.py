from __future__ import annotations

from uuid import uuid4

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.platform.events.publisher import EventPublisher
from app.modules.student_life.schemas import (
    AccessibilitySupportCreateSchema,
    AccessibilitySupportSchema,
    CounselingCaseCreateSchema,
    CounselingCaseSchema,
    DISCIPLINARY_ALLOWED_TRANSITIONS,
    DisciplinaryCaseCreateSchema,
    DisciplinaryCaseSchema,
    DisciplinaryCaseStatusUpdateSchema,
    StudentLifeHealthSnapshotSchema,
    WellbeingCheckinCreateSchema,
    WellbeingCheckinSchema,
)
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.modules.student_life.business_rules import StudentLifeRules
from app.core.module_helpers.service_validation import DomainValidationError

# ---------------------------------------------------------------------------
# W104: Disciplinary case student enrollment guard
# A disciplinary case may only be opened for a student with an active enrollment.
# Opening a disciplinary case (especially severity=critical/high) triggers
# automated escalation alerts and Brain Core events. Ghost-student disciplinary
# records cause automated decisions for phantom individuals — FERPA/audit violation.
# ---------------------------------------------------------------------------
_DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES: frozenset[str] = frozenset(
    {"enrolled", "active", "registered"}
)


def _check_student_is_enrolled_for_disciplinary(
    *,
    tenant_id: int,
    student_id: str,
    severity: str,
) -> None:
    """W104: Cross-entity guard — student_life_disciplinary_cases × enrollments.

    A student must have at least one active enrollment record before any
    disciplinary case (especially high/critical severity) can be opened.

    Real-world invariant: disciplinary proceedings require an active student
    relationship with the institution. Creating cases for withdrawn/expelled/
    non-existent students:
      - Generates phantom escalation alerts and Brain Core events
      - Creates permanent disciplinary records for ghost individuals
      - Violates FERPA (records for non-students)
      - Corrupts institutional disciplinary metrics

    FAIL-CLOSED: if the enrollments query fails, the case creation is BLOCKED.
    """
    try:
        all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Disciplinary case blocked for student_id='{student_id}' "
            f"(severity='{severity}'): enrollments lookup failed — {exc}. "
            "Cannot verify active enrollment status."
        ) from exc

    student_enrollments = [
        row for row in all_enrollments
        if str(row.get("student_id") or "").strip() == str(student_id).strip()
    ]

    if not student_enrollments:
        raise DomainValidationError(
            f"Disciplinary case blocked for student_id='{student_id}' "
            f"(severity='{severity}'): no enrollment records found. "
            "Active enrollment is required to open a disciplinary case."
        )

    has_active = any(
        str(row.get("status") or row.get("enrollment_status") or "").strip().lower()
        in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES
        for row in student_enrollments
    )
    if not has_active:
        found_statuses = list(
            {str(row.get("status") or row.get("enrollment_status") or "unknown")
             for row in student_enrollments}
        )
        raise DomainValidationError(
            f"Disciplinary case blocked for student_id='{student_id}' "
            f"(severity='{severity}'): no active enrollment found. "
            f"Found enrollment statuses: {found_statuses}. "
            "Active enrollment required to initiate institutional disciplinary proceedings."
        )


# ---------------------------------------------------------------------------
# W57 — disciplinary case cap: max active cases per severity
# ---------------------------------------------------------------------------
_DISCIPLINARY_SEVERITY_MAX_ACTIVE: dict[str, int] = {
    "low": 50,
    "medium": 30,
    "high": 15,
    "critical": 5,
}

# Disciplinary statuses counted as active toward the cap
_ACTIVE_DISCIPLINARY_STATUSES: frozenset[str] = frozenset({"reported", "under_review", "hearing_scheduled", "appealed"})

# Statuses that trigger escalation risk alert
_DISCIPLINARY_ESCALATION_RISK_STATUSES: frozenset[str] = frozenset({"appealed"})

# --- W32: counseling case cap by concern_type ---
_CONCERN_TYPE_MAX_ACTIVE_CASES: dict[str, int] = {
    "academic": 40,
    "mental_health": 20,
    "financial": 25,
    "wellbeing_risk": 30,
    "career": 50,
    "other": 60,
}

_ACTIVE_COUNSELING_STATUSES: frozenset[str] = frozenset({"open", "in_progress"})

# concern types that trigger a disciplinary alert record side effect
_SERIOUS_CONCERN_TYPES: frozenset[str] = frozenset(
    {"misconduct", "harassment", "violence", "substance_abuse"}
)


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="student_life",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_counseling_cases(tenant_id: int) -> list[CounselingCaseSchema]:
    rows = list_entities_for_tenant("student_life_counseling_cases", tenant_id)
    return [CounselingCaseSchema.model_validate(r) for r in rows]


def create_counseling_case(tenant_id: int, request: CounselingCaseCreateSchema, actor: str) -> CounselingCaseSchema:
    concern_type = str(request.concern_type or "other").strip().lower()
    cap = _CONCERN_TYPE_MAX_ACTIVE_CASES.get(concern_type, 60)

    if request.status in _ACTIVE_COUNSELING_STATUSES:
        all_cases = list_entities_for_tenant("student_life_counseling_cases", tenant_id)
        active_count = sum(
            1 for r in all_cases
            if str(r.get("concern_type") or "").strip().lower() == concern_type
            and str(r.get("status") or "").strip().lower() in _ACTIVE_COUNSELING_STATUSES
        )
        if active_count >= cap:
            raise ValueError(
                f"Active counseling case cap ({cap}) for concern_type '{concern_type}' reached."
            )

    created = create_entity_for_tenant(
        "student_life_counseling_cases",
        {
            "case_code": request.case_code.strip(),
            "student_id": request.student_id.strip(),
            "concern_type": request.concern_type.strip(),
            "status": request.status,
            "priority": getattr(request, "priority", None),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "counseling_case", "create"),
        path="/internal/student-life/counseling-cases",
        metadata={"resource_id": str(created.get("id")), "case_code": request.case_code},
        tenant_id=tenant_id,
    )

    if concern_type in _SERIOUS_CONCERN_TYPES:
        _ensure_student_alert_record(created, tenant_id)

    return CounselingCaseSchema.model_validate(created)


def _ensure_disciplinary_escalation_alert(tenant_id: int, case_id: int, case_data: dict) -> None:
    """Idempotent: create disciplinary_escalation_alerts record and publish event.

    Uses integration_source='disciplinary_escalation_queue' + source_entity_id.
    """
    existing = [
        r for r in list_entities_for_tenant("student_life_disciplinary_escalation_alerts", tenant_id)
        if str(r.get("integration_source")) == "disciplinary_escalation_queue"
        and str(r.get("source_entity_id")) == str(case_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "student_life_disciplinary_escalation_alerts",
        {
            "case_id": case_id,
            "incident_code": case_data.get("incident_code"),
            "student_id": case_data.get("student_id"),
            "incident_type": case_data.get("incident_type"),
            "severity": case_data.get("severity"),
            "status": case_data.get("status"),
            "alert_level": "warning",
            "risk_status": "active",
            "integration_source": "disciplinary_escalation_queue",
            "source_entity_id": str(case_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.student_life.disciplinary_escalation_risk_detected",
        aggregate_type="student_life_disciplinary_cases",
        aggregate_id=case_id,
        payload_json={
            "case_id": case_id,
            "incident_code": case_data.get("incident_code"),
            "student_id": case_data.get("student_id"),
            "severity": case_data.get("severity"),
        },
    )


def _ensure_student_alert_record(case: dict[str, object], tenant_id: int) -> None:
    """Idempotent side-effect: ensure a disciplinary alert record for serious counseling cases."""
    case_id = str(case.get("id") or case.get("case_code") or "unknown")
    existing = list_entities_for_tenant("student_life_alert_records", tenant_id)
    for rec in existing:
        if str(rec.get("source_entity_id") or "") == case_id and str(
            rec.get("integration_source") or ""
        ) == "counseling_serious_concern":
            return  # already exists

    create_entity_for_tenant(
        "student_life_alert_records",
        {
            "case_id": case_id,
            "case_code": case.get("case_code"),
            "concern_type": case.get("concern_type"),
            "student_id": case.get("student_id"),
            "integration_source": "counseling_serious_concern",
            "source_entity_id": case_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def list_wellbeing_checkins(tenant_id: int) -> list[WellbeingCheckinSchema]:
    rows = list_entities_for_tenant("student_life_wellbeing_checkins", tenant_id)
    return [WellbeingCheckinSchema.model_validate(r) for r in rows]


def _ensure_counseling_case_for_wellbeing_risk(tenant_id: int, student_id: str) -> None:
    counseling_rows = list_entities_for_tenant("student_life_counseling_cases", tenant_id)
    has_open_case = any(
        str(row.get("student_id") or "") == student_id
        and str(row.get("status") or "") in {"open", "in_progress"}
        for row in counseling_rows
    )
    if has_open_case:
        return

    case_code = f"WB-AUTO-{uuid4().hex[:8]}"
    create_entity_for_tenant(
        "student_life_counseling_cases",
        {
            "case_code": case_code,
            "student_id": student_id,
            "concern_type": "wellbeing_risk",
            "status": "open",
        },
        tenant_id,
    )


def create_wellbeing_checkin(
    tenant_id: int,
    request: WellbeingCheckinCreateSchema,
    actor: str,
) -> WellbeingCheckinSchema:
    if request.wellbeing_score <= 40 and request.status != "at_risk":
        raise ValueError("wellbeing_score <= 40 requires status='at_risk'")

    created = create_entity_for_tenant(
        "student_life_wellbeing_checkins",
        {
            "student_id": request.student_id.strip(),
            "wellbeing_score": int(request.wellbeing_score),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "wellbeing_checkin", "create"),
        path="/internal/student-life/wellbeing-checkins",
        metadata={"resource_id": str(created.get("id")), "student_id": request.student_id},
        tenant_id=tenant_id,
    )

    if request.status == "at_risk" or request.wellbeing_score <= 40:
        _ensure_counseling_case_for_wellbeing_risk(
            tenant_id=tenant_id,
            student_id=request.student_id.strip(),
        )

    return WellbeingCheckinSchema.model_validate(created)


def list_accessibility_supports(tenant_id: int) -> list[AccessibilitySupportSchema]:
    rows = list_entities_for_tenant("student_life_accessibility_supports", tenant_id)
    return [AccessibilitySupportSchema.model_validate(r) for r in rows]


def create_accessibility_support(
    tenant_id: int,
    request: AccessibilitySupportCreateSchema,
    actor: str,
) -> AccessibilitySupportSchema:
    created = create_entity_for_tenant(
        "student_life_accessibility_supports",
        {
            "support_code": request.support_code.strip(),
            "student_id": request.student_id.strip(),
            "support_type": request.support_type.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "accessibility_support", "create"),
        path="/internal/student-life/accessibility-supports",
        metadata={"resource_id": str(created.get("id")), "support_code": request.support_code},
        tenant_id=tenant_id,
    )
    return AccessibilitySupportSchema.model_validate(created)


def list_disciplinary_cases(tenant_id: int) -> list[DisciplinaryCaseSchema]:
    rows = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)
    return [DisciplinaryCaseSchema.model_validate(r) for r in rows]


def create_disciplinary_case(
    tenant_id: int,
    request: DisciplinaryCaseCreateSchema,
    actor: str,
) -> DisciplinaryCaseSchema:
    # DATA INTEGRITY: one active disciplinary case per student
    student_id = request.student_id.strip()
    if str(request.status) in _ACTIVE_DISCIPLINARY_STATUSES:
        all_cases_for_student = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)
        active_for_student = [
            r for r in all_cases_for_student
            if str(r.get("student_id") or "").strip() == student_id
            and str(r.get("status") or "") in _ACTIVE_DISCIPLINARY_STATUSES
        ]
        StudentLifeRules.validate_no_duplicate_active_disciplinary_case(
            active_for_student, student_id=student_id
        )

    # W57 — cap guard: limit active disciplinary cases per severity
    severity = str(request.severity or "").strip().lower()
    cap = _DISCIPLINARY_SEVERITY_MAX_ACTIVE.get(severity)
    if cap is not None and str(request.status) in _ACTIVE_DISCIPLINARY_STATUSES:
        all_cases = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)
        active_count = sum(
            1 for r in all_cases
            if str(r.get("severity") or "").strip().lower() == severity
            and str(r.get("status") or "") in _ACTIVE_DISCIPLINARY_STATUSES
        )
        if active_count >= cap:
            raise ValueError(
                f"active disciplinary case cap reached for severity '{severity}'"
            )

    # W104: Student enrollment guard — disciplinary case requires active enrollment
    _check_student_is_enrolled_for_disciplinary(
        tenant_id=tenant_id,
        student_id=student_id,
        severity=severity,
    )

    created = create_entity_for_tenant(
        "student_life_disciplinary_cases",
        {
            "incident_code": request.incident_code.strip(),
            "student_id": request.student_id.strip(),
            "incident_type": request.incident_type.strip(),
            "severity": request.severity.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "disciplinary_case", "create"),
        path="/internal/student-life/disciplinary-cases",
        metadata={"resource_id": str(created.get("id")), "incident_code": request.incident_code},
        tenant_id=tenant_id,
    )
    return DisciplinaryCaseSchema.model_validate(created)


def update_disciplinary_case_status(
    tenant_id: int,
    case_id: int,
    request: DisciplinaryCaseStatusUpdateSchema,
    actor: str,
) -> DisciplinaryCaseSchema:
    rows = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == case_id), None)
    if existing is None:
        raise ValueError(f"Disciplinary case {case_id} not found for tenant {tenant_id}")

    current_status = str(existing.get("status") or "reported")
    allowed = DISCIPLINARY_ALLOWED_TRANSITIONS.get(current_status, [])
    if request.status not in allowed:
        raise ValueError(
            f"Transition from '{current_status}' to '{request.status}' is not allowed. "
            f"Allowed: {allowed}"
        )

    updated = update_entity_for_tenant(
        "student_life_disciplinary_cases",
        case_id,
        {**existing, "status": request.status},
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "disciplinary_case", "status_update"),
        path=f"/internal/student-life/disciplinary-cases/{case_id}/status",
        metadata={
            "resource_id": str(case_id),
            "from_status": current_status,
            "to_status": request.status,
            "reason": request.reason or "",
        },
        tenant_id=tenant_id,
    )
    # Cross-module: when case is closed, create an academic record note
    if request.status == "closed":
        try:
            from app.modules.academic_records.service import create_record
            student_id = str(existing.get("student_id") or "")
            create_record(
                {
                    "record_type": "disciplinary_note",
                    "student_id": student_id,
                    "content": f"Disciplinary case {case_id} closed. Incident: {existing.get('incident_type', '')}.",
                    "source": "student_life",
                    "related_case_id": str(case_id),
                },
                tenant_id,
            )
        except Exception:
            pass  # academic_records wiring must never break disciplinary flow
    # W57 — trigger escalation alert when transitioning to escalation risk status
    if request.status in _DISCIPLINARY_ESCALATION_RISK_STATUSES:
        _ensure_disciplinary_escalation_alert(tenant_id, case_id, dict(updated))

    return DisciplinaryCaseSchema.model_validate(updated)


def get_student_life_health_snapshot(tenant_id: int) -> StudentLifeHealthSnapshotSchema:
    counseling_rows = list_entities_for_tenant("student_life_counseling_cases", tenant_id)
    wellbeing_rows = list_entities_for_tenant("student_life_wellbeing_checkins", tenant_id)
    accessibility_rows = list_entities_for_tenant("student_life_accessibility_supports", tenant_id)
    disciplinary_rows = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)

    open_counseling_cases = 0
    for row in counseling_rows:
        if str(row.get("status") or "") in {"open", "in_progress"}:
            open_counseling_cases += 1

    at_risk_wellbeing = 0
    for row in wellbeing_rows:
        status = str(row.get("status") or "")
        score = row.get("wellbeing_score")
        is_low_score = isinstance(score, int) and score <= 40
        if status == "at_risk" or is_low_score:
            at_risk_wellbeing += 1

    active_accessibility_supports = 0
    for row in accessibility_rows:
        if str(row.get("status") or "") in {"requested", "active"}:
            active_accessibility_supports += 1

    unresolved_disciplinary_cases = 0
    for row in disciplinary_rows:
        if str(row.get("status") or "") in {"reported", "under_review", "appealed"}:
            unresolved_disciplinary_cases += 1

    return StudentLifeHealthSnapshotSchema(
        tenant_id=tenant_id,
        counseling_cases_total=len(counseling_rows),
        open_counseling_cases=open_counseling_cases,
        wellbeing_checkins_total=len(wellbeing_rows),
        at_risk_wellbeing_checkins=at_risk_wellbeing,
        accessibility_supports_total=len(accessibility_rows),
        active_accessibility_supports=active_accessibility_supports,
        disciplinary_cases_total=len(disciplinary_rows),
        unresolved_disciplinary_cases=unresolved_disciplinary_cases,
    )