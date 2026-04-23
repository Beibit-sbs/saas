"""Phase X-X2: HR/Payroll service."""
from __future__ import annotations

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
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher


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
    created = create_entity_for_tenant(
        "hr_employees",
        {
            "employee_code": request.employee_code.strip(),
            "full_name": request.full_name.strip(),
            "department_id": request.department_id.strip(),
            "role_title": request.role_title.strip(),
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
    return HrEmployeeSchema.model_validate(created)


def update_hr_employee_status(
    tenant_id: int,
    employee_id: int,
    request: HrEmployeeStatusUpdateSchema,
    actor: str,
) -> HrEmployeeSchema | None:
    rows = list_entities_for_tenant("hr_employees", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == employee_id), None)
    if existing is None:
        return None
    updated = update_entity_for_tenant(
        "hr_employees", employee_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("hr_payroll", "employee", "status_update"),
        path=f"/internal/hr-payroll/employees/{employee_id}/status",
        metadata={"resource_id": str(employee_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return HrEmployeeSchema.model_validate(updated)


# --- Payroll Cycles ---

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
    return PayrollCycleSchema.model_validate(created)


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
    updated = update_entity_for_tenant(
        "hr_payroll_cycles", cycle_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("hr_payroll", "payroll_cycle", "status_update"),
        path=f"/internal/hr-payroll/cycles/{cycle_id}/status",
        metadata={"resource_id": str(cycle_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return PayrollCycleSchema.model_validate(updated)
