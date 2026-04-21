from statistics import pstdev

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


def _safe_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_role(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_instructor_id(value: object) -> str:
    return str(value or "").strip()


def _list_scheduling_workload_rows(tenant_id: int, term_id: int) -> list[dict[str, object]]:
    """Return instructor workload rows for a term.

    Uses scheduling sections as workload source when available in tenant entity
    storage. Each section is mapped as a primary assignment by default to keep
    legacy compatibility where explicit role is not tracked.
    """
    try:
        sections = list_entities_for_tenant("scheduling_sections", tenant_id)
    except ValueError:
        return []

    rows: list[dict[str, object]] = []
    for section in sections:
        if _safe_int(section.get("term_id")) != term_id:
            continue
        rows.append(
            {
                "term_id": section.get("term_id"),
                "course_id": section.get("course_id"),
                "instructor_id": section.get("instructor_id"),
                "role": section.get("role") or "primary",
            }
        )
    return rows


def list_faculty(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("faculty", tenant_id)


def list_faculty_contracts(
    tenant_id: int,
    faculty_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    faculty_filter = str(faculty_id or "").strip()
    status_filter = str(status or "").strip().lower()

    filtered: list[dict[str, object]] = []
    for row in contracts:
        row_faculty_id = str(row.get("faculty_id") or "").strip()
        row_status = str(row.get("status") or "").strip().lower()
        if faculty_filter and row_faculty_id != faculty_filter:
            continue
        if status_filter and row_status != status_filter:
            continue
        filtered.append(row)
    return filtered


def create_faculty_contract(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    faculty_id = str(payload.get("faculty_id") or "").strip()
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    faculty_exists = any(str(row.get("faculty_id") or "").strip() == faculty_id for row in faculty_rows)
    if not faculty_exists:
        raise ValueError("faculty not found")
    return create_entity_for_tenant("faculty_contracts", payload, tenant_id)


def update_faculty_contract_status(
    contract_id: int,
    status: str,
    tenant_id: int,
    notes: str | None = None,
) -> dict[str, object]:
    current = list_entities_for_tenant("faculty_contracts", tenant_id)
    row = next((item for item in current if _safe_int(item.get("id")) == contract_id), None)
    if row is None:
        raise ValueError("faculty_contract not found")

    updated_payload = dict(row)
    updated_payload["status"] = status
    if notes is not None:
        updated_payload["notes"] = notes
    return update_entity_for_tenant("faculty_contracts", contract_id, updated_payload, tenant_id)


def create_faculty_member(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("faculty", payload, tenant_id)


def update_faculty_member(faculty_row_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("faculty", faculty_row_id, payload, tenant_id)


def delete_faculty_member(faculty_row_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("faculty", faculty_row_id, tenant_id)


def get_faculty_consistency_report(tenant_id: int) -> dict[str, object]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)

    issues: list[dict[str, object]] = []
    faculty_id_counts: dict[str, int] = {}
    email_counts: dict[str, int] = {}
    allowed_statuses = {"active", "inactive", "on_leave", "sabbatical"}

    for row in faculty_rows:
        row_id_raw = row.get("id")
        faculty_id_raw = row.get("faculty_id")
        email_raw = row.get("email")

        try:
            row_id = int(row_id_raw)
        except (TypeError, ValueError):
            row_id = None

        faculty_id = str(faculty_id_raw).strip() if faculty_id_raw is not None else ""
        email = str(email_raw).strip() if email_raw is not None else ""
        normalized_email = email.lower()
        status = str(row.get("status") or "").strip().lower()

        if not faculty_id:
            issues.append(
                {
                    "issue_type": "faculty_missing_identifier",
                    "faculty_row_id": row_id,
                    "email": email or None,
                }
            )
        else:
            faculty_id_counts[faculty_id] = faculty_id_counts.get(faculty_id, 0) + 1

        if not email:
            issues.append(
                {
                    "issue_type": "faculty_missing_email",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id or None,
                }
            )
        else:
            email_counts[normalized_email] = email_counts.get(normalized_email, 0) + 1
            if "@" not in normalized_email or normalized_email.startswith("@") or normalized_email.endswith("@"):
                issues.append(
                    {
                        "issue_type": "faculty_invalid_email_format",
                        "faculty_row_id": row_id,
                        "faculty_id": faculty_id or None,
                        "email": email,
                    }
                )

        if not status or status not in allowed_statuses:
            issues.append(
                {
                    "issue_type": "faculty_invalid_status",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id or None,
                    "email": email or None,
                }
            )

    duplicate_faculty_ids = {
        faculty_id for faculty_id, count in faculty_id_counts.items() if count > 1
    }
    duplicate_emails = {
        email for email, count in email_counts.items() if count > 1
    }

    for row in faculty_rows:
        row_id_raw = row.get("id")
        faculty_id_raw = row.get("faculty_id")
        email_raw = row.get("email")
        try:
            row_id = int(row_id_raw)
        except (TypeError, ValueError):
            row_id = None

        faculty_id = str(faculty_id_raw).strip() if faculty_id_raw is not None else ""
        email = str(email_raw).strip() if email_raw is not None else ""
        normalized_email = email.lower()

        if faculty_id and faculty_id in duplicate_faculty_ids:
            issues.append(
                {
                    "issue_type": "duplicate_faculty_identifier",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id,
                    "email": email or None,
                }
            )

        if email and normalized_email in duplicate_emails:
            issues.append(
                {
                    "issue_type": "duplicate_faculty_email",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id or None,
                    "email": email,
                }
            )

    return {
        "faculty_count": len(faculty_rows),
        "issue_count": len(issues),
        "issues": issues,
    }


def get_faculty_workload(tenant_id: int, faculty_id: str, term_id: int) -> dict[str, object]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    courses = list_entities_for_tenant("courses", tenant_id)
    workload_rows = _list_scheduling_workload_rows(tenant_id, term_id)

    faculty_row = next((row for row in faculty_rows if str(row.get("faculty_id") or "").strip() == faculty_id), None)
    if faculty_row is None:
        raise ValueError("faculty not found")

    course_credits: dict[int, int] = {}
    for row in courses:
        course_id = _safe_int(row.get("id"))
        credits = _safe_int(row.get("credits"))
        if course_id is not None:
            course_credits[course_id] = credits or 0

    total_credit_hours = 0
    primary_assignments = 0
    assistant_assignments = 0

    for row in workload_rows:
        if _normalize_instructor_id(row.get("instructor_id")) != faculty_id:
            continue
        if _safe_int(row.get("term_id")) != term_id:
            continue

        role = _normalize_role(row.get("role"))
        course_id = _safe_int(row.get("course_id"))
        course_credits_value = course_credits.get(course_id or -1, 0)

        if role == "assistant":
            assistant_assignments += 1
            continue

        # Default unknown/empty role to primary to keep backward compatibility.
        primary_assignments += 1
        total_credit_hours += course_credits_value

    max_credit_hours = _safe_int(faculty_row.get("max_credit_hours")) or 18
    fte_ratio = _safe_float(faculty_row.get("fte_ratio"), 1.0)
    effective_capacity = max(int(round(max_credit_hours * max(fte_ratio, 0.0))), 1)
    utilization = round(total_credit_hours / effective_capacity, 4)

    alerts: list[str] = []
    if total_credit_hours > int(round(max_credit_hours * 1.25)):
        alerts.append("overload_threshold")
    elif total_credit_hours > max_credit_hours:
        alerts.append("max_credit_exceeded")
    elif total_credit_hours < int(round(max_credit_hours * 0.5)):
        alerts.append("underload_alert")

    return {
        "faculty_id": faculty_id,
        "department": str(faculty_row.get("department") or ""),
        "term_id": term_id,
        "total_credit_hours": total_credit_hours,
        "max_credit_hours": max_credit_hours,
        "fte_ratio": fte_ratio,
        "effective_capacity": effective_capacity,
        "utilization": utilization,
        "primary_assignments": primary_assignments,
        "assistant_assignments": assistant_assignments,
        "alerts": alerts,
    }


def get_department_workload_summary(tenant_id: int, department: str, term_id: int) -> list[dict[str, object]]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    department_normalized = department.strip().lower()

    results: list[dict[str, object]] = []
    for row in faculty_rows:
        row_department = str(row.get("department") or "").strip().lower()
        if row_department != department_normalized:
            continue
        faculty_id = str(row.get("faculty_id") or "").strip()
        if not faculty_id:
            continue
        results.append(get_faculty_workload(tenant_id, faculty_id, term_id))

    utilizations = [float(item["utilization"]) for item in results]
    if len(utilizations) > 1 and pstdev(utilizations) > 0.35:
        for item in results:
            alerts = list(item.get("alerts") or [])
            if "fairness_check" not in alerts:
                alerts.append("fairness_check")
            item["alerts"] = alerts

    return results


def list_workload_alerts(tenant_id: int, term_id: int) -> list[dict[str, object]]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    alerts: list[dict[str, object]] = []
    for row in faculty_rows:
        faculty_id = str(row.get("faculty_id") or "").strip()
        if not faculty_id:
            continue
        workload = get_faculty_workload(tenant_id, faculty_id, term_id)
        if workload["alerts"]:
            alerts.append(workload)
    return alerts


def update_faculty_capacity(
    tenant_id: int,
    faculty_id: str,
    max_credit_hours: int,
    fte_ratio: float,
) -> dict[str, object]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    normalized_faculty_id = faculty_id.strip()
    faculty_row = next(
        (
            row
            for row in faculty_rows
            if str(row.get("faculty_id") or "").strip() == normalized_faculty_id
        ),
        None,
    )
    if faculty_row is None:
        raise ValueError("faculty not found")

    row_id = _safe_int(faculty_row.get("id"))
    if row_id is None:
        raise ValueError("faculty not found")

    updated_payload = dict(faculty_row)
    updated_payload["max_credit_hours"] = int(max_credit_hours)
    updated_payload["fte_ratio"] = float(fte_ratio)
    return update_entity_for_tenant("faculty", row_id, updated_payload, tenant_id)
