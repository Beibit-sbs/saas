"""Phase V-V1: Budget planning service — budget plans, allocations, drift tracking."""
from __future__ import annotations

import logging

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.core.module_helpers.service_validation import DomainValidationError
from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action


logger = logging.getLogger("app.modules.budget_planning")


_BUDGET_PLAN_STATUSES = {"draft", "review", "submitted", "approved", "locked", "rejected"}
_BUDGET_PLAN_STATUS_ALIASES: dict[str, str] = {"submitted": "review"}
_BUDGET_PLAN_STATUS_MAX_ACTIVE: dict[str, int] = {
    "draft": 50,
    "review": 30,
    "submitted": 30,
    "approved": 100,
    "locked": 100,
    "rejected": 200,
}
_ACTIVE_PLAN_STATUSES = frozenset({"draft", "review", "submitted"})
_OVERRUN_RISK_STATUSES = frozenset({"rejected"})
_ALLOWED_BUDGET_PLAN_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"review", "submitted"},
    "review": {"approved", "rejected"},
    "submitted": {"approved", "rejected", "review"},
    "approved": {"locked"},
    "locked": set(),
    "rejected": set(),
}

# W88: uniqueness guard — one approved plan per (department_id, fiscal_year)
_APPROVAL_UNIQUENESS_STATUSES: frozenset[str] = frozenset({"approved"})

# W113: only approved plans may receive allocations
_APPROVED_PLAN_STATUS_FOR_ALLOCATION: frozenset[str] = frozenset({"approved"})


def _normalize_status_for_transition(status: str) -> str:
    return _BUDGET_PLAN_STATUS_ALIASES.get(status, status)


def _event_type_for_status(status: str) -> str | None:
    return {
        "review": "budget_plan.review_requested",
        "submitted": "budget_plan.review_requested",
        "approved": "budget_plan.approved",
        "locked": "budget_plan.locked",
        "rejected": "budget_plan.rejected",
    }.get(status)


def _publish_budget_event(
    *,
    tenant_id: int,
    event_type: str,
    aggregate_type: str,
    aggregate_id: int,
    payload_json: dict[str, object],
) -> None:
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=payload_json,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "budget event publish failed tenant_id=%s event_type=%s aggregate_type=%s aggregate_id=%s",
            tenant_id,
            event_type,
            aggregate_type,
            aggregate_id,
        )


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        from app.modules.usage.service import record_usage_event

        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:  # noqa: BLE001
        logger.exception(
            "budget metric record failed tenant_id=%s metric=%s value=%s",
            tenant_id,
            metric,
            value,
        )


def _record_outcome(*, tenant_id: int, signal_id: str, outcome_type: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            signal_id,
            payload={
                "outcome_type": outcome_type,
                "source_module": "budget_planning",
                "tenant_id": tenant_id,
            },
            actor=actor,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "budget outcome record failed tenant_id=%s signal_id=%s outcome_type=%s",
            tenant_id,
            signal_id,
            outcome_type,
        )


def _emit_audit(
    *,
    actor: str,
    action: str,
    path: str,
    metadata: dict[str, object],
    tenant_id: int,
) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=path,
            client_ip="service",
            entity="budget_planning",
            metadata=metadata,
            tenant_id=tenant_id,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "budget audit emit failed tenant_id=%s action=%s path=%s",
            tenant_id,
            action,
            path,
        )


def _create_plan_lock_outcome_record(
    *,
    tenant_id: int,
    plan_id: int,
    actor: str,
) -> None:
    create_entity_for_tenant(
        "budget_overrun_alerts",
        {
            "plan_id": plan_id,
            "alert_type": "plan_locked_outcome_recorded",
            "integration_source": "budget_plan_workflow",
            "source_entity_id": str(plan_id),
            "tenant_id": str(tenant_id),
        },
        tenant_id,
    )
    _publish_budget_event(
        tenant_id=tenant_id,
        event_type="budget_plan.outcome_recorded",
        aggregate_type="budget_plan",
        aggregate_id=plan_id,
        payload_json={
            "plan_id": plan_id,
            "outcome": "locked",
            "actor": actor,
            "source_module": "budget_planning",
        },
    )


def _ensure_lock_action_path(plan: dict[str, object], tenant_id: int) -> None:
    """Fail-closed check: lock transition requires an auditable expense record."""
    department_id = str(plan.get("department_id") or "GENERAL").strip() or "GENERAL"
    fiscal_year = str(plan.get("fiscal_year") or "0000").strip() or "0000"
    payload = {
        "cost_center_id": f"BP-{department_id}-{fiscal_year}"[:64],
        "category": "budget_lock",
        "amount": max(float(plan.get("total_amount") or 0.0), 0.0),
        "currency": str(plan.get("currency") or "USD").strip() or "USD",
        "status": "locked",
        "description": f"Budget plan {plan.get('id')} locked for execution",
        "tenant_id": str(tenant_id),
    }
    try:
        create_entity_for_tenant("expense_records", payload, tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot lock budget plan_id={plan.get('id')}: failed to persist lock action record. "
            f"Reason: {exc}"
        ) from exc


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
    actor: str = "system",
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
    record = create_entity_for_tenant("budget_plans", {**payload, "status": status}, tenant_id)
    plan_id = int(record.get("id") or 0)
    _publish_budget_event(
        tenant_id=tenant_id,
        event_type="budget_plan.created",
        aggregate_type="budget_plan",
        aggregate_id=plan_id,
        payload_json={
            "plan_id": plan_id,
            "department_id": record.get("department_id"),
            "fiscal_year": record.get("fiscal_year"),
            "status": record.get("status"),
            "actor": actor,
            "source_module": "budget_planning",
        },
    )
    _record_outcome(
        tenant_id=tenant_id,
        signal_id=f"budget_plan:{plan_id}",
        outcome_type="plan_created",
        actor=actor,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("budget_planning", "budget_plan", "create"),
        path="/internal/budget-planning/plans",
        metadata={
            "plan_id": plan_id,
            "department_id": record.get("department_id"),
            "fiscal_year": record.get("fiscal_year"),
            "status": record.get("status"),
        },
        tenant_id=tenant_id,
    )
    _metric(tenant_id, "budget_plans_created", 1)
    return record


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
    actor: str = "system",
) -> dict[str, object] | None:
    rows = list_entities_for_tenant("budget_plans", tenant_id)
    existing = next((row for row in rows if int(row.get("id") or 0) == plan_id), None)
    if existing is None:
        return None

    current_status = _normalize_budget_plan_status(existing.get("status") or "draft")
    next_status = _normalize_budget_plan_status(status)
    current_transition_status = _normalize_status_for_transition(current_status)
    next_transition_status = _normalize_status_for_transition(next_status)
    if next_transition_status not in _ALLOWED_BUDGET_PLAN_TRANSITIONS.get(current_transition_status, set()):
        raise ValueError(
            f"Invalid budget plan transition from '{current_status}' to '{next_status}'"
        )

    # W88: enforce uniqueness — one approved plan per (department_id, fiscal_year)
    if next_transition_status in _APPROVAL_UNIQUENESS_STATUSES:
        _check_no_duplicate_approved_plan(
            tenant_id=tenant_id,
            plan_id=plan_id,
            department_id=str(existing.get("department_id") or ""),
            fiscal_year=existing.get("fiscal_year"),
        )

    if next_transition_status == "locked":
        _ensure_lock_action_path(existing, tenant_id)

    updated = update_entity_for_tenant(
        "budget_plans",
        plan_id,
        {**existing, "status": next_status},
        tenant_id,
    )

    if next_transition_status == "approved" and updated is not None:
        _ensure_cost_center_for_approved_plan(updated, tenant_id)

    if next_transition_status in _OVERRUN_RISK_STATUSES and updated is not None:
        _ensure_overrun_alert_record(plan_id, tenant_id)

    if updated is not None:
        event_type = _event_type_for_status(next_status)
        if event_type:
            _publish_budget_event(
                tenant_id=tenant_id,
                event_type=event_type,
                aggregate_type="budget_plan",
                aggregate_id=plan_id,
                payload_json={
                    "plan_id": plan_id,
                    "from_status": current_status,
                    "to_status": next_status,
                    "department_id": updated.get("department_id"),
                    "fiscal_year": updated.get("fiscal_year"),
                    "actor": actor,
                    "source_module": "budget_planning",
                },
            )
        _record_outcome(
            tenant_id=tenant_id,
            signal_id=f"budget_plan:{plan_id}",
            outcome_type=f"status_{next_transition_status}",
            actor=actor,
        )
        _emit_audit(
            actor=actor,
            action=build_audit_action("budget_planning", "budget_plan", "transition"),
            path=f"/internal/budget-planning/plans/{plan_id}/status",
            metadata={
                "plan_id": plan_id,
                "from_status": current_status,
                "to_status": next_status,
            },
            tenant_id=tenant_id,
        )
        _metric(tenant_id, "budget_plan_status_transitions", 1)

    if next_transition_status == "locked" and updated is not None:
        _create_plan_lock_outcome_record(tenant_id=tenant_id, plan_id=plan_id, actor=actor)

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
    actor: str = "system",
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
    record_id = int(record.get("id") or 0)
    _publish_budget_event(
        tenant_id=tenant_id,
        event_type="budget_allocation.created",
        aggregate_type="budget_allocation",
        aggregate_id=record_id,
        payload_json={
            "allocation_id": record_id,
            "plan_id": int(record.get("plan_id") or 0),
            "category": record.get("category"),
            "allocated_amount": record.get("allocated_amount"),
            "spent_amount": record.get("spent_amount"),
            "actor": actor,
            "source_module": "budget_planning",
        },
    )

    try:
        allocated = float(record.get("allocated_amount") or 0)
        spent = float(record.get("spent_amount") or 0)
    except (TypeError, ValueError):
        allocated = 0.0
        spent = 0.0

    drift_rate = spent / max(allocated, 0.01)
    if drift_rate > 0.9:
        plan_id_str = str(record.get("plan_id") or "unknown")
        _publish_budget_event(
            tenant_id=tenant_id,
            event_type="finance.budget_variance.threshold_reached",
            aggregate_type="budget_allocation",
            aggregate_id=record_id,
            payload_json={
                "plan_id": plan_id_str,
                "category": record.get("category"),
                "allocated_amount": allocated,
                "spent_amount": spent,
                "drift_rate": round(drift_rate, 4),
                "source_entity_type": "budget_allocation",
                "source_entity_id": str(record_id),
                "actor": actor,
            },
        )
    _record_outcome(
        tenant_id=tenant_id,
        signal_id=f"budget_allocation:{record_id}",
        outcome_type="allocation_created",
        actor=actor,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("budget_planning", "budget_allocation", "create"),
        path="/internal/budget-planning/allocations",
        metadata={
            "allocation_id": record_id,
            "plan_id": int(record.get("plan_id") or 0),
            "allocated_amount": record.get("allocated_amount"),
            "spent_amount": record.get("spent_amount"),
        },
        tenant_id=tenant_id,
    )
    _metric(tenant_id, "budget_allocations_created", 1)
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
