from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def list_records(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("academic_records", tenant_id)


def create_record(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("academic_records", payload, tenant_id)


def update_record(record_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("academic_records", record_id, payload, tenant_id)


def delete_record(record_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("academic_records", record_id, tenant_id)


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
    from app.platform.events.publisher import EventPublisher
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="academic_records.inconsistency.detected",
        aggregate_type="academic_records",
        aggregate_id=tenant_id,
        payload_json={
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
