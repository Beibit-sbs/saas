"""Phase V-V1: Budget planning service — budget plans, allocations, drift tracking."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.core.module_helpers.service_validation import DomainValidationError


_BUDGET_PLAN_STATUSES = {"draft", "submitted", "approved", "rejected"}
_BUDGET_PLAN_STATUS_MAX_ACTIVE: dict[str, int] = {"draft": 50, "submitted": 30, "approved": 100, "rejected": 200}
_ACTIVE_PLAN_STATUSES = frozenset({"draft", "submitted"})
_OVERRUN_RISK_STATUSES = frozenset({"rejected"})
_ALLOWED_BUDGET_PLAN_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted"},
    "submitted": {"approved", "rejected"},
    "approved": set(),
    "rejected": set(),
}

# W88: uniqueness guard — one approved plan per (department_id, fiscal_year)
_APPROVAL_UNIQUENESS_STATUSES: frozenset[str] = frozenset({"approved"})

# W113: only approved plans may receive allocations
_APPROVED_PLAN_STATUS_FOR_ALLOCATION: frozenset[str] = frozenset({"approved"})


def _check_budget_plan_approved_for_allocation(
    *,
    tenant_id: int,
    plan_id: int,
) -> None:
    """Cross-entity guard: budget_allocations × budget_plans by plan_id.

    Budget allocations may ONLY be created against an APPROVED budget plan.
    Allocating funds against a draft, submitted, or rejected plan creates
    phantom financial commitments without proper organizational authorization:

    - draft: not reviewed — no authority to commit funds
    - submitted: pending approval — authorization not yet granted
    - rejected: explicitly denied — allocating is an authorization bypass

    FAIL-CLOSED: if plan lookup raises any exception, allocation is BLOCKED.
    Cannot commit organizational funds without confirmed budget authority.
    """
    try:
        all_plans = list_entities_for_tenant("budget_plans", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Budget allocation blocked for plan_id={plan_id}: "
            f"budget plan lookup failed \u2014 {exc}. "
            f"Cannot commit funds without verifying budget authorization."
        ) from exc

    plan = next((row for row in all_plans if int(row.get("id") or 0) == plan_id), None)

    if plan is None:
        raise DomainValidationError(
            f"Budget allocation blocked: budget plan plan_id={plan_id} not found. "
            f"Cannot allocate funds against a non-existent budget plan."
        )

    plan_status = str(plan.get("status") or "").strip().lower()
    if plan_status not in _APPROVED_PLAN_STATUS_FOR_ALLOCATION:
        raise DomainValidationError(
            f"Budget allocation blocked for plan_id={plan_id}: "
            f"plan status is '{plan_status}' but only 'approved' plans may receive allocations. "
            f"Allocating against a {plan_status!r} plan creates unauthorized financial "
            f"commitments. Submit and approve the budget plan before allocating funds."
        )


def _normalize_budget_plan_status(status: object) -> str:
    normalized = str(status or "draft").strip().lower()
    if normalized not in _BUDGET_PLAN_STATUSES:
        raise ValueError(f"Unsupported budget plan status '{status}'")
    return normalized


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
    status = _normalize_budget_plan_status(payload.get("status") or "draft")
    if status != "draft":
        raise ValueError("Budget plans must be created in 'draft' status")
    all_plans = list_entities_for_tenant("budget_plans", tenant_id)
    active_count = sum(
        1 for p in all_plans
        if str(p.get("status", "")).strip().lower() in _ACTIVE_PLAN_STATUSES
    )
    cap = _BUDGET_PLAN_STATUS_MAX_ACTIVE.get(status, 50)
    if active_count >= cap:
        raise ValueError(
            f"Active budget plan cap reached for status '{status}': {active_count}/{cap}"
        )
    return create_entity_for_tenant("budget_plans", {**payload, "status": status}, tenant_id)


def _ensure_cost_center_for_approved_plan(plan: dict[str, object], tenant_id: int) -> None:
    """Create or keep a matching expense_controls cost center when plan is approved.

    This wiring must never break budget_plan status transitions.
    """
    try:
        from app.modules.expense_controls.service import create_cost_center

        department_id = str(plan.get("department_id") or "GENERAL").strip() or "GENERAL"
        fiscal_year = str(plan.get("fiscal_year") or "0000").strip() or "0000"
        code = f"BP-{department_id}-{fiscal_year}"[:64]
        name = f"Budget Plan {department_id} {fiscal_year}"[:128]
        currency = str(plan.get("currency") or "USD").strip() or "USD"
        budget_limit = float(plan.get("total_amount") or 0.0)

        existing_cost_centers = list_entities_for_tenant("cost_centers", tenant_id)
        if any(str(row.get("code") or "").strip() == code for row in existing_cost_centers):
            return

        create_cost_center(
            {
                "name": name,
                "code": code,
                "department_id": department_id,
                "budget_limit": max(budget_limit, 0.0),
                "currency": currency,
                "active": True,
            },
            tenant_id,
        )
    except Exception:
        # Cross-module wiring must not break primary budget status updates.
        return


def _check_no_duplicate_approved_plan(
    tenant_id: int,
    plan_id: int,
    department_id: str,
    fiscal_year: object,
) -> None:
    """W88: Block approval when another approved plan already exists for same (dept, fiscal_year).

    Business invariant: a department cannot have two approved budget plans for the same
    fiscal year. Duplicate approvals create conflicting cost center codes and ambiguous
    budget authority — expense_records cannot determine which plan governs the spend.
    NO SILENT FALLBACK: query error → raises DomainValidationError.
    """
    try:
        rows = list_entities_for_tenant("budget_plans", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot approve budget plan: budget_plans query failed — cannot enforce "
            f"uniqueness invariant for department='{department_id}', fiscal_year={fiscal_year}. "
            f"Error: {exc}"
        ) from exc

    dept_str = str(department_id or "").strip().lower()
    try:
        fy_int = int(fiscal_year or 0)
    except (TypeError, ValueError):
        fy_int = 0

    for row in rows:
        if int(row.get("id") or 0) == plan_id:
            continue  # skip the plan being approved
        row_status = str(row.get("status") or "").strip().lower()
        row_dept = str(row.get("department_id") or "").strip().lower()
        try:
            row_fy = int(row.get("fiscal_year") or 0)
        except (TypeError, ValueError):
            row_fy = 0

        if (
            row_status in _APPROVAL_UNIQUENESS_STATUSES
            and row_dept == dept_str
            and row_fy == fy_int
            and dept_str  # only enforce when department_id is set
        ):
            conflict_id = int(row.get("id") or 0)
            raise DomainValidationError(
                f"Cannot approve budget plan_id={plan_id}: department='{department_id}' already "
                f"has an approved budget plan (plan_id={conflict_id}) for fiscal_year={fiscal_year}. "
                f"A department cannot have two approved budget plans for the same fiscal year — "
                f"this creates conflicting cost center authority and ambiguous expense allocation."
            )


def update_budget_plan_status(
    tenant_id: int,
    plan_id: int,
    status: str,
) -> dict[str, object] | None:
    rows = list_entities_for_tenant("budget_plans", tenant_id)
    existing = next((row for row in rows if int(row.get("id") or 0) == plan_id), None)
    if existing is None:
        return None

    current_status = _normalize_budget_plan_status(existing.get("status") or "draft")
    next_status = _normalize_budget_plan_status(status)
    if next_status not in _ALLOWED_BUDGET_PLAN_TRANSITIONS.get(current_status, set()):
        raise ValueError(
            f"Invalid budget plan transition from '{current_status}' to '{next_status}'"
        )

    # W88: enforce uniqueness — one approved plan per (department_id, fiscal_year)
    if next_status in _APPROVAL_UNIQUENESS_STATUSES:
        _check_no_duplicate_approved_plan(
            tenant_id=tenant_id,
            plan_id=plan_id,
            department_id=str(existing.get("department_id") or ""),
            fiscal_year=existing.get("fiscal_year"),
        )

    updated = update_entity_for_tenant(
        "budget_plans",
        plan_id,
        {**existing, "status": next_status},
        tenant_id,
    )

    if next_status == "approved" and updated is not None:
        _ensure_cost_center_for_approved_plan(updated, tenant_id)

    if next_status in _OVERRUN_RISK_STATUSES and updated is not None:
        _ensure_overrun_alert_record(plan_id, tenant_id)

    return updated


def _ensure_overrun_alert_record(plan_id: int, tenant_id: int) -> None:
    """Idempotently create a budget overrun alert record for a rejected plan."""
    existing = list_entities_for_tenant("budget_overrun_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source") or "").strip() == "budget_overrun_queue"
            and str(rec.get("source_entity_id") or "").strip() == str(plan_id)
        ):
            return
    create_entity_for_tenant(
        "budget_overrun_alerts",
        {
            "plan_id": plan_id,
            "alert_type": "plan_rejected",
            "integration_source": "budget_overrun_queue",
            "source_entity_id": str(plan_id),
        },
        tenant_id,
    )
    from app.platform.events.publisher import EventPublisher
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.budget.overrun_risk_detected",
        aggregate_type="budget_plan",
        aggregate_id=plan_id,
        payload_json={
            "plan_id": plan_id,
            "alert_type": "plan_rejected",
            "source_module": "budget_planning",
        },
    )


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
    plan_id_val = int(payload.get("plan_id") or 0)
    if plan_id_val <= 0:
        raise ValueError("plan_id must be a positive integer")

    # W113: Cross-entity guard — plan must be in approved status before allocation
    _check_budget_plan_approved_for_allocation(
        tenant_id=tenant_id,
        plan_id=plan_id_val,
    )

    plans = list_entities_for_tenant("budget_plans", tenant_id)
    plan = next((row for row in plans if int(row.get("id") or 0) == plan_id_val), None)
    if plan is None:
        raise ValueError("Budget plan not found")

    try:
        plan_total = float(plan.get("total_amount") or 0.0)
    except (TypeError, ValueError):
        plan_total = 0.0

    try:
        requested_allocation = float(payload.get("allocated_amount") or 0.0)
    except (TypeError, ValueError):
        requested_allocation = 0.0

    existing_allocations = list_entities_for_tenant("budget_allocations", tenant_id)
    already_allocated = 0.0
    for row in existing_allocations:
        try:
            row_plan_id = int(row.get("plan_id") or 0)
        except (TypeError, ValueError):
            row_plan_id = 0
        if row_plan_id != plan_id_val:
            continue
        try:
            already_allocated += float(row.get("allocated_amount") or 0.0)
        except (TypeError, ValueError):
            continue

    if already_allocated + requested_allocation > plan_total:
        raise ValueError(
            "Allocation exceeds plan total_amount: "
            f"allocated={already_allocated + requested_allocation:.2f}, total={plan_total:.2f}"
        )

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
