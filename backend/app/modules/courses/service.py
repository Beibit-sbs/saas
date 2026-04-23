from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.modules.billing.service import assert_billing_write_allowed


def list_courses(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("courses", tenant_id)


def create_course(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    assert_billing_write_allowed(int(tenant_id), action="courses.create")
    return create_entity_for_tenant("courses", payload, tenant_id)


def update_course(course_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    assert_billing_write_allowed(int(tenant_id), action="courses.update")
    result = update_entity_for_tenant("courses", course_id, payload, tenant_id)
    to_status = str(payload.get("status") or "").strip().lower()
    if to_status in {"inactive", "archived"}:
        from app.platform.events.publisher import EventPublisher
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="courses.status.risk_detected",
            aggregate_type="course",
            aggregate_id=course_id,
            payload_json={
                "course_id": course_id,
                "to_status": to_status,
                "source_module": "courses",
            },
        )
    return result


def delete_course(course_id: int, tenant_id: int) -> dict[str, object]:
    assert_billing_write_allowed(int(tenant_id), action="courses.delete")
    return delete_entity_for_tenant("courses", course_id, tenant_id)


def get_course_consistency_report(tenant_id: int) -> dict[str, object]:
    courses = list_entities_for_tenant("courses", tenant_id)
    programs = list_entities_for_tenant("programs", tenant_id)

    program_ids = {
        int(program_id)
        for program_id in (program.get("id") for program in programs)
        if program_id is not None
    }

    allowed_statuses = {"active", "inactive", "archived", "draft"}
    code_counts: dict[str, int] = {}
    for course in courses:
        code_raw = course.get("course_code")
        code = str(code_raw).strip() if code_raw is not None else ""
        if code:
            code_counts[code] = code_counts.get(code, 0) + 1
    duplicate_codes = {code for code, count in code_counts.items() if count > 1}

    issues: list[dict[str, object]] = []
    for course in courses:
        course_id_raw = course.get("id")
        program_id_raw = course.get("program_id")
        code_raw = course.get("course_code")
        title_raw = course.get("title")
        credits_raw = course.get("credits")
        status_raw = course.get("status")

        try:
            course_id = int(course_id_raw)
        except (TypeError, ValueError):
            continue

        try:
            program_id = int(program_id_raw)
        except (TypeError, ValueError):
            program_id = None

        if program_id is None or program_id not in program_ids:
            issues.append(
                {
                    "issue_type": "course_missing_program",
                    "course_id": course_id,
                    "program_id": program_id,
                }
            )

        code = str(code_raw).strip() if code_raw is not None else ""
        if not code:
            issues.append({"issue_type": "course_missing_code", "course_id": course_id})
        elif code in duplicate_codes:
            issues.append(
                {
                    "issue_type": "duplicate_course_code",
                    "course_id": course_id,
                    "course_code": code,
                }
            )

        title = str(title_raw).strip() if title_raw is not None else ""
        if not title:
            issues.append({"issue_type": "course_missing_title", "course_id": course_id})

        try:
            credits = int(credits_raw)
            if credits <= 0:
                raise ValueError
        except (TypeError, ValueError):
            issues.append(
                {
                    "issue_type": "course_invalid_credits",
                    "course_id": course_id,
                    "credits": credits_raw,
                }
            )

        status = str(status_raw).strip().lower() if status_raw is not None else ""
        if status not in allowed_statuses:
            issues.append(
                {
                    "issue_type": "course_invalid_status",
                    "course_id": course_id,
                    "status": status_raw,
                }
            )

    return {
        "course_count": len(courses),
        "issue_count": len(issues),
        "issues": issues,
    }


def get_courses_brain_context(tenant_id: int) -> dict[str, object]:
    """Return aggregated brain-context snapshot for Brain Core context builder."""
    courses = list_entities_for_tenant("courses", tenant_id)
    report = get_course_consistency_report(tenant_id)
    active = sum(1 for c in courses if str(c.get("status", "")).lower() == "active")
    issue_count = int(report.get("issue_count", 0))
    return {
        "snapshot_type": "brain_context",
        "module": "courses",
        "tenant_id": tenant_id,
        "total_courses": len(courses),
        "active_courses": active,
        "inconsistency_count": issue_count,
        "courses_risk_level": "high" if issue_count > 10 else ("medium" if issue_count > 0 else "low"),
    }
