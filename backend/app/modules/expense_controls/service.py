"""Phase V-V2: Expense controls service."""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)

# ---------------------------------------------------------------------------
# W116: Cost-center active gate — expenses may only be created against active
# cost centers. Creating expenses against inactive/frozen/closed cost centers
# bypasses financial freeze controls and corrupts budget reconciliation.
# ---------------------------------------------------------------------------
_COST_CENTER_REQUIRED_ACTIVE: bool = True

_EXPENSE_CATEGORY_MAX_ACTIVE: dict[str, int] = {
    "travel": 3,
    "software": 5,
    "equipment": 2,
    "general": 10,
}
_ACTIVE_STATUSES_EC: frozenset[str] = frozenset({"pending", "in_review"})

# W62: budget risk statuses for expense records
_BUDGET_RISK_STATUSES: frozenset[str] = frozenset({"pending", "in_review", "approved"})


def _check_cost_center_is_active(
    *,
    tenant_id: int,
    cost_center_id: int,
) -> None:
    """W116: Cross-entity guard — expense_records × cost_centers.active.

    An expense record may only be created against an ACTIVE cost center.
    Cost centers are deactivated/frozen when a budget cycle closes, when a
    department is restructured, or when a financial hold is placed on a unit.
    Creating expenses against a frozen/inactive cost center bypasses the freeze
    control, distorts active budget tracking, and corrupts reconciliation.

    FAIL-CLOSED: If the cost_centers lookup fails, the expense creation is
    BLOCKED. A query fault must never silently allow a bypass of this control.

    Real-world invariant: Institutional financial policy prohibits posting expenses
    to closed or frozen cost centers. Only active cost centers accept new charges.
    """
    if not _COST_CENTER_REQUIRED_ACTIVE:
        return  # sentinel: if guard is ever disabled, skip

    try:
        cost_centers = list_entities_for_tenant("cost_centers", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Expense creation blocked for cost_center_id={cost_center_id}: "
            f"cost_centers lookup failed — {exc}. "
            "Cannot verify cost center active status."
        ) from exc

    cc = next(
        (c for c in cost_centers if int(c.get("id") or 0) == cost_center_id),
        None,
    )
    if cc is None:
        raise DomainValidationError(
            f"Expense creation blocked: cost_center_id={cost_center_id} not found. "
            "Expenses require a valid, active cost center."
        )

    active_val = cc.get("active")
    # Treat None, False, 0, "false", "0", "inactive", "no" as inactive
    if active_val is None:
        is_active = False
    elif isinstance(active_val, bool):
        is_active = active_val
    elif isinstance(active_val, int):
        is_active = active_val != 0
    else:
        is_active = str(active_val).strip().lower() not in ("false", "0", "inactive", "no", "closed", "frozen", "disabled")

    if not is_active:
        cc_name = str(cc.get("name") or cc.get("code") or cost_center_id)
        raise DomainValidationError(
            f"Expense creation blocked: cost_center '{cc_name}' (id={cost_center_id}) "
            f"is not active (active={active_val!r}). "
            "Expenses may only be posted to active cost centers. "
            "Posting to a frozen or closed cost center bypasses financial freeze controls "
            "and corrupts budget reconciliation."
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
    cost_center_id = payload.get("cost_center_id")
    try:
        cost_center_id_val = int(cost_center_id or 0)
    except (TypeError, ValueError):
        cost_center_id_val = 0
    if cost_center_id_val <= 0:
        raise ValueError("cost_center_id must be a positive integer")

    # W116: FIRST — cost center must be active (before any other business logic)
    _check_cost_center_is_active(tenant_id=tenant_id, cost_center_id=cost_center_id_val)

    try:
        amount = float(payload.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0:
        raise ValueError("amount must be greater than 0")

    # Policy cap: limit active (pending/in_review) expenses per category.
    category = str(payload.get("category") or "").strip().lower()
    cap = _EXPENSE_CATEGORY_MAX_ACTIVE.get(category)
    if cap is not None:
        existing_rows = list_entities_for_tenant("expense_records", tenant_id)
        active_count = sum(
            1 for r in existing_rows
            if str(r.get("category") or "").strip().lower() == category
            and r.get("status") in _ACTIVE_STATUSES_EC
        )
        if active_count >= cap:
            raise ValueError(
                f"Active expense cap exceeded for category '{category}': "
                f"limit={cap}, current={active_count}"
            )

    # Budget guard: enforce total expenses within cost-center budget.
    cost_centers = list_entities_for_tenant("cost_centers", tenant_id)
    cc = next(
        (c for c in cost_centers if int(c.get("id") or 0) == cost_center_id_val),
        None,
    )
    if cc is None:
        raise ValueError("Cost center not found")

    try:
        budget_limit = float(cc.get("budget_limit") or 0)
    except (TypeError, ValueError):
        budget_limit = 0.0

    current_expenses = list_entities_for_tenant("expense_records", tenant_id)
    current_total = 0.0
    for row in current_expenses:
        try:
            row_cc_id = int(row.get("cost_center_id") or 0)
        except (TypeError, ValueError):
            row_cc_id = 0
        if row_cc_id != cost_center_id_val:
            continue
        if str(row.get("status") or "").strip().lower() == "rejected":
            continue
        try:
            current_total += float(row.get("amount") or 0)
        except (TypeError, ValueError):
            continue

    if budget_limit > 0 and current_total + amount > budget_limit:
        EventPublisher().publish_event(
            event_type="finance.expense.budget_exceeded",
            tenant_id=tenant_id,
            aggregate_type="expense_record",
            aggregate_id=str(cost_center_id_val),
            payload_json={
                "cost_center_id": cost_center_id_val,
                "amount": amount,
                "current_total": current_total,
                "budget_limit": budget_limit,
                "attempted_total": current_total + amount,
            },
        )
        raise ValueError(
            "Expense exceeds cost center budget_limit: "
            f"attempted_total={current_total + amount:.2f}, budget_limit={budget_limit:.2f}"
        )
    record = create_entity_for_tenant("expense_records", payload, tenant_id)

    try:
        amount_for_policy = float(record.get("amount") or 0)
    except (TypeError, ValueError):
        amount_for_policy = 0.0
    if amount_for_policy >= 5000.0:
        _ensure_expense_policy_review_record(record, tenant_id)

    return record


def _ensure_expense_policy_review_record(record: dict, tenant_id: int) -> None:
    """Idempotent: create a policy-review record for high-value expenses."""
    record_id = str(record.get("id") or "")
    existing = list_entities_for_tenant("expense_policy_review_records", tenant_id)
    for row in existing:
        if (
            str(row.get("integration_source") or "") == "expense_policy"
            and str(row.get("source_entity_id") or "") == record_id
        ):
            return
    create_entity_for_tenant(
        "expense_policy_review_records",
        {
            "expense_id": record_id,
            "expense_code": str(record.get("category") or ""),
            "cost_center_id": str(record.get("cost_center_id") or ""),
            "amount": record.get("amount"),
            "status": "pending_review",
            "integration_source": "expense_policy",
            "source_entity_id": record_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_budget_exceeded_risk_alert_record(
    tenant_id: int,
    expense_id: int,
    expense_data: dict,
) -> None:
    """Idempotent: create a budget-exceeded alert when an expense exceeds cost center budget."""
    existing = list_entities_for_tenant("expense_budget_exceeded_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "budget_exceeded_risk"
            and str(rec.get("source_entity_id")) == str(expense_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "expense_budget_exceeded_alerts",
        {
            "expense_id": expense_id,
            "cost_center_id": int(expense_data.get("cost_center_id") or 0),
            "category": str(expense_data.get("category") or ""),
            "amount": expense_data.get("amount"),
            "alert_status": "open",
            "integration_source": "budget_exceeded_risk",
            "source_entity_id": str(expense_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.expense_controls.budget_exceeded_risk_detected",
        aggregate_type="expense_record",
        aggregate_id=str(expense_id),
        payload_json={
            "expense_id": expense_id,
            "cost_center_id": int(expense_data.get("cost_center_id") or 0),
            "category": str(expense_data.get("category") or ""),
            "amount": expense_data.get("amount"),
            "source_module": "expense_controls",
            "source_entity_type": "expense_record",
            "source_entity_id": str(expense_id),
        },
    )


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
