"""Phase V-V1: Budget planning service — budget plans, allocations, drift tracking."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_budget_plans(
    tenant_id: int,
    department_id: str | None = None,
    fiscal_year: int | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("budget_plans", tenant_id)
    dept_filter = str(department_id or "").strip()
    result: list[dict[str, object]] = []
    for row in rows:
        if dept_filter and str(row.get("department_id") or "").strip() != dept_filter:
            continue
        if fiscal_year is not None and row.get("fiscal_year") != fiscal_year:
            continue
        result.append(row)
    return result


def create_budget_plan(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    return create_entity_for_tenant("budget_plans", payload, tenant_id)


def list_budget_allocations(
    tenant_id: int,
    plan_id: int | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("budget_allocations", tenant_id)
    result: list[dict[str, object]] = []
    for row in rows:
        if plan_id is not None:
            try:
                row_plan_id = int(row.get("plan_id") or 0)
            except (TypeError, ValueError):
                row_plan_id = 0
            if row_plan_id != plan_id:
                continue
        result.append(row)
    return result


def create_budget_allocation(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Create a budget allocation and fire signal if drift threshold exceeded."""
    record = create_entity_for_tenant("budget_allocations", payload, tenant_id)

    try:
        allocated = float(record.get("allocated_amount") or 0)
        spent = float(record.get("spent_amount") or 0)
    except (TypeError, ValueError):
        allocated = 0.0
        spent = 0.0

    drift_rate = spent / max(allocated, 0.01)
    if drift_rate > 0.9:
        record_id = str(record.get("id") or "unknown")
        plan_id_val = str(record.get("plan_id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="finance.budget_drift.critical_threshold",
            aggregate_type="budget_allocation",
            aggregate_id=record_id,
            payload_json={
                "plan_id": plan_id_val,
                "category": record.get("category"),
                "allocated_amount": allocated,
                "spent_amount": spent,
                "drift_rate": round(drift_rate, 4),
                "source_entity_type": "budget_allocation",
                "source_entity_id": record_id,
            },
        )
    return record


def get_budget_brain_context(tenant_id: int) -> dict:
    """Return aggregated budget context snapshot for Brain Core."""
    plans = list_entities_for_tenant("budget_plans", tenant_id)
    allocations = list_entities_for_tenant("budget_allocations", tenant_id)

    total_plans = len(plans)
    by_status: dict[str, int] = {}
    total_budget = 0.0
    for p in plans:
        status = str(p.get("status") or "unknown").lower()
        by_status[status] = by_status.get(status, 0) + 1
        try:
            total_budget += float(p.get("total_amount") or 0)
        except (TypeError, ValueError):
            pass

    total_allocated = 0.0
    total_spent = 0.0
    drift_alerts = 0
    for a in allocations:
        try:
            alloc = float(a.get("allocated_amount") or 0)
            spent = float(a.get("spent_amount") or 0)
        except (TypeError, ValueError):
            alloc = 0.0
            spent = 0.0
        total_allocated += alloc
        total_spent += spent
        if alloc > 0 and spent / alloc > 0.9:
            drift_alerts += 1

    drift_rate = round(total_spent / max(total_allocated, 0.01), 4)
    risk_level = (
        "high" if drift_alerts > 0 or drift_rate > 0.9
        else ("medium" if drift_rate > 0.7 else "low")
    )

    return {
        "module": "budget_planning",
        "tenant_id": tenant_id,
        "total_plans": total_plans,
        "total_budget": round(total_budget, 2),
        "total_allocated": round(total_allocated, 2),
        "total_spent": round(total_spent, 2),
        "drift_rate": drift_rate,
        "drift_alerts": drift_alerts,
        "by_status": by_status,
        "risk_level": risk_level,
    }
