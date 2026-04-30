from statistics import pstdev

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_FACULTY_CONTRACT_STATUS_MAX_ACTIVE: dict[str, int] = {
    "active": 500,
    "draft": 200,
    "pending": 150,
    "terminated": 1000,
    "expired": 2000,
}
_ACTIVE_CONTRACT_STATUSES = frozenset({"active", "draft", "pending"})
_CONTRACT_TERMINATION_RISK_STATUSES = frozenset({"terminated"})


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
    contract_status = str(payload.get("status") or "active").strip().lower()
    existing = list_entities_for_tenant("faculty_contracts", tenant_id)
    active_count = sum(
        1 for r in existing
        if str(r.get("status") or "").strip().lower() in _ACTIVE_CONTRACT_STATUSES
    )
    cap = _FACULTY_CONTRACT_STATUS_MAX_ACTIVE.get(contract_status, 200)
    if active_count >= cap:
        raise ValueError("faculty_contract active cap reached")
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
    result = update_entity_for_tenant("faculty_contracts", contract_id, updated_payload, tenant_id)
    if status in _CONTRACT_TERMINATION_RISK_STATUSES:
        _ensure_contract_termination_alert_record(contract_id, tenant_id)
    return result


def _ensure_contract_termination_alert_record(contract_id: int, tenant_id: int) -> None:
    existing = list_entities_for_tenant("faculty_contract_termination_alerts", tenant_id)
    already = any(
        r.get("integration_source") == "faculty_contract_termination_queue"
        and str(r.get("source_entity_id") or "") == str(contract_id)
        for r in existing
    )
    if already:
        return
    alert_payload: dict[str, object] = {
        "contract_id": contract_id,
        "alert_status": "open",
        "integration_source": "faculty_contract_termination_queue",
        "source_entity_id": str(contract_id),
        "tenant_id": tenant_id,
    }
    create_entity_for_tenant("faculty_contract_termination_alerts", alert_payload, tenant_id)
    EventPublisher.publish(
        "campus.faculty.contract_termination_risk_detected",
        {"contract_id": contract_id, "tenant_id": tenant_id},
    )


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
            if "overload_threshold" in workload["alerts"] or "max_credit_exceeded" in workload["alerts"]:
                risk_level = "high" if "overload_threshold" in workload["alerts"] else "medium"
                source_id = f"{faculty_id}:{term_id}"
                EventPublisher().publish_event(
                    tenant_id=tenant_id,
                    event_type="faculty.workload_overload.detected",
                    aggregate_type="faculty_workload",
                    aggregate_id=source_id,
                    payload_json={
                        "faculty_id": faculty_id,
                        "term_id": term_id,
                        "workload_ratio": workload.get("utilization"),
                        "total_credit_hours": workload.get("total_credit_hours"),
                        "max_credit_hours": workload.get("max_credit_hours"),
                        "risk_level": risk_level,
                        "source_entity_type": "faculty_workload",
                        "source_entity_id": source_id,
                    },
                )
    return alerts


def get_faculty_capacity(tenant_id: int, faculty_id: str) -> dict[str, object]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    normalized = faculty_id.strip()
    row = next(
        (r for r in faculty_rows if str(r.get("faculty_id") or "").strip() == normalized),
        None,
    )
    if row is None:
        raise ValueError("faculty not found")
    return {
        "faculty_id": faculty_id,
        "max_credit_hours": int(row.get("max_credit_hours") or 18),
        "fte_ratio": float(row.get("fte_ratio") or 1.0),
    }


def get_workload_metrics(tenant_id: int, term_id: int) -> dict[str, object]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    by_dept: dict[str, list[dict]] = {}
    for row in faculty_rows:
        fid = str(row.get("faculty_id") or "").strip()
        if not fid:
            continue
        try:
            w = get_faculty_workload(tenant_id, fid, term_id)
        except (ValueError, Exception):
            continue
        dept = str(w.get("department") or "unknown")
        by_dept.setdefault(dept, []).append(w)

    all_workloads = [w for ws in by_dept.values() for w in ws]
    utils = [float(w["utilization"]) for w in all_workloads]

    def _avg(vals: list[float]) -> float:
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    def _median(vals: list[float]) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        m = len(s) // 2
        return round(s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2, 4)

    departments = []
    for dept, ws in by_dept.items():
        du = [float(w["utilization"]) for w in ws]
        departments.append({
            "department": dept,
            "term_id": term_id,
            "total_faculty": len(ws),
            "average_utilization_pct": _avg(du),
            "underload_count": sum(1 for w in ws if "underload_alert" in (w.get("alerts") or [])),
            "overload_count": sum(1 for w in ws if "overload_threshold" in (w.get("alerts") or [])),
            "max_credit_exceeded_count": sum(1 for w in ws if "max_credit_exceeded" in (w.get("alerts") or [])),
        })

    return {
        "term_id": term_id,
        "total_faculty": len(all_workloads),
        "average_utilization_pct": _avg(utils),
        "median_utilization_pct": _median(utils),
        "min_utilization_pct": round(min(utils), 4) if utils else 0.0,
        "max_utilization_pct": round(max(utils), 4) if utils else 0.0,
        "utilization_std_dev": round(pstdev(utils), 4) if len(utils) > 1 else 0.0,
        "alert_count_by_type": {
            "underload": sum(1 for w in all_workloads if "underload_alert" in (w.get("alerts") or [])),
            "overload": sum(1 for w in all_workloads if "overload_threshold" in (w.get("alerts") or [])),
            "max_credit_exceeded": sum(1 for w in all_workloads if "max_credit_exceeded" in (w.get("alerts") or [])),
        },
        "departments": departments,
    }


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


# --- Teaching Quality (Phase IV-IV1) ---

_QUALITY_ALERT_THRESHOLD = 60.0


def list_teaching_quality(tenant_id: int, faculty_id: str | None = None) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("teaching_quality_records", tenant_id)
    if faculty_id is not None:
        normalized = faculty_id.strip()
        rows = [r for r in rows if str(r.get("faculty_id") or "").strip() == normalized]
    return rows


def create_teaching_quality_record(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    record = create_entity_for_tenant("teaching_quality_records", payload, tenant_id)
    quality_score = float(record.get("quality_score") or 100.0)
    kpi_score = float(record.get("kpi_score") or 100.0)
    if quality_score < _QUALITY_ALERT_THRESHOLD or kpi_score < _QUALITY_ALERT_THRESHOLD:
        record_id = str(record.get("id") or "unknown")
        faculty_id_val = str(record.get("faculty_id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="faculty.quality_drop.detected",
            aggregate_type="teaching_quality_record",
            aggregate_id=record_id,
            payload_json={
                "faculty_id": faculty_id_val,
                "course_id": record.get("course_id"),
                "term_id": record.get("term_id"),
                "quality_score": quality_score,
                "kpi_score": kpi_score,
                "risk_level": "high" if min(quality_score, kpi_score) < 40.0 else "medium",
                "source_entity_type": "teaching_quality_record",
                "source_entity_id": record_id,
            },
        )
    return record


def get_faculty_brain_context(tenant_id: int) -> dict:
    """Return aggregated faculty context snapshot for Brain Core."""
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    quality_rows = list_entities_for_tenant("teaching_quality_records", tenant_id)

    total_faculty = len(faculty_rows)
    by_status: dict[str, int] = {}
    by_department: dict[str, int] = {}
    for r in faculty_rows:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        dep = str(r.get("department") or "unknown")
        by_department[dep] = by_department.get(dep, 0) + 1

    quality_alert_count = sum(
        1
        for r in quality_rows
        if float(r.get("quality_score") or 100.0) < _QUALITY_ALERT_THRESHOLD
        or float(r.get("kpi_score") or 100.0) < _QUALITY_ALERT_THRESHOLD
    )
    avg_quality = (
        sum(float(r.get("quality_score") or 0.0) for r in quality_rows) / len(quality_rows)
        if quality_rows
        else None
    )

    risk_level = (
        "high"
        if total_faculty > 0 and quality_alert_count / max(total_faculty, 1) > 0.3
        else ("medium" if quality_alert_count > 0 else "low")
    )

    return {
        "module": "faculty",
        "tenant_id": tenant_id,
        "total_faculty": total_faculty,
        "by_status": by_status,
        "by_department": by_department,
        "total_quality_records": len(quality_rows),
        "quality_alert_count": quality_alert_count,
        "avg_quality_score": avg_quality,
        "risk_level": risk_level,
    }


# ---------------------------------------------------------------------------
# Phase IV-IV2: Proctoring / exam supervision
# ---------------------------------------------------------------------------

_PROCTORING_HIGH_SEVERITY = "high"


def list_proctoring_records(
    tenant_id: int,
    faculty_id: str | None = None,
    exam_id: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("proctoring_records", tenant_id)
    faculty_filter = str(faculty_id or "").strip()
    exam_filter = str(exam_id or "").strip()
    result: list[dict[str, object]] = []
    for row in rows:
        if faculty_filter and str(row.get("faculty_id") or "").strip() != faculty_filter:
            continue
        if exam_filter and str(row.get("exam_id") or "").strip() != exam_filter:
            continue
        result.append(row)
    return result


def create_proctoring_record(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    record = create_entity_for_tenant("proctoring_records", payload, tenant_id)
    severity = str(record.get("severity") or "").strip().lower()
    if severity == _PROCTORING_HIGH_SEVERITY:
        record_id = str(record.get("id") or "unknown")
        faculty_id_val = str(record.get("faculty_id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="faculty.proctoring.violation_detected",
            aggregate_type="proctoring_record",
            aggregate_id=record_id,
            payload_json={
                "faculty_id": faculty_id_val,
                "exam_id": record.get("exam_id"),
                "room_id": record.get("room_id"),
                "violation_type": record.get("violation_type"),
                "severity": severity,
                "student_id": record.get("student_id"),
                "status": record.get("status"),
                "source_entity_type": "proctoring_record",
                "source_entity_id": record_id,
            },
        )
    return record


def get_proctoring_brain_context(tenant_id: int) -> dict:
    """Return aggregated proctoring context snapshot for Brain Core."""
    rows = list_entities_for_tenant("proctoring_records", tenant_id)

    total = len(rows)
    by_severity: dict[str, int] = {}
    by_violation_type: dict[str, int] = {}
    open_count = 0
    for r in rows:
        sev = str(r.get("severity") or "unknown").lower()
        by_severity[sev] = by_severity.get(sev, 0) + 1
        vtype = str(r.get("violation_type") or "unknown")
        by_violation_type[vtype] = by_violation_type.get(vtype, 0) + 1
        if str(r.get("status") or "").lower() == "open":
            open_count += 1

    high_count = by_severity.get("high", 0)
    risk_level = (
        "high"
        if high_count > 0 and high_count / max(total, 1) > 0.2
        else ("medium" if high_count > 0 else "low")
    )

    return {
        "module": "proctoring",
        "tenant_id": tenant_id,
        "total_records": total,
        "open_violations": open_count,
        "by_severity": by_severity,
        "by_violation_type": by_violation_type,
        "high_severity_count": high_count,
        "risk_level": risk_level,
    }


# ---------------------------------------------------------------------------
# Phase IV-IV3: Office hours scheduling & availability management
# ---------------------------------------------------------------------------


def list_office_hours(
    tenant_id: int,
    faculty_id: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("office_hours_records", tenant_id)
    faculty_filter = str(faculty_id or "").strip()
    result: list[dict[str, object]] = []
    for row in rows:
        if faculty_filter and str(row.get("faculty_id") or "").strip() != faculty_filter:
            continue
        result.append(row)
    return result


def create_office_hours_record(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    record = create_entity_for_tenant("office_hours_records", payload, tenant_id)
    no_show = record.get("no_show")
    if no_show is True or no_show == "true" or no_show == 1:
        record_id = str(record.get("id") or "unknown")
        faculty_id_val = str(record.get("faculty_id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="faculty.office_hours.no_show_detected",
            aggregate_type="office_hours_record",
            aggregate_id=record_id,
            payload_json={
                "faculty_id": faculty_id_val,
                "scheduled_at": record.get("scheduled_at"),
                "student_id": record.get("student_id"),
                "location": record.get("location"),
                "no_show": True,
                "source_entity_type": "office_hours_record",
                "source_entity_id": record_id,
            },
        )
    return record


def get_office_hours_brain_context(tenant_id: int) -> dict:
    """Return aggregated office hours context snapshot for Brain Core."""
    rows = list_entities_for_tenant("office_hours_records", tenant_id)

    total = len(rows)
    no_show_count = 0
    by_status: dict[str, int] = {}
    for r in rows:
        status = str(r.get("status") or "unknown").lower()
        by_status[status] = by_status.get(status, 0) + 1
        if r.get("no_show") is True or r.get("no_show") == "true" or r.get("no_show") == 1:
            no_show_count += 1

    no_show_rate = round(no_show_count / max(total, 1), 2)
    risk_level = (
        "high" if no_show_rate > 0.3
        else ("medium" if no_show_rate > 0.1 else "low")
    )

    return {
        "module": "office_hours",
        "tenant_id": tenant_id,
        "total_records": total,
        "no_show_count": no_show_count,
        "no_show_rate": no_show_rate,
        "by_status": by_status,
        "risk_level": risk_level,
    }
