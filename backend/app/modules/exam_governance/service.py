from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher
from app.modules.exam_governance.schemas import (
    ExamCreateSchema,
    ExamSchema,
    ExamUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ENTITY = "exams"

# W35: cap on active (scheduled/in_progress) exams per exam_type per term
_EXAM_TYPE_MAX_ACTIVE: dict[str, int] = {
    "midterm": 20,
    "final": 15,
    "quiz": 50,
    "practical": 10,
}

_ACTIVE_EXAM_STATUSES: frozenset[str] = frozenset({"scheduled", "in_progress"})

# W35: proctoring risk flag threshold
_HIGH_RISK_PROCTORING_MODES: frozenset[str] = frozenset({"remote", "hybrid"})

# W93: FSM — allowed status transitions for exam lifecycle
_ALLOWED_EXAM_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "scheduled": frozenset({"in_progress", "cancelled"}),
    "in_progress": frozenset({"completed", "cancelled"}),
    "completed": frozenset(),   # terminal
    "cancelled": frozenset(),   # terminal
}

# W93: activation statuses that require cross-entity faculty contract validation
_EXAM_ACTIVATION_STATUSES: frozenset[str] = frozenset({"in_progress"})

# W93: faculty contract statuses that count as active employment
_FACULTY_ACTIVE_CONTRACT_STATUSES: frozenset[str] = frozenset({"active", "draft", "pending"})


def _to_schema(row: dict) -> ExamSchema:
    return ExamSchema(
        id=row["id"],
        tenant_id=str(row.get("tenant_id", "")),
        course_code=row.get("course_code", ""),
        course_title=row.get("course_title", ""),
        faculty_id=row.get("faculty_id", ""),
        exam_type=row.get("exam_type", "midterm"),
        term_id=row.get("term_id", ""),
        status=row.get("status", "scheduled"),
        scheduled_date=row.get("scheduled_date"),
        scheduled_time=row.get("scheduled_time"),
        duration_minutes=int(row.get("duration_minutes") or 120),
        is_proctored=bool(row.get("is_proctored", True)),
        proctoring_mode=row.get("proctoring_mode", "in_person"),
    )


def _check_faculty_has_active_contract_for_exam_activation(
    *,
    tenant_id: int,
    faculty_id: str,
    exam_id: int,
    target_status: str,
) -> None:
    """W93: Cross-entity guard — exams × faculty_contracts.

    An exam cannot be activated (moved to in_progress) if the assigned faculty member
    has no active employment contract.  Starting an exam with a departed faculty member
    means no legitimate proctor is present — grades issued become contestable and may
    violate accreditation standards.

    HARDENING RULES:
    - Guard is surgical: only fires when target_status is in _EXAM_ACTIVATION_STATUSES.
    - faculty_id missing or empty → DomainValidationError (cannot identify who the proctor is).
    - faculty_contracts query failure → DomainValidationError (fail-closed, not silently granted).
    - No active contract found → DomainValidationError with rationale.
    """
    if target_status not in _EXAM_ACTIVATION_STATUSES:
        return  # surgical: only enforced on activation transition

    if not faculty_id or not faculty_id.strip():
        raise DomainValidationError(
            f"Cannot activate exam_id={exam_id}: faculty_id is missing or empty. "
            "An exam cannot be started (in_progress) without a named faculty proctor."
        )

    try:
        all_contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot activate exam_id={exam_id}: faculty_contracts lookup failed for "
            f"faculty_id={faculty_id!r}. Cannot verify faculty is still under active contract. "
            f"Reason: {exc}"
        ) from exc

    faculty_contracts = [
        c for c in all_contracts if str(c.get("faculty_id") or "") == faculty_id
    ]

    # Only enforce if there ARE contracts for this faculty (tracking is set up).
    # If no contracts exist at all, the system is not tracking employment for this faculty.
    if not faculty_contracts:
        return

    active_contracts = [
        c
        for c in faculty_contracts
        if str(c.get("status") or "") in _FACULTY_ACTIVE_CONTRACT_STATUSES
    ]

    if not active_contracts:
        raise DomainValidationError(
            f"Cannot activate exam_id={exam_id}: faculty_id={faculty_id!r} has no active "
            f"employment contract (checked statuses: {sorted(_FACULTY_ACTIVE_CONTRACT_STATUSES)}). "
            "An exam cannot be started with a faculty member who is not currently employed. "
            "Assign an active faculty member or reinstate the faculty contract before activation."
        )


def list_exams(
    tenant_id: int,
    *,
    status: str | None = None,
    term_id: str | None = None,
) -> list[ExamSchema]:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if term_id:
        rows = [r for r in rows if r.get("term_id") == term_id]
    return [_to_schema(r) for r in rows]


def _ensure_proctoring_alert_record(
    tenant_id: int,
    exam_id: int,
    exam_data: dict,
) -> None:
    """Idempotent: create an exam_proctoring_alerts entry for remote/hybrid proctoring exams."""
    existing = list_entities_for_tenant("exam_proctoring_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "exam_proctoring_risk"
            and str(rec.get("source_entity_id")) == str(exam_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "exam_proctoring_alerts",
        {
            "exam_id": exam_id,
            "course_code": str(exam_data.get("course_code") or ""),
            "proctoring_mode": str(exam_data.get("proctoring_mode") or "remote"),
            "alert_status": "open",
            "integration_source": "exam_proctoring_risk",
            "source_entity_id": str(exam_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="exam.violation_detected",
            aggregate_type="exam",
            aggregate_id=exam_id,
            payload_json={
                "exam_id": exam_id,
                "course_code": str(exam_data.get("course_code") or ""),
                "proctoring_mode": str(exam_data.get("proctoring_mode") or "remote"),
                "violation_type": "proctoring_risk",
            },
        )
    except Exception:  # noqa: BLE001 — events must never break core flow
        pass


def create_exam(tenant_id: int, payload: ExamCreateSchema, actor: str) -> ExamSchema:
    exam_type_key = payload.exam_type
    cap = _EXAM_TYPE_MAX_ACTIVE.get(exam_type_key, 20)
    existing = list_entities_for_tenant(_ENTITY, tenant_id)
    active_count = sum(
        1
        for e in existing
        if str(e.get("exam_type") or "") == exam_type_key
        and str(e.get("status") or "") in _ACTIVE_EXAM_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active exam cap ({cap}) reached for exam_type '{exam_type_key}'"
        )

    data = payload.model_dump()
    row = create_entity_for_tenant(_ENTITY, data, tenant_id)
    log_admin_action(
        actor=actor,
        action="exam.create",
        path="/api/admin/exam-governance",
        client_ip="service",
        entity="exam",
        metadata={"course_code": payload.course_code, "exam_type": payload.exam_type},
        tenant_id=tenant_id,
    )

    if payload.proctoring_mode in _HIGH_RISK_PROCTORING_MODES:
        _ensure_proctoring_alert_record(
            tenant_id=tenant_id,
            exam_id=int(row.get("id") or 0),
            exam_data={
                "course_code": payload.course_code,
                "proctoring_mode": payload.proctoring_mode,
            },
        )

    schema = _to_schema(row)
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="exam.created",
            aggregate_type="exam",
            aggregate_id=schema.id,
            payload_json={
                "exam_id": schema.id,
                "course_code": schema.course_code,
                "exam_type": schema.exam_type,
                "term_id": schema.term_id,
                "actor": actor,
            },
        )
    except Exception:  # noqa: BLE001 — events must never break core flow
        pass
    record_usage_event(tenant_id, "exams_created", 1)
    return schema


def update_exam(
    tenant_id: int, exam_id: int, payload: ExamUpdateSchema, actor: str
) -> ExamSchema:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}

    # Always read current row to enable merged updates (required field validation)
    all_rows = list_entities_for_tenant(_ENTITY, tenant_id)
    current_row = next((r for r in all_rows if r["id"] == exam_id), None)
    if current_row is None:
        raise ValueError(f"Exam {exam_id} not found")

    if not updates:
        return _to_schema(current_row)

    # W93: FSM transition guard + cross-entity faculty contract validation
    if payload.status is not None:
        current_status = str(current_row.get("status") or "scheduled")
        allowed_next = _ALLOWED_EXAM_STATUS_TRANSITIONS.get(current_status, frozenset())
        if payload.status not in allowed_next:
            terminal_note = " (terminal state — no further transitions allowed)" if not allowed_next else ""
            raise DomainValidationError(
                f"Cannot transition exam_id={exam_id} from status={current_status!r} "
                f"to {payload.status!r}. "
                f"Allowed next statuses: {sorted(allowed_next) or ['none']}{terminal_note}."
            )
        # Cross-entity guard: faculty must have active contract to activate exam
        _check_faculty_has_active_contract_for_exam_activation(
            tenant_id=tenant_id,
            faculty_id=str(current_row.get("faculty_id") or ""),
            exam_id=exam_id,
            target_status=payload.status,
        )

    # Merge current row data with updates to satisfy required field validation
    merged_payload = {k: v for k, v in current_row.items() if k != "id"}
    merged_payload.update(updates)
    row = update_entity_for_tenant(_ENTITY, exam_id, merged_payload, tenant_id)
    if row is None:
        raise ValueError(f"Exam {exam_id} not found")
    log_admin_action(
        actor=actor,
        action="exam.update",
        path=f"/api/admin/exam-governance/{exam_id}",
        client_ip="service",
        entity="exam",
        metadata={"exam_id": exam_id, "updates": list(updates.keys())},
        tenant_id=tenant_id,
    )
    schema = _to_schema(row)
    if payload.status in {"in_progress", "completed"}:
        event_type = "exam.started" if payload.status == "in_progress" else "exam.submitted"
        try:
            EventPublisher().publish_event(
                tenant_id=tenant_id,
                event_type=event_type,
                aggregate_type="exam",
                aggregate_id=exam_id,
                payload_json={
                    "exam_id": exam_id,
                    "status": payload.status,
                    "actor": actor,
                },
            )
        except Exception:  # noqa: BLE001 — events must never break core flow
            pass
    record_usage_event(tenant_id, "exam_status_updates", 1)
    return schema


def get_exam_dashboard_summary(tenant_id: int) -> dict:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    status_breakdown: dict[str, int] = {
        "scheduled": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0,
    }
    type_breakdown: dict[str, int] = {
        "midterm": 0,
        "final": 0,
        "quiz": 0,
        "practical": 0,
    }
    for row in rows:
        s = row.get("status", "scheduled")
        if s in status_breakdown:
            status_breakdown[s] += 1
        t = row.get("exam_type", "midterm")
        if t in type_breakdown:
            type_breakdown[t] += 1
    return {
        "total_exams": len(rows),
        "status_breakdown": status_breakdown,
        "exam_type_breakdown": type_breakdown,
    }


def get_exam_statistics(tenant_id: int, exam_id: int) -> dict:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    row = next((r for r in rows if r["id"] == exam_id), None)
    if row is None:
        raise ValueError(f"Exam {exam_id} not found")
    return {
        "exam_id": exam_id,
        "total_registrations": 0,
        "completion_rate": 0.0,
        "average_score": None,
        "pass_rate": None,
    }


def grade_exam(
    tenant_id: int,
    exam_id: int,
    average_score: float,
    pass_rate: float,
    actor: str,
) -> dict:
    """Record grade summary for a completed exam and publish exam.graded event."""
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    row = next((r for r in rows if r["id"] == exam_id), None)
    if row is None:
        raise ValueError(f"Exam {exam_id} not found")
    if str(row.get("status") or "") != "completed":
        raise DomainValidationError(
            f"Cannot grade exam_id={exam_id}: exam must be in 'completed' status "
            f"(current: {row.get('status')!r}). Complete the exam before grading."
        )
    log_admin_action(
        actor=actor,
        action="exam.grade",
        path=f"/api/admin/exam-governance/{exam_id}/grade",
        client_ip="service",
        entity="exam",
        metadata={"exam_id": exam_id, "average_score": average_score, "pass_rate": pass_rate},
        tenant_id=tenant_id,
    )
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="exam.graded",
            aggregate_type="exam",
            aggregate_id=exam_id,
            payload_json={
                "exam_id": exam_id,
                "average_score": average_score,
                "pass_rate": pass_rate,
                "actor": actor,
            },
        )
    except Exception:  # noqa: BLE001 — events must never break core flow
        pass
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            exam_id,
            payload={
                "outcome_type": "exam_graded",
                "effectiveness": "positive" if pass_rate >= 0.5 else "neutral",
                "source_module": "exam_governance",
                "exam_id": exam_id,
                "average_score": average_score,
                "pass_rate": pass_rate,
            },
            actor=actor,
        )
    except Exception:  # noqa: BLE001 — brain core must never break core flow
        pass
    record_usage_event(tenant_id, "exams_graded", 1)
    return {
        "exam_id": exam_id,
        "average_score": average_score,
        "pass_rate": pass_rate,
        "graded_by": actor,
        "status": "graded",
    }
