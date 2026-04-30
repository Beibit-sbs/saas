"""Phase X-X2: HR/Payroll service."""
from __future__ import annotations

from typing import cast

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.hr_payroll.schemas import (
    HrEmployeeCreateSchema,
    HrEmployeeSchema,
    HrEmployeeStatus,
    HrEmployeeStatusUpdateSchema,
    PayrollCycleCreateSchema,
    PayrollCycleSchema,
    PayrollCycleStatus,
    PayrollCycleStatusUpdateSchema,
)
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher


_ALLOWED_PAYROLL_CYCLE_TRANSITIONS: dict[PayrollCycleStatus, set[PayrollCycleStatus]] = {
    "DRAFT": {"CALCULATING"},
    "CALCULATING": {"APPROVED"},
    "APPROVED": {"PAID"},
    "PAID": set(),
}

# W43: cap on active employees per status per tenant
_EMPLOYEE_STATUS_MAX_ACTIVE: dict[str, int] = {
    "active": 1000,
    "on_leave": 200,
    "onboarding": 150,
    "offboarding": 100,
    "terminated": 500,
}

_ACTIVE_EMPLOYEE_STATUSES: frozenset[str] = frozenset({
    "active", "on_leave", "onboarding", "offboarding",
})

# W43: statuses that trigger an offboarding risk alert
_OFFBOARDING_RISK_STATUSES: frozenset[str] = frozenset({"offboarding", "terminated"})

# W66: payroll cycle statuses indicating processing risk
_PAYROLL_CYCLE_RISK_STATUSES: frozenset[str] = frozenset({"DRAFT", "CALCULATING"})

# W94: payroll cycle approval requires active employees
_PAYROLL_APPROVAL_GATE_STATUSES: frozenset[str] = frozenset({"APPROVED"})

# W94: employee statuses that qualify as actively payable
_PAYABLE_EMPLOYEE_STATUSES: frozenset[str] = frozenset({"active", "on_leave"})

# W125: payroll cycle creation requires at least one payable employee
_PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES: frozenset[str] = frozenset({"active", "on_leave"})

# W73: enforce employee lifecycle transitions
_ALLOWED_EMPLOYEE_STATUS_TRANSITIONS: dict[HrEmployeeStatus, frozenset[HrEmployeeStatus]] = {
    "onboarding": frozenset({"active", "terminated"}),
    "active": frozenset({"on_leave", "offboarding", "terminated"}),
    "on_leave": frozenset({"active", "offboarding", "terminated"}),
    "offboarding": frozenset({"on_leave", "terminated"}),
    "terminated": frozenset(),
}


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="hr_payroll",
        metadata=metadata,
        tenant_id=tenant_id,
    )


# --- Employees ---

def list_hr_employees(
    tenant_id: int,
    department_id: str | None = None,
    status: HrEmployeeStatus | None = None,
) -> list[HrEmployeeSchema]:
    rows = list_entities_for_tenant("hr_employees", tenant_id)
    if department_id:
        dept = department_id.strip()
        rows = [r for r in rows if str(r.get("department_id") or "").strip() == dept]
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [HrEmployeeSchema.model_validate(r) for r in rows]


def get_hr_employee(tenant_id: int, employee_id: int) -> HrEmployeeSchema | None:
    rows = list_entities_for_tenant("hr_employees", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == employee_id), None)
    if row is None:
        return None
    return HrEmployeeSchema.model_validate(row)


def create_hr_employee(
    tenant_id: int,
    request: HrEmployeeCreateSchema,
    actor: str,
) -> HrEmployeeSchema:
    existing = list_entities_for_tenant("hr_employees", tenant_id)

    # W43: count-cap guard on active employees by status
    emp_status = str(request.status)
    cap = _EMPLOYEE_STATUS_MAX_ACTIVE.get(emp_status, 1000)
    active_count = sum(
        1 for r in existing
        if str(r.get("status") or "") in _ACTIVE_EMPLOYEE_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active employee cap ({cap}) reached; cannot create new employee with status '{emp_status}'"
        )

    created = create_entity_for_tenant(
        "hr_employees",
        {
            "employee_code": request.employee_code.strip(),
            "full_name": request.full_name.strip(),
            "department_id": request.department_id.strip(),
            "role_title": request.role_title.strip(),
            "contract_type": str(request.contract_type).strip() if request.contract_type else None,
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("hr_payroll", "employee", "create"),
        path="/internal/hr-payroll/employees",
        metadata={"resource_id": str(created.get("id")), "employee_code": request.employee_code},
        tenant_id=tenant_id,
    )
    # Brain signal on offboarding
    if request.status in ("offboarding", "terminated"):
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="hr.employee.offboarding_initiated",
            aggregate_type="hr_employees",
            aggregate_id=str(created.get("id") or "unknown"),
            payload_json={"employee_code": request.employee_code, "status": request.status},
        )
    # W43: side-effect offboarding alert for risk statuses
    if emp_status in _OFFBOARDING_RISK_STATUSES:
        _ensure_offboarding_alert_record(
            tenant_id=tenant_id,
            employee_id=int(created.get("id") or 0),
            employee_data={
                "employee_code": request.employee_code.strip(),
                "department_id": request.department_id.strip(),
                "status": emp_status,
            },
        )
    return HrEmployeeSchema.model_validate(created)


def _ensure_offboarding_alert_record(
    tenant_id: int,
    employee_id: int,
    employee_data: dict,
) -> None:
    """Idempotent: create an hr_offboarding_alerts entry for offboarding/terminated employees."""
    existing = list_entities_for_tenant("hr_offboarding_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "hr_offboarding_queue"
            and str(rec.get("source_entity_id")) == str(employee_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "hr_offboarding_alerts",
        {
            "employee_id": employee_id,
            "employee_code": str(employee_data.get("employee_code") or ""),
            "department_id": str(employee_data.get("department_id") or ""),
            "offboarding_status": str(employee_data.get("status") or ""),
            "alert_status": "open",
            "integration_source": "hr_offboarding_queue",
            "source_entity_id": str(employee_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def update_hr_employee_status(
    tenant_id: int,
    employee_id: int,
    request: HrEmployeeStatusUpdateSchema,
    actor: str,
) -> HrEmployeeSchema:
    rows = list_entities_for_tenant("hr_employees", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == employee_id), None)
    if existing is None:
        raise LookupError("Employee not found")

    current_status = cast(HrEmployeeStatus, str(existing.get("status") or "").strip())
    if current_status not in _ALLOWED_EMPLOYEE_STATUS_TRANSITIONS:
        raise ValueError(f"Unsupported current employee status '{current_status}'")

    next_status = request.status
    allowed_next = _ALLOWED_EMPLOYEE_STATUS_TRANSITIONS[current_status]
    if next_status != current_status and next_status not in allowed_next:
        raise ValueError(
            f"Invalid employee status transition '{current_status}' -> '{next_status}'"
        )

    updated = update_entity_for_tenant(
        "hr_employees", employee_id, {**existing, "status": next_status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("hr_payroll", "employee", "status_update"),
        path=f"/internal/hr-payroll/employees/{employee_id}/status",
        metadata={"resource_id": str(employee_id), "new_status": next_status},
        tenant_id=tenant_id,
    )
    return HrEmployeeSchema.model_validate(updated)


# --- Payroll Cycles ---

def _validate_payroll_cycle_transition(
    current_status: PayrollCycleStatus,
    target_status: PayrollCycleStatus,
) -> None:
    if current_status == target_status:
        return
    allowed_targets = _ALLOWED_PAYROLL_CYCLE_TRANSITIONS[current_status]
    if target_status not in allowed_targets:
        allowed_repr = ", ".join(sorted(allowed_targets)) or "<terminal>"
        raise ValueError(
            "Invalid payroll cycle transition "
            f"{current_status} -> {target_status}. "
            f"Allowed next statuses: {allowed_repr}."
        )


def _check_active_employees_exist_for_payroll_approval(
    *,
    tenant_id: int,
    cycle_id: int,
    target_status: str,
) -> None:
    """W94: Cross-entity guard — hr_payroll_cycles × hr_employees.

    A payroll cycle cannot be APPROVED if the tenant has no employees in a payable
    status (active or on_leave).  Approving an empty payroll cycle creates a ghost
    payroll scenario: financial records are committed with no actual recipients,
    bypassing payroll audit controls and exposing the institution to fraud risk.

    HARDENING RULES:
    - Guard is surgical: only fires when target_status is in _PAYROLL_APPROVAL_GATE_STATUSES.
    - hr_employees query failure → DomainValidationError (fail-closed; cannot verify payroll legitimacy).
    - Zero payable employees → DomainValidationError with ghost payroll rationale.
    """
    if target_status not in _PAYROLL_APPROVAL_GATE_STATUSES:
        return  # surgical: only enforced on APPROVED transition

    try:
        all_employees = list_entities_for_tenant("hr_employees", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot approve payroll cycle_id={cycle_id}: hr_employees lookup failed. "
            "Cannot verify at least one active employee exists for this payroll cycle. "
            f"Reason: {exc}"
        ) from exc

    payable = [
        e for e in all_employees
        if str(e.get("status") or "") in _PAYABLE_EMPLOYEE_STATUSES
    ]

    if not payable:
        raise DomainValidationError(
            f"Cannot approve payroll cycle_id={cycle_id}: no employees with payable status "
            f"(checked: {sorted(_PAYABLE_EMPLOYEE_STATUSES)}) found for this tenant. "
            "Approving an empty payroll cycle constitutes a ghost payroll scenario and is "
            "blocked to prevent fraudulent financial commitments. "
            "Ensure at least one active or on_leave employee exists before approving."
        )


def _check_payable_employees_exist_for_payroll_cycle_create(
    *,
    tenant_id: int,
    cycle_code: str,
) -> None:
    """W125: Cross-entity guard — hr_payroll_cycles × hr_employees.

    A payroll cycle cannot be created when there are no employees in a payable
    status (active or on_leave).  Creating a payroll cycle with zero payable
    employees generates a ghost cycle: financial records committed for no real
    recipients, bypassing payroll audit controls and opening fraud risk.

    HARDENING RULES:
    - hr_employees lookup failure → DomainValidationError (fail-closed).
    - Zero payable employees → DomainValidationError with ghost payroll rationale.
    """
    try:
        all_employees = list_entities_for_tenant("hr_employees", tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise DomainValidationError(
            f"Cannot create payroll cycle '{cycle_code}': hr_employees lookup failed. "
            "Cannot verify payable employees exist for this tenant. "
            f"Reason: {exc}"
        ) from exc

    payable = [
        e for e in all_employees
        if str(e.get("status") or "") in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES
    ]

    if not payable:
        raise DomainValidationError(
            f"Cannot create payroll cycle '{cycle_code}': no employees with payable status "
            f"(checked: {sorted(_PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES)}) found for this tenant. "
            "Creating a payroll cycle with zero active employees constitutes a ghost payroll "
            "scenario and is blocked to prevent fraudulent financial commitments."
        )


def list_payroll_cycles(
    tenant_id: int,
    status: PayrollCycleStatus | None = None,
) -> list[PayrollCycleSchema]:
    rows = list_entities_for_tenant("hr_payroll_cycles", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [PayrollCycleSchema.model_validate(r) for r in rows]


def get_payroll_cycle(tenant_id: int, cycle_id: int) -> PayrollCycleSchema | None:
    rows = list_entities_for_tenant("hr_payroll_cycles", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == cycle_id), None)
    if row is None:
        return None
    return PayrollCycleSchema.model_validate(row)


def create_payroll_cycle(
    tenant_id: int,
    request: PayrollCycleCreateSchema,
    actor: str,
) -> PayrollCycleSchema:
    # W125: cross-entity guard — must have payable employees before creating a cycle
    _check_payable_employees_exist_for_payroll_cycle_create(
        tenant_id=tenant_id,
        cycle_code=request.cycle_code.strip(),
    )

    created = create_entity_for_tenant(
        "hr_payroll_cycles",
        {
            "cycle_code": request.cycle_code.strip(),
            "period_label": request.period_label.strip(),
            "total_gross": float(request.total_gross),
            "total_net": float(request.total_net),
            "employee_count": int(request.employee_count),
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("hr_payroll", "payroll_cycle", "create"),
        path="/internal/hr-payroll/cycles",
        metadata={"resource_id": str(created.get("id")), "cycle_code": request.cycle_code},
        tenant_id=tenant_id,
    )

    # W66: payroll processing risk alert
    if str(created.get("status") or "DRAFT") in _PAYROLL_CYCLE_RISK_STATUSES:
        _ensure_payroll_cycle_risk_alert_record(
            tenant_id=tenant_id,
            cycle_id=int(created.get("id") or 0),
            cycle_data={
                "cycle_code": request.cycle_code,
                "period_label": request.period_label,
                "employee_count": request.employee_count,
            },
        )

    return PayrollCycleSchema.model_validate(created)


def _ensure_payroll_cycle_risk_alert_record(
    tenant_id: int,
    cycle_id: int,
    cycle_data: dict,
) -> None:
    """Idempotent: create hr_payroll_cycle_risk_alerts when payroll cycle risk detected."""
    existing = list_entities_for_tenant("hr_payroll_cycle_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "payroll_cycle_risk"
            and str(rec.get("source_entity_id")) == str(cycle_id)
        ):
            return
    create_entity_for_tenant(
        "hr_payroll_cycle_risk_alerts",
        {
            "cycle_id": cycle_id,
            "cycle_code": str(cycle_data.get("cycle_code") or ""),
            "period_label": str(cycle_data.get("period_label") or ""),
            "employee_count": int(cycle_data.get("employee_count") or 0),
            "alert_status": "open",
            "integration_source": "payroll_cycle_risk",
            "source_entity_id": str(cycle_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.hr.payroll_cycle_risk_detected",
        aggregate_type="hr_payroll_cycles",
        aggregate_id=str(cycle_id),
        payload_json={
            "cycle_id": cycle_id,
            "cycle_code": str(cycle_data.get("cycle_code") or ""),
            "period_label": str(cycle_data.get("period_label") or ""),
            "employee_count": int(cycle_data.get("employee_count") or 0),
            "source_module": "hr_payroll",
            "source_entity_type": "hr_payroll_cycles",
            "source_entity_id": str(cycle_id),
        },
    )


def update_payroll_cycle_status(
    tenant_id: int,
    cycle_id: int,
    request: PayrollCycleStatusUpdateSchema,
    actor: str,
) -> PayrollCycleSchema | None:
    rows = list_entities_for_tenant("hr_payroll_cycles", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == cycle_id), None)
    if existing is None:
        return None

    current_status = str(existing.get("status") or "DRAFT")
    if current_status not in _ALLOWED_PAYROLL_CYCLE_TRANSITIONS:
        raise ValueError(f"Unknown payroll cycle status in storage: {current_status}")
    typed_current_status = cast(PayrollCycleStatus, current_status)

    _validate_payroll_cycle_transition(typed_current_status, request.status)

    # W94: cross-entity guard — must have active employees before APPROVED
    _check_active_employees_exist_for_payroll_approval(
        tenant_id=tenant_id,
        cycle_id=cycle_id,
        target_status=request.status,
    )

    updated = update_entity_for_tenant(
        "hr_payroll_cycles", cycle_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("hr_payroll", "payroll_cycle", "status_update"),
        path=f"/internal/hr-payroll/cycles/{cycle_id}/status",
        metadata={
            "resource_id": str(cycle_id),
            "from_status": typed_current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )
    return PayrollCycleSchema.model_validate(updated)
