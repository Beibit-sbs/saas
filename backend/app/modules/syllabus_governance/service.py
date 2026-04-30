from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.syllabus_governance.schemas import (
    SyllabusCreateSchema,
    SyllabusSchema,
    SyllabusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ENTITY = "syllabi"

# W97: guard — syllabus approval requires course linked to active program
_SYLLABUS_APPROVAL_TARGET_STATUS: str = "approved"
_PROGRAM_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})

# W123: guard — syllabus creation requires faculty member to have an active contract
_FACULTY_CONTRACT_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})


def _check_faculty_has_active_contract_for_syllabus(
    *,
    tenant_id: int,
    faculty_id: str,
) -> None:
    """W123 fail-closed guard: block syllabus creation when faculty has no active contract.

    5 hardening questions:
    1. Dangerous action      : create_syllabus assigns faculty to a course for the term
    2. Real-world constraint : only faculty with active employment contracts can be assigned
    3. External entity       : faculty_contracts
    4. Validate BEFORE       : create_entity_for_tenant("syllabi", ...)
    5. Bad outcome prevented : syllabus assigned to terminated/resigned faculty — ghost syllabus,
                               accreditation compliance violation
    """
    normalized = str(faculty_id or "").strip()
    if not normalized:
        raise DomainValidationError(
            "Cannot create syllabus: faculty_id is missing or empty — "
            "faculty contract validation cannot be enforced"
        )

    try:
        contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot create syllabus for faculty_id='{normalized}': "
            f"faculty_contracts lookup failed — faculty employment cannot be verified (fail-closed)"
        ) from exc

    faculty_contracts = [
        c for c in contracts
        if str(c.get("faculty_id") or "").strip() == normalized
    ]

    if not faculty_contracts:
        raise DomainValidationError(
            f"Cannot create syllabus for faculty_id='{normalized}': "
            f"no faculty contract records found — faculty employment cannot be confirmed"
        )

    has_active = any(
        str(c.get("status") or "").strip().lower() in _FACULTY_CONTRACT_ACTIVE_STATUSES
        for c in faculty_contracts
    )
    if not has_active:
        raise DomainValidationError(
            f"Cannot create syllabus for faculty_id='{normalized}': "
            f"faculty has no active contract — terminated or resigned faculty cannot be assigned"
        )


def _check_course_linked_to_active_program_for_syllabus_approval(
    *,
    tenant_id: int,
    syllabus_id: int,
    target_status: str,
) -> None:
    """Guard: approving a syllabus requires its course_code to be tied to an active program."""
    if target_status != _SYLLABUS_APPROVAL_TARGET_STATUS:
        return

    syllabi = list_entities_for_tenant(_ENTITY, tenant_id)
    syllabus_row = next((r for r in syllabi if r.get("id") == syllabus_id), None)
    if syllabus_row is None:
        raise DomainValidationError(
            f"Syllabus {syllabus_id} not found — cannot validate program linkage for approval"
        )

    course_code = str(syllabus_row.get("course_code") or "").strip()
    if not course_code:
        raise DomainValidationError(
            f"Syllabus {syllabus_id} approval blocked: syllabus has no course_code "
            f"— cannot approve without course linkage to an active program"
        )

    try:
        courses = list_entities_for_tenant("courses", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Syllabus {syllabus_id} (course_code='{course_code}') approval blocked: "
            f"course lookup failed — {exc}"
        ) from exc

    matching_courses = [
        c for c in courses
        if str(c.get("course_code") or "").strip() == course_code
    ]
    if not matching_courses:
        raise DomainValidationError(
            f"Syllabus {syllabus_id} (course_code='{course_code}') approval blocked: "
            f"no course record found for course_code '{course_code}' — dead syllabus prevention"
        )

    try:
        programs = list_entities_for_tenant("programs", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Syllabus {syllabus_id} (course_code='{course_code}') approval blocked: "
            f"program lookup failed — {exc}"
        ) from exc

    active_program_ids = frozenset(
        str(p.get("id"))
        for p in programs
        if str(p.get("status") or "") in _PROGRAM_ACTIVE_STATUSES
    )

    for course in matching_courses:
        pid = str(course.get("program_id") or "")
        if pid and pid in active_program_ids:
            return  # at least one course is tied to an active program

    raise DomainValidationError(
        f"Syllabus {syllabus_id} (course_code='{course_code}') approval blocked: "
        f"no matching course is linked to an active program "
        f"— dead syllabus prevention (accreditation integrity)"
    )

_DEPT_MAX_ACTIVE_SYLLABI: dict[str, int] = {
    "cs": 30,
    "math": 25,
    "physics": 20,
    "humanities": 40,
    "law": 20,
    "medicine": 15,
    "default": 35,
}

_ACTIVE_SYLLABUS_STATUSES: frozenset[str] = frozenset({"draft", "under_review"})

# W36: flag syllabi in high-workload status for review alert
_HIGH_WORKLOAD_STATUSES: frozenset[str] = frozenset({"under_review"})


def _to_schema(row: dict) -> SyllabusSchema:
    return SyllabusSchema(
        id=row["id"],
        tenant_id=str(row.get("tenant_id", "")),
        course_code=row.get("course_code", ""),
        course_title=row.get("course_title", ""),
        department_id=row.get("department_id", ""),
        faculty_id=row.get("faculty_id", ""),
        term_id=row.get("term_id", ""),
        status=row.get("status", "draft"),
    )


def list_syllabi(
    tenant_id: int,
    *,
    status: str | None = None,
    department_id: str | None = None,
) -> list[SyllabusSchema]:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if department_id:
        rows = [r for r in rows if r.get("department_id") == department_id]
    return [_to_schema(r) for r in rows]


def _ensure_review_backlog_record(
    tenant_id: int,
    syllabus_id: int,
    syllabus_data: dict,
) -> None:
    """Idempotent: create a syllabus_review_backlogs entry when syllabus is under_review."""
    existing = list_entities_for_tenant("syllabus_review_backlogs", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "syllabus_review_queue"
            and str(rec.get("source_entity_id")) == str(syllabus_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "syllabus_review_backlogs",
        {
            "syllabus_id": syllabus_id,
            "course_code": str(syllabus_data.get("course_code") or ""),
            "department_id": str(syllabus_data.get("department_id") or ""),
            "backlog_status": "pending",
            "integration_source": "syllabus_review_queue",
            "source_entity_id": str(syllabus_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def create_syllabus(tenant_id: int, payload: SyllabusCreateSchema, actor: str) -> SyllabusSchema:
    # W123 cross-entity guard: verify faculty has an active employment contract
    _check_faculty_has_active_contract_for_syllabus(
        tenant_id=tenant_id,
        faculty_id=payload.faculty_id,
    )

    dept_key = payload.department_id.strip().lower()
    cap = _DEPT_MAX_ACTIVE_SYLLABI.get(dept_key, _DEPT_MAX_ACTIVE_SYLLABI["default"])
    existing = list_entities_for_tenant(_ENTITY, tenant_id)
    active_count = sum(
        1
        for s in existing
        if str(s.get("department_id") or "").strip().lower() == dept_key
        and str(s.get("status") or "") in _ACTIVE_SYLLABUS_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active syllabus cap ({cap}) reached for department '{dept_key}'"
        )

    data = payload.model_dump()
    row = create_entity_for_tenant(_ENTITY, data, tenant_id)
    log_admin_action(
        actor=actor,
        action="syllabus.create",
        path="/api/admin/syllabus-governance",
        client_ip="service",
        entity="syllabus",
        metadata={"course_code": payload.course_code},
        tenant_id=tenant_id,
    )

    if payload.status in _HIGH_WORKLOAD_STATUSES:
        _ensure_review_backlog_record(
            tenant_id=tenant_id,
            syllabus_id=int(row.get("id") or 0),
            syllabus_data={
                "course_code": payload.course_code,
                "department_id": payload.department_id,
            },
        )

    return _to_schema(row)


def update_syllabus(
    tenant_id: int, syllabus_id: int, payload: SyllabusUpdateSchema, actor: str
) -> SyllabusSchema:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        rows = list_entities_for_tenant(_ENTITY, tenant_id)
        row = next((r for r in rows if r["id"] == syllabus_id), None)
        if row is None:
            raise ValueError(f"Syllabus {syllabus_id} not found")
        return _to_schema(row)
    # W97 guard: approving a syllabus requires course linked to active program
    _check_course_linked_to_active_program_for_syllabus_approval(
        tenant_id=tenant_id,
        syllabus_id=syllabus_id,
        target_status=str(updates.get("status") or ""),
    )
    row = update_entity_for_tenant(_ENTITY, syllabus_id, updates, tenant_id)
    if row is None:
        raise ValueError(f"Syllabus {syllabus_id} not found")
    log_admin_action(
        actor=actor,
        action="syllabus.update",
        path=f"/api/admin/syllabus-governance/{syllabus_id}",
        client_ip="service",
        entity="syllabus",
        metadata={"syllabus_id": syllabus_id, "updates": list(updates.keys())},
        tenant_id=tenant_id,
    )
    return _to_schema(row)


def get_syllabus_dashboard_summary(tenant_id: int) -> dict:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    breakdown: dict[str, int] = {
        "draft": 0,
        "under_review": 0,
        "approved": 0,
        "published": 0,
        "archived": 0,
    }
    for row in rows:
        s = row.get("status", "draft")
        if s in breakdown:
            breakdown[s] += 1
        else:
            breakdown[s] = breakdown.get(s, 0) + 1
    return {
        "total_syllabi": len(rows),
        "status_breakdown": breakdown,
    }


def get_approval_workflow(tenant_id: int, syllabus_id: int) -> dict:
    """Return a stub approval workflow for the given syllabus."""
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    row = next((r for r in rows if r["id"] == syllabus_id), None)
    if row is None:
        raise ValueError(f"Syllabus {syllabus_id} not found")
    status = row.get("status", "draft")
    wf_status = "completed" if status in ("approved", "published") else "in_progress"
    current_step = 1
    if status == "under_review":
        current_step = 2
    elif status in ("approved", "published"):
        current_step = 4
    return {
        "workflow_id": f"wf-{syllabus_id}",
        "syllabi_id": str(syllabus_id),
        "current_step": current_step,
        "total_steps": 4,
        "status": wf_status,
        "initiated_at": row.get("created_at", ""),
        "completed_at": None,
        "rejection_reason": None,
        "approval_steps": [
            {"step_id": "s1", "syllabi_id": str(syllabus_id), "step_type": "department_chair",
             "assigned_to": "chair@example.com", "assigned_to_name": "Department Chair",
             "status": "approved" if current_step > 1 else "pending",
             "order": 1, "created_at": ""},
            {"step_id": "s2", "syllabi_id": str(syllabus_id), "step_type": "academic_dean",
             "assigned_to": "dean@example.com", "assigned_to_name": "Academic Dean",
             "status": "approved" if current_step > 2 else "pending",
             "order": 2, "created_at": ""},
            {"step_id": "s3", "syllabi_id": str(syllabus_id), "step_type": "compliance_review",
             "assigned_to": "compliance@example.com", "assigned_to_name": "Compliance Officer",
             "status": "approved" if current_step > 3 else "pending",
             "order": 3, "created_at": ""},
            {"step_id": "s4", "syllabi_id": str(syllabus_id), "step_type": "final_approval",
             "assigned_to": "provost@example.com", "assigned_to_name": "Provost",
             "status": "approved" if current_step >= 4 else "pending",
             "order": 4, "created_at": ""},
        ],
    }
