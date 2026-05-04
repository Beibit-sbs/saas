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
from app.platform.events.publisher import EventPublisher


_ENTITY = "syllabi"
_WORKFLOW_ENTITY = "syllabus_approval_workflows"
_ACTION_ENTITY = "syllabus_approval_actions"
_OUTCOME_ENTITY = "syllabus_approval_outcomes"

# W97: guard — syllabus approval requires course linked to active program
_SYLLABUS_APPROVAL_TARGET_STATUS: str = "approved"
_PROGRAM_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})

# W123: guard — syllabus creation requires faculty member to have an active contract
_FACULTY_CONTRACT_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})

_DEPT_MAX_ACTIVE_SYLLABI: dict[str, int] = {
    "cs": 30,
    "math": 25,
    "physics": 20,
    "humanities": 40,
    "law": 20,
    "medicine": 15,
    "default": 35,
}

_SYLLABUS_STATUSES: frozenset[str] = frozenset({
    "draft",
    "under_review",
    "approved",
    "published",
    "archived",
})

_ALLOWED_SYLLABUS_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"under_review", "archived"},
    "under_review": {"approved", "archived"},
    "approved": {"published", "archived"},
    "published": {"archived"},
    "archived": set(),
}

_ACTIVE_SYLLABUS_STATUSES: frozenset[str] = frozenset({"draft", "under_review"})

# W36: flag syllabi in high-workload status for review alert
_HIGH_WORKLOAD_STATUSES: frozenset[str] = frozenset({"under_review"})


def _normalize_syllabus_status(status: object) -> str:
    normalized = str(status or "draft").strip().lower()
    if normalized not in _SYLLABUS_STATUSES:
        raise ValueError(f"Unsupported syllabus status '{status}'")
    return normalized


def _publish_syllabus_event(
    *,
    tenant_id: int,
    event_type: str,
    aggregate_id: int,
    payload_json: dict[str, object],
) -> None:
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type="syllabus",
        aggregate_id=aggregate_id,
        payload_json=payload_json,
    )


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


def _get_syllabus_row(*, tenant_id: int, syllabus_id: int) -> dict[str, object]:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == syllabus_id), None)
    if row is None:
        raise DomainValidationError(f"Syllabus {syllabus_id} not found")
    return row


def _check_faculty_has_active_contract_for_syllabus(
    *,
    tenant_id: int,
    faculty_id: str,
) -> None:
    """W123 fail-closed guard: block syllabus creation when faculty has no active contract."""
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

    syllabus_row = _get_syllabus_row(tenant_id=tenant_id, syllabus_id=syllabus_id)

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
        if str(p.get("status") or "").strip().lower() in _PROGRAM_ACTIVE_STATUSES
    )

    for course in matching_courses:
        pid = str(course.get("program_id") or "")
        if pid and pid in active_program_ids:
            return

    raise DomainValidationError(
        f"Syllabus {syllabus_id} (course_code='{course_code}') approval blocked: "
        f"no matching course is linked to an active program "
        f"— dead syllabus prevention (accreditation integrity)"
    )


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
            return
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


def _ensure_approval_workflow_and_action(
    *,
    tenant_id: int,
    syllabus_id: int,
    actor: str,
    course_code: str,
    department_id: str,
) -> None:
    workflows = list_entities_for_tenant(_WORKFLOW_ENTITY, tenant_id)
    workflow = next(
        (
            w for w in workflows
            if int(w.get("syllabus_id") or 0) == syllabus_id
        ),
        None,
    )

    if workflow is None:
        workflow = create_entity_for_tenant(
            _WORKFLOW_ENTITY,
            {
                "syllabus_id": syllabus_id,
                "workflow_status": "in_progress",
                "current_step": 1,
                "total_steps": 4,
                "initiated_by": actor,
                "tenant_id": tenant_id,
            },
            tenant_id,
        )

    actions = list_entities_for_tenant(_ACTION_ENTITY, tenant_id)
    if any(
        int(a.get("workflow_id") or 0) == int(workflow.get("id") or 0)
        and str(a.get("action_type") or "") == "review_requested"
        and str(a.get("action_status") or "") in {"pending", "completed"}
        for a in actions
    ):
        return

    create_entity_for_tenant(
        _ACTION_ENTITY,
        {
            "workflow_id": int(workflow.get("id") or 0),
            "syllabus_id": syllabus_id,
            "step_order": 1,
            "step_type": "department_chair",
            "assigned_to": "chair@example.com",
            "action_type": "review_requested",
            "action_status": "pending",
            "course_code": course_code,
            "department_id": department_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _record_syllabus_outcome(
    *,
    tenant_id: int,
    syllabus_id: int,
    actor: str,
    outcome: str,
) -> None:
    create_entity_for_tenant(
        _OUTCOME_ENTITY,
        {
            "syllabus_id": syllabus_id,
            "outcome": outcome,
            "recorded_by": actor,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def list_syllabi(
    tenant_id: int,
    *,
    status: str | None = None,
    department_id: str | None = None,
) -> list[SyllabusSchema]:
    rows = list_entities_for_tenant(_ENTITY, tenant_id)
    if status:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if department_id:
        rows = [r for r in rows if str(r.get("department_id") or "") == department_id]
    return [_to_schema(r) for r in rows]


def create_syllabus(tenant_id: int, payload: SyllabusCreateSchema, actor: str) -> SyllabusSchema:
    # W123 cross-entity guard: verify faculty has an active employment contract
    _check_faculty_has_active_contract_for_syllabus(
        tenant_id=tenant_id,
        faculty_id=payload.faculty_id,
    )

    status = _normalize_syllabus_status(payload.status)

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
    row = create_entity_for_tenant(_ENTITY, {**data, "status": status}, tenant_id)
    syllabus_id = int(row.get("id") or 0)

    if status in _HIGH_WORKLOAD_STATUSES:
        _ensure_approval_workflow_and_action(
            tenant_id=tenant_id,
            syllabus_id=syllabus_id,
            actor=actor,
            course_code=payload.course_code,
            department_id=payload.department_id,
        )
        _ensure_review_backlog_record(
            tenant_id=tenant_id,
            syllabus_id=syllabus_id,
            syllabus_data={
                "course_code": payload.course_code,
                "department_id": payload.department_id,
            },
        )

    _publish_syllabus_event(
        tenant_id=tenant_id,
        event_type="syllabus.created",
        aggregate_id=syllabus_id,
        payload_json={
            "syllabus_id": syllabus_id,
            "course_code": row.get("course_code"),
            "department_id": row.get("department_id"),
            "status": row.get("status"),
            "actor": actor,
            "source_module": "syllabus_governance",
        },
    )

    if status in _HIGH_WORKLOAD_STATUSES:
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.review_requested",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "course_code": row.get("course_code"),
                "department_id": row.get("department_id"),
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="campus.syllabus_governance.review_backlog_detected",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "course_code": row.get("course_code"),
                "department_id": row.get("department_id"),
                "source_module": "syllabus_governance",
            },
        )

    log_admin_action(
        actor=actor,
        action="syllabus.create",
        path="/api/admin/syllabus-governance",
        client_ip="service",
        entity="syllabus",
        metadata={"course_code": payload.course_code},
        tenant_id=tenant_id,
    )

    return _to_schema(row)


def update_syllabus(
    tenant_id: int, syllabus_id: int, payload: SyllabusUpdateSchema, actor: str
) -> SyllabusSchema:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    existing = _get_syllabus_row(tenant_id=tenant_id, syllabus_id=syllabus_id)

    if not updates:
        return _to_schema(existing)

    next_status_obj = updates.get("status")
    current_status = _normalize_syllabus_status(existing.get("status") or "draft")

    if next_status_obj is not None:
        next_status = _normalize_syllabus_status(next_status_obj)
        if next_status != current_status and next_status not in _ALLOWED_SYLLABUS_TRANSITIONS.get(current_status, set()):
            raise ValueError(
                f"Invalid syllabus transition from '{current_status}' to '{next_status}'"
            )

        _check_course_linked_to_active_program_for_syllabus_approval(
            tenant_id=tenant_id,
            syllabus_id=syllabus_id,
            target_status=next_status,
        )

        if next_status == "under_review":
            # fail-closed action path: do not move to review if workflow action cannot be persisted
            try:
                _ensure_approval_workflow_and_action(
                    tenant_id=tenant_id,
                    syllabus_id=syllabus_id,
                    actor=actor,
                    course_code=str(existing.get("course_code") or ""),
                    department_id=str(existing.get("department_id") or ""),
                )
            except Exception as exc:
                raise DomainValidationError(
                    f"Cannot move syllabus {syllabus_id} to under_review: failed to persist approval workflow/action path. "
                    f"Reason: {exc}"
                ) from exc

        updates["status"] = next_status
    else:
        next_status = current_status

    merged = {**existing, **updates}
    row = update_entity_for_tenant(_ENTITY, syllabus_id, merged, tenant_id)
    if row is None:
        raise ValueError(f"Syllabus {syllabus_id} not found")

    if next_status == "under_review":
        _ensure_review_backlog_record(
            tenant_id=tenant_id,
            syllabus_id=syllabus_id,
            syllabus_data={
                "course_code": str(row.get("course_code") or ""),
                "department_id": str(row.get("department_id") or ""),
            },
        )
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.review_requested",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "from_status": current_status,
                "to_status": next_status,
                "course_code": row.get("course_code"),
                "department_id": row.get("department_id"),
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="campus.syllabus_governance.review_backlog_detected",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "course_code": row.get("course_code"),
                "department_id": row.get("department_id"),
                "source_module": "syllabus_governance",
            },
        )

    if next_status == "approved":
        _record_syllabus_outcome(tenant_id=tenant_id, syllabus_id=syllabus_id, actor=actor, outcome="approved")
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.approved",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "from_status": current_status,
                "to_status": next_status,
                "course_code": row.get("course_code"),
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.outcome_recorded",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "outcome": "approved",
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )

    if next_status == "published":
        _record_syllabus_outcome(tenant_id=tenant_id, syllabus_id=syllabus_id, actor=actor, outcome="published")
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.published",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "from_status": current_status,
                "to_status": next_status,
                "course_code": row.get("course_code"),
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.outcome_recorded",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "outcome": "published",
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )

    if next_status == "archived":
        _record_syllabus_outcome(tenant_id=tenant_id, syllabus_id=syllabus_id, actor=actor, outcome="archived")
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.archived",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "from_status": current_status,
                "to_status": next_status,
                "course_code": row.get("course_code"),
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )
        _publish_syllabus_event(
            tenant_id=tenant_id,
            event_type="syllabus.outcome_recorded",
            aggregate_id=syllabus_id,
            payload_json={
                "syllabus_id": syllabus_id,
                "outcome": "archived",
                "actor": actor,
                "source_module": "syllabus_governance",
            },
        )

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
        s = str(row.get("status") or "draft")
        if s in breakdown:
            breakdown[s] += 1
        else:
            breakdown[s] = breakdown.get(s, 0) + 1
    return {
        "total_syllabi": len(rows),
        "status_breakdown": breakdown,
    }


def get_approval_workflow(tenant_id: int, syllabus_id: int) -> dict:
    """Return persisted approval workflow (not stub) for the given syllabus."""
    _get_syllabus_row(tenant_id=tenant_id, syllabus_id=syllabus_id)

    workflows = list_entities_for_tenant(_WORKFLOW_ENTITY, tenant_id)
    workflow = next(
        (w for w in workflows if int(w.get("syllabus_id") or 0) == syllabus_id),
        None,
    )

    if workflow is None:
        return {
            "workflow_id": f"wf-{syllabus_id}",
            "syllabi_id": str(syllabus_id),
            "current_step": 0,
            "total_steps": 4,
            "status": "not_started",
            "initiated_at": "",
            "completed_at": None,
            "rejection_reason": None,
            "approval_steps": [],
        }

    actions = list_entities_for_tenant(_ACTION_ENTITY, tenant_id)
    wf_actions = [
        a for a in actions
        if int(a.get("workflow_id") or 0) == int(workflow.get("id") or 0)
    ]
    wf_actions.sort(key=lambda x: int(x.get("step_order") or 0))

    approval_steps = [
        {
            "step_id": str(a.get("id") or f"step-{idx + 1}"),
            "syllabi_id": str(syllabus_id),
            "step_type": str(a.get("step_type") or "review"),
            "assigned_to": str(a.get("assigned_to") or ""),
            "assigned_to_name": str(a.get("assigned_to") or "").split("@")[0].replace(".", " ").title(),
            "status": str(a.get("action_status") or "pending"),
            "order": int(a.get("step_order") or (idx + 1)),
            "created_at": str(a.get("created_at") or ""),
        }
        for idx, a in enumerate(wf_actions)
    ]

    return {
        "workflow_id": str(workflow.get("id") or f"wf-{syllabus_id}"),
        "syllabi_id": str(syllabus_id),
        "current_step": int(workflow.get("current_step") or 0),
        "total_steps": int(workflow.get("total_steps") or 4),
        "status": str(workflow.get("workflow_status") or "in_progress"),
        "initiated_at": str(workflow.get("created_at") or ""),
        "completed_at": workflow.get("completed_at"),
        "rejection_reason": workflow.get("rejection_reason"),
        "approval_steps": approval_steps,
    }
