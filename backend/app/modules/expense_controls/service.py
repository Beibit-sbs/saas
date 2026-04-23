"""Phase V-V2: Expense controls service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_expense_records(
    tenant_id: int,
    cost_center_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    rows = list_entities_for_tenant("expense_records", tenant_id)
    result: list[dict] = []
    for row in rows:
        if cost_center_id is not None:
            try:
                row_cc_id = int(row.get("cost_center_id") or 0)
            except (TypeError, ValueError):
                row_cc_id = 0
            if row_cc_id != cost_center_id:
                continue
        if status is not None and row.get("status") != status:
            continue
        result.append(row)
    return result


def create_expense_record(
    payload: dict,
    tenant_id: int,
) -> dict:
    record = create_entity_for_tenant("expense_records", payload, tenant_id)

    # Brain signal: budget exceeded — fire when amount > budget_limit of the cost center
    cost_center_id = payload.get("cost_center_id")
    try:
        amount = float(record.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0

    cost_centers = list_entities_for_tenant("cost_centers", tenant_id)
    cc = next(
        (c for c in cost_centers if int(c.get("id") or 0) == cost_center_id),
        None,
    )
    if cc is not None:
        try:
            budget_limit = float(cc.get("budget_limit") or 0)
        except (TypeError, ValueError):
            budget_limit = 0.0
        if budget_limit > 0 and amount > budget_limit:
            record_id = str(record.get("id") or "unknown")
            EventPublisher().publish_event(
                event_type="finance.expense.budget_exceeded",
                tenant_id=tenant_id,
                aggregate_type="expense_record",
                aggregate_id=record_id,
                payload_json={
                    "cost_center_id": cost_center_id,
                    "amount": amount,
                    "budget_limit": budget_limit,
                },
            )

    return record


def list_cost_centers(
    tenant_id: int,
    active: bool | None = None,
) -> list[dict]:
    rows = list_entities_for_tenant("cost_centers", tenant_id)
    if active is None:
        return rows
    return [r for r in rows if bool(r.get("active")) == active]


def create_cost_center(
    payload: dict,
    tenant_id: int,
) -> dict:
    return create_entity_for_tenant("cost_centers", payload, tenant_id)


def get_expense_brain_context(tenant_id: int) -> dict:
    """Return aggregated expense context snapshot for Brain Core."""
    expenses = list_entities_for_tenant("expense_records", tenant_id)
    cost_centers = list_entities_for_tenant("cost_centers", tenant_id)

    pending = sum(1 for e in expenses if e.get("status") == "pending")
    approved = sum(1 for e in expenses if e.get("status") == "approved")

    cc_map = {int(c.get("id") or 0): c for c in cost_centers}
    budget_exceeded_alerts = 0
    for expense in expenses:
        try:
            cc_id = int(expense.get("cost_center_id") or 0)
            amount = float(expense.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        cc = cc_map.get(cc_id)
        if cc is not None:
            try:
                limit = float(cc.get("budget_limit") or 0)
            except (TypeError, ValueError):
                limit = 0.0
            if limit > 0 and amount > limit:
                budget_exceeded_alerts += 1

    if budget_exceeded_alerts > 0:
        risk_level = "high"
    elif len(expenses) > 0 and pending > len(expenses) * 0.5:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "module": "expense_controls",
        "tenant_id": tenant_id,
        "total_expenses": len(expenses),
        "total_cost_centers": len(cost_centers),
        "pending_expenses": pending,
        "approved_expenses": approved,
        "budget_exceeded_alerts": budget_exceeded_alerts,
        "risk_level": risk_level,
    }
