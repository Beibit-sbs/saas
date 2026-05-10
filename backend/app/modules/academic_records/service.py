from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher

_ACADEMIC_RECORD_STATUS_MAX_ACTIVE: dict[str, int] = {
    "published": 2000,
    "draft": 500,
    "pending": 300,
    "archived": 5000,
    "withdrawn": 1000,
}
_ACTIVE_RECORD_STATUSES = frozenset({"published", "draft", "pending"})
_WITHDRAWAL_RISK_STATUSES = frozenset({"withdrawn"})
_ENROLLMENT_ELIGIBLE_STATUSES = frozenset({"active", "enrolled", "registered", "completed", "withdrawn"})


def _fire(tenant_id: int, event_type: str, aggregate_type: str, aggregate_id: str | int, payload: dict[str, object]) -> None:
    try:
        publisher_cls = EventPublisher
        if "unittest.mock" not in type(EventPublisher).__module__:
            from app.platform.events import publisher as publisher_module

            publisher_cls = publisher_module.EventPublisher

        publisher_cls().publish_event(
            tenant_id=int(tenant_id),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload_json=payload,
        )
    except Exception:
        pass


def _record_outcome(record_id: str | int, outcome: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            str(record_id),
            payload={
                "outcome_type": outcome,
                "source_module": "academic_records",
                "record_id": str(record_id),
            },
            actor=actor,
        )
    except Exception:
        pass


def _audit(tenant_id: int, actor: str, action: str, record_id: str | int, metadata: dict[str, object]) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=f"/internal/academic-records/{record_id}",
            client_ip="service",
            entity="academic_records",
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

def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _check_enrollment_exists_for_academic_record(
    *,
    tenant_id: int,
    student_id: int,
    course_id: int,
    semester: str,
) -> None:
    """W118: Cross-entity guard — academic_records × enrollments.

    Academic records are official transcript artifacts and may only be created for
    a verifiable student-course enrollment relationship in the same term.

    FAIL-CLOSED: if enrollments lookup fails, creation is blocked.
    """
    try:
        enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            "Academic record creation blocked: enrollments lookup failed. "
            f"student_id={student_id}, course_id={course_id}, semester='{semester}'."
        ) from exc

    target_semester = str(semester or "").strip().lower()
    matches = []
    for row in enrollments:
        row_student_id = _safe_int(row.get("student_id"))
        row_course_id = _safe_int(row.get("course_id"))
        if row_student_id != student_id or row_course_id != course_id:
            continue

        row_status = str(row.get("status") or row.get("enrollment_status") or "").strip().lower()
        if row_status not in _ENROLLMENT_ELIGIBLE_STATUSES:
            continue

        row_semester = str(
            row.get("semester")
            or row.get("term")
            or row.get("academic_term")
            or ""
        ).strip().lower()
        if row_semester and target_semester and row_semester != target_semester:
            continue

        matches.append(row)

    if not matches:
        raise DomainValidationError(
            "Academic record creation blocked: no eligible enrollment found for "
            f"student_id={student_id}, course_id={course_id}, semester='{semester}'. "
            "Transcript records require a valid enrollment relationship."
        )


def list_records(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("academic_records", tenant_id)


def create_record(payload: dict[str, object], tenant_id: int, actor: str = "system") -> dict[str, object]:
    student_id = _safe_int(payload.get("student_id"))
    course_id = _safe_int(payload.get("course_id"))
    semester = str(payload.get("semester") or "").strip()
    if student_id is None or student_id <= 0:
        raise ValueError("student_id must be a positive integer")
    if course_id is None or course_id <= 0:
        raise ValueError("course_id must be a positive integer")
    if not semester:
        raise ValueError("semester is required")

    _check_enrollment_exists_for_academic_record(
        tenant_id=tenant_id,
        student_id=student_id,
        course_id=course_id,
        semester=semester,
    )

    record_status = str(payload.get("status") or "pending").strip().lower()
    all_records = list_entities_for_tenant("academic_records", tenant_id)
    active_count = sum(
        1 for r in all_records
        if str(r.get("status", "")).strip().lower() in _ACTIVE_RECORD_STATUSES
    )
    cap = _ACADEMIC_RECORD_STATUS_MAX_ACTIVE.get(record_status, 2000)
    if active_count >= cap:
        raise ValueError(
            f"Active academic record cap reached for status '{record_status}': {active_count}/{cap}"
        )
    created = create_entity_for_tenant("academic_records", payload, tenant_id)
    record_id = created.get("id", "")

    _fire(
        tenant_id,
        "academic_records.record.created",
        "academic_record",
        record_id,
        {
            "record_id": record_id,
            "student_id": created.get("student_id"),
            "course_id": created.get("course_id"),
            "status": created.get("status"),
            "semester": created.get("semester"),
            "source_module": "academic_records",
        },
    )
    _record_outcome(record_id, "record_created", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("academic_records", "record", "create"),
        record_id,
        {
            "record_id": record_id,
            "student_id": created.get("student_id"),
            "course_id": created.get("course_id"),
            "status": created.get("status"),
        },
    )
    _metric(tenant_id, "academic_records_created", 1)
    return created


def update_record(record_id: int, payload: dict[str, object], tenant_id: int, actor: str = "system") -> dict[str, object]:
    _check_record_not_published(record_id, tenant_id)
    result = update_entity_for_tenant("academic_records", record_id, payload, tenant_id)
    to_status = str(payload.get("status") or "").strip().lower()
    if to_status in _WITHDRAWAL_RISK_STATUSES:
        _ensure_withdrawal_alert_record(record_id, tenant_id)

    _fire(
        tenant_id,
        "academic_records.record.updated",
        "academic_record",
        record_id,
        {
            "record_id": record_id,
            "status": result.get("status"),
            "grade": result.get("grade"),
            "source_module": "academic_records",
        },
    )
    _record_outcome(record_id, "record_updated", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("academic_records", "record", "update"),
        record_id,
        {
            "record_id": record_id,
            "status": result.get("status"),
            "grade": result.get("grade"),
        },
    )
    _metric(tenant_id, "academic_records_updated", 1)
    return result


def _check_record_not_published(record_id: int, tenant_id: int) -> None:
    """Immutability guard: a published academic record must not be mutated.

    Published records are official institutional documents. Any correction requires
    a formal correction workflow — direct update is forbidden once a record reaches
    'published' status to prevent silent corruption of official academic documentation.

    Silently proceeds when the record cannot be found (not-found is a separate concern).
    """
    all_records = list_entities_for_tenant("academic_records", tenant_id)
    for rec in all_records:
        if _safe_int(rec.get("id")) == record_id:
            current_status = str(rec.get("status") or "").strip().lower()
            if current_status == "published":
                raise ValueError(
                    f"Academic record {record_id} is published and immutable: "
                    "direct update is forbidden. Use a formal correction workflow."
                )
            return


def _ensure_withdrawal_alert_record(record_id: int, tenant_id: int) -> None:
    """Idempotently create a withdrawal alert for a withdrawn academic record."""
    existing = list_entities_for_tenant("academic_withdrawal_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source") or "").strip() == "academic_records_withdrawal_queue"
            and str(rec.get("source_entity_id") or "").strip() == str(record_id)
        ):
            return
    create_entity_for_tenant(
        "academic_withdrawal_alerts",
        {
            "record_id": record_id,
            "alert_type": "record_withdrawn",
            "integration_source": "academic_records_withdrawal_queue",
            "source_entity_id": str(record_id),
        },
        tenant_id,
    )
    _fire(
        tenant_id,
        "campus.academic_records.withdrawal_risk_detected",
        "academic_record",
        record_id,
        {
            "record_id": record_id,
            "alert_type": "record_withdrawn",
            "source_module": "academic_records",
        },
    )


def delete_record(record_id: int, tenant_id: int, actor: str = "system") -> dict[str, object]:
    deleted = delete_entity_for_tenant("academic_records", record_id, tenant_id)

    _fire(
        tenant_id,
        "academic_records.record.deleted",
        "academic_record",
        record_id,
        {
            "record_id": record_id,
            "student_id": deleted.get("student_id"),
            "course_id": deleted.get("course_id"),
            "source_module": "academic_records",
        },
    )
    _record_outcome(record_id, "record_deleted", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("academic_records", "record", "delete"),
        record_id,
        {
            "record_id": record_id,
            "student_id": deleted.get("student_id"),
            "course_id": deleted.get("course_id"),
        },
    )
    _metric(tenant_id, "academic_records_deleted", 1)
    return deleted


def get_record_consistency_report(tenant_id: int) -> dict[str, object]:
    records = list_entities_for_tenant("academic_records", tenant_id)
    students = list_entities_for_tenant("students", tenant_id)
    courses = list_entities_for_tenant("courses", tenant_id)

    student_ids = {
        sid for sid in (_safe_int(student.get("id")) for student in students) if sid is not None
    }
    course_ids = {
        cid for cid in (_safe_int(course.get("id")) for course in courses) if cid is not None
    }

    allowed_statuses = {"published", "draft", "pending", "archived", "withdrawn"}
    allowed_grades = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "P", "NP", "I", "W"}

    issues: list[dict[str, object]] = []
    enrollment_keys: dict[tuple[int | None, int | None, str], int] = {}

    for record in records:
        record_id = _safe_int(record.get("id"))
        student_id = _safe_int(record.get("student_id"))
        course_id = _safe_int(record.get("course_id"))
        grade_raw = record.get("grade")
        semester_raw = record.get("semester")
        status_raw = record.get("status")

        if record_id is None:
            continue

        missing_student = student_id is None or student_id not in student_ids
        missing_course = course_id is None or course_id not in course_ids

        if missing_student and missing_course:
            issues.append(
                {
                    "issue_type": "record_orphaned_references",
                    "record_id": record_id,
                    "student_id": student_id,
                    "course_id": course_id,
                }
            )
        elif missing_student:
            issues.append(
                {
                    "issue_type": "record_missing_student",
                    "record_id": record_id,
                    "student_id": student_id,
                    "course_id": course_id,
                }
            )
        elif missing_course:
            issues.append(
                {
                    "issue_type": "record_missing_course",
                    "record_id": record_id,
                    "student_id": student_id,
                    "course_id": course_id,
                }
            )

        status = str(status_raw).strip().lower() if status_raw is not None else ""
        if not status:
            issues.append({"issue_type": "record_missing_status", "record_id": record_id})
        elif status not in allowed_statuses:
            issues.append(
                {
                    "issue_type": "record_invalid_status",
                    "record_id": record_id,
                    "status": status_raw,
                }
            )

        grade = str(grade_raw).strip().upper() if grade_raw is not None else ""
        if grade and grade not in allowed_grades:
            issues.append(
                {
                    "issue_type": "record_invalid_grade",
                    "record_id": record_id,
                    "grade": grade_raw,
                }
            )

        semester = str(semester_raw).strip() if semester_raw is not None else ""
        if not semester:
            issues.append({"issue_type": "record_missing_semester", "record_id": record_id})
        else:
            parts = semester.split("-")
            if len(parts) != 2:
                issues.append(
                    {
                        "issue_type": "record_invalid_semester_format",
                        "record_id": record_id,
                        "semester": semester_raw,
                    }
                )

        enrollment_key = (student_id, course_id, semester)
        if enrollment_key != (None, None, "") and not missing_student and not missing_course:
            enrollment_keys[enrollment_key] = enrollment_keys.get(enrollment_key, 0) + 1

    for (student_id, course_id, semester), count in enrollment_keys.items():
        if count > 1 and semester:
            for record in records:
                r_id = _safe_int(record.get("id"))
                if (
                    r_id is not None
                    and _safe_int(record.get("student_id")) == student_id
                    and _safe_int(record.get("course_id")) == course_id
                    and str(record.get("semester")).strip() == semester
                ):
                    issues.append(
                        {
                            "issue_type": "record_duplicate_enrollment",
                            "record_id": r_id,
                            "student_id": student_id,
                            "course_id": course_id,
                            "semester": semester,
                        }
                    )

    return {
        "record_count": len(records),
        "issue_count": len(issues),
        "issues": issues,
    }


def emit_academic_records_inconsistency_signal(tenant_id: int, issue_count: int) -> None:
    _fire(
        tenant_id,
        "academic_records.inconsistency.detected",
        "academic_records",
        tenant_id,
        {
            "issue_count": issue_count,
            "source_module": "academic_records",
        },
    )


def get_academic_records_brain_context(tenant_id: int) -> dict[str, object]:
    """Return aggregated brain-context snapshot for Brain Core context builder."""
    report = get_record_consistency_report(tenant_id)
    issue_count = int(report.get("issue_count", 0))
    record_count = int(report.get("record_count", 0))
    return {
        "snapshot_type": "brain_context",
        "module": "academic_records",
        "tenant_id": tenant_id,
        "total_records": record_count,
        "inconsistency_count": issue_count,
        "records_risk_level": "high" if issue_count > 10 else ("medium" if issue_count > 0 else "low"),
    }
