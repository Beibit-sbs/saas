import logging

from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.modules.billing.service import assert_billing_write_allowed

logger = logging.getLogger("app.modules.courses")


# ---------------------------------------------------------------------------
# Canonical fail-safe helpers (Steps 5 / 8 / 9 / 10)
# ---------------------------------------------------------------------------

def _fire(
    tenant_id: int,
    event_type: str,
    aggregate_type: str,
    aggregate_id: int | str,
    payload_json: dict,
) -> None:
    try:
        from app.platform.events.publisher import EventPublisher
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=payload_json,
        )
    except Exception:
        logger.exception(
            "courses event publish failed tenant_id=%s event_type=%s aggregate_id=%s",
            tenant_id, event_type, aggregate_id,
        )


def _record_outcome(
    tenant_id: int,
    entity_id: int | str,
    outcome_type: str,
) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service
        brain_core_service.record_dispatch_outcome(
            tenant_id=tenant_id,
            entity_id=str(entity_id),
            outcome_type=outcome_type,
        )
    except Exception:
        logger.exception(
            "courses outcome failed entity_id=%s outcome_type=%s",
            entity_id, outcome_type,
        )


def _audit(
    actor: str,
    action: str,
    entity: str,
    entity_id: int | str,
    path: str,
) -> None:
    try:
        from app.modules.audit.service import log_admin_action, build_audit_action
        log_admin_action(
            build_audit_action(
                user=actor,
                action=action,
                entity=entity,
                path=path,
                result="success",
                correlation_id=str(entity_id),
            )
        )
    except Exception:
        logger.exception("courses audit failed action=%s entity_id=%s", action, entity_id)


def _metric(tenant_id: int, metric_name: str, value: int = 1) -> None:
    try:
        from app.modules.usage.service import record_usage_event
        record_usage_event(tenant_id, metric_name, value)
    except Exception:
        logger.exception("courses metric failed metric_name=%s", metric_name)

# W45: cap on active courses per status per tenant
_COURSE_STATUS_MAX_ACTIVE: dict[str, int] = {
    "active": 500,
    "draft": 200,
    "inactive": 300,
    "archived": 1000,
}

_ACTIVE_COURSE_STATUSES: frozenset[str] = frozenset({"active", "draft"})

# W45: statuses that trigger a course retirement alert
_RETIREMENT_RISK_STATUSES: frozenset[str] = frozenset({"inactive", "archived"})


def list_courses(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("courses", tenant_id)


def create_course(
    payload: dict[str, object],
    tenant_id: int,
    actor: str = "system",
) -> dict[str, object]:
    assert_billing_write_allowed(int(tenant_id), action="courses.create")
    existing = list_entities_for_tenant("courses", tenant_id)

    # W45: count-cap guard on active courses by status
    course_status = str(payload.get("status") or "").strip().lower()
    cap = _COURSE_STATUS_MAX_ACTIVE.get(course_status, 500)
    active_count = sum(
        1 for c in existing
        if str(c.get("status") or "").strip().lower() in _ACTIVE_COURSE_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active course cap ({cap}) reached; cannot create new course with status '{course_status}'"
        )

    result = create_entity_for_tenant("courses", payload, tenant_id)
    course_id = result.get("id", 0)

    # Step 5: event
    _fire(tenant_id, "courses.course.created", "course", course_id, {"course_id": course_id, "status": course_status})
    # Step 8: outcome
    _record_outcome(tenant_id, course_id, "course_created")
    # Step 9: audit
    _audit(actor, "courses.create", "course", course_id, "/internal/courses")
    # Step 10: metric
    _metric(tenant_id, "courses_created")

    return result


def update_course(
    course_id: int,
    payload: dict[str, object],
    tenant_id: int,
    actor: str = "system",
) -> dict[str, object]:
    assert_billing_write_allowed(int(tenant_id), action="courses.update")
    result = update_entity_for_tenant("courses", course_id, payload, tenant_id)
    to_status = str(payload.get("status") or "").strip().lower()
    if to_status in {"inactive", "archived"}:
        _fire(
            tenant_id,
            "courses.status.risk_detected",
            "course",
            course_id,
            {"course_id": course_id, "to_status": to_status, "source_module": "courses"},
        )
    # W45: side-effect retirement alert for risk statuses
    if to_status in _RETIREMENT_RISK_STATUSES:
        _ensure_retirement_alert_record(
            tenant_id=tenant_id,
            course_id=course_id,
            course_data={
                "course_code": str(payload.get("course_code") or ""),
                "program_id": str(payload.get("program_id") or ""),
                "status": to_status,
            },
        )

    # Step 8: outcome
    _record_outcome(tenant_id, course_id, "course_updated")
    # Step 9: audit
    _audit(actor, "courses.update", "course", course_id, f"/internal/courses/{course_id}")
    # Step 10: metric
    _metric(tenant_id, "courses_updated")

    return result


def _ensure_retirement_alert_record(
    tenant_id: int,
    course_id: int,
    course_data: dict,
) -> None:
    """Idempotent: create a course_retirement_alerts entry for inactive/archived courses."""
    src = "courses_retirement_queue"
    src_id = str(course_id)
    existing = list_entities_for_tenant("course_retirement_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == src
            and str(rec.get("source_entity_id")) == src_id
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "course_retirement_alerts",
        {
            "course_id": course_id,
            "course_code": str(course_data.get("course_code") or ""),
            "program_id": str(course_data.get("program_id") or ""),
            "retirement_status": str(course_data.get("status") or ""),
            "alert_status": "open",
            "integration_source": src,
            "source_entity_id": src_id,
        },
        tenant_id,
    )


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
