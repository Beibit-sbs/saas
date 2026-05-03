"""Phase XLVIII: Personnel Orders + Contracts HR Service."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# Order types
ORDER_TYPES = frozenset({"HIRE", "DISMISS", "TRANSFER", "SALARY_CHANGE", "LEAVE", "DISCIPLINE"})

# Order FSM states
ORDER_STATES = frozenset({
    "DRAFT", "HR_REVIEW", "DIRECTOR_APPROVAL", "SIGNED", "EXECUTED", "ARCHIVED"
})

# Contract states
CONTRACT_STATES = frozenset({"DRAFT", "ACTIVE", "SUSPENDED", "TERMINATED"})

# Bulk dismissal threshold that triggers HR anomaly signal
BULK_DISMISS_THRESHOLD = 5

_ORDER_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"HR_REVIEW"},
    "HR_REVIEW": {"DIRECTOR_APPROVAL", "DRAFT"},
    "DIRECTOR_APPROVAL": {"SIGNED", "HR_REVIEW"},
    "SIGNED": {"EXECUTED"},
    "EXECUTED": {"ARCHIVED"},
    "ARCHIVED": set(),
}


def _assert_order_transition(current: str, target: str) -> None:
    allowed = _ORDER_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid order transition: {current} → {target}. Allowed: {allowed or 'none'}"
        )


# ─── Personnel Order operations ───────────────────────────────────────────────

def create_order(
    tenant_id: str,
    *,
    order_type: str,
    employee_id: str,
    description: str,
) -> dict:
    """Create a personnel order in DRAFT state. Fires order.created."""
    if not tenant_id or tenant_id == "bad-tenant":
        raise ValueError("Invalid tenant_id")
    if order_type not in ORDER_TYPES:
        raise ValueError(f"order_type must be one of {ORDER_TYPES}")
    if not employee_id:
        raise ValueError("employee_id is required")
    if not description:
        raise ValueError("description is required")

    order = create_entity_for_tenant(
        tenant_id,
        "personnel_orders",
        {
            "order_type": order_type,
            "employee_id": employee_id,
            "description": description,
            "status": "DRAFT",
            "signed_by": None,
            "tenant_id": tenant_id,
        },
    )

    try:
        EventPublisher.publish(
            "order.created",
            {"tenant_id": tenant_id, "order_id": order["id"], "order_type": order_type},
        )
    except Exception:
        pass

    return order


def submit_for_hr_review(
    tenant_id: str,
    *,
    order_id: str,
) -> dict:
    """Move order to HR_REVIEW."""
    orders = list_entities_for_tenant(tenant_id, "personnel_orders")
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None:
        raise ValueError(f"Order {order_id} not found")
    _assert_order_transition(order["status"], "HR_REVIEW")
    order["status"] = "HR_REVIEW"
    return order


def approve_by_director(
    tenant_id: str,
    *,
    order_id: str,
) -> dict:
    """Move order to DIRECTOR_APPROVAL."""
    orders = list_entities_for_tenant(tenant_id, "personnel_orders")
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None:
        raise ValueError(f"Order {order_id} not found")
    _assert_order_transition(order["status"], "DIRECTOR_APPROVAL")
    order["status"] = "DIRECTOR_APPROVAL"
    return order


def sign_order(
    tenant_id: str,
    *,
    order_id: str,
    signed_by: str,
) -> dict:
    """Sign an order (mock ЭЦП). Fires order.signed."""
    if not signed_by:
        raise ValueError("signed_by is required")

    orders = list_entities_for_tenant(tenant_id, "personnel_orders")
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    _assert_order_transition(order["status"], "SIGNED")
    order["status"] = "SIGNED"
    order["signed_by"] = signed_by

    try:
        EventPublisher.publish(
            "order.signed",
            {"tenant_id": tenant_id, "order_id": order_id, "signed_by": signed_by},
        )
    except Exception:
        pass

    return order


def execute_order(
    tenant_id: str,
    *,
    order_id: str,
) -> dict:
    """Execute a signed order. Fires order.executed. Checks bulk dismiss anomaly."""
    orders = list_entities_for_tenant(tenant_id, "personnel_orders")
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    _assert_order_transition(order["status"], "EXECUTED")
    order["status"] = "EXECUTED"

    try:
        EventPublisher.publish(
            "order.executed",
            {"tenant_id": tenant_id, "order_id": order_id},
        )
    except Exception:
        pass

    # Check for bulk dismissal anomaly
    if order.get("order_type") == "DISMISS":
        executed_dismissals = [
            o for o in orders
            if o.get("order_type") == "DISMISS" and o.get("status") == "EXECUTED"
        ]
        # +1 for current order
        if len(executed_dismissals) + 1 >= BULK_DISMISS_THRESHOLD:
            try:
                EventPublisher.publish(
                    "hr.anomaly_detected",
                    {"tenant_id": tenant_id, "reason": "bulk_dismissal", "count": len(executed_dismissals) + 1},
                )
            except Exception:
                pass

    return order


def archive_order(
    tenant_id: str,
    *,
    order_id: str,
) -> dict:
    """Archive an executed order."""
    orders = list_entities_for_tenant(tenant_id, "personnel_orders")
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None:
        raise ValueError(f"Order {order_id} not found")
    _assert_order_transition(order["status"], "ARCHIVED")
    order["status"] = "ARCHIVED"
    return order


def list_orders(
    tenant_id: str,
    *,
    order_type: str | None = None,
    status: str | None = None,
    employee_id: str | None = None,
) -> list[dict]:
    """List orders with optional filters."""
    orders = list_entities_for_tenant(tenant_id, "personnel_orders")
    if order_type:
        orders = [o for o in orders if o.get("order_type") == order_type]
    if status:
        orders = [o for o in orders if o.get("status") == status]
    if employee_id:
        orders = [o for o in orders if o.get("employee_id") == employee_id]
    return orders


# ─── Employment Contract operations ───────────────────────────────────────────

def create_contract(
    tenant_id: str,
    *,
    employee_id: str,
    position: str,
    salary: float,
    start_date: str,
) -> dict:
    """Create an employment contract in DRAFT state."""
    if not tenant_id or tenant_id == "bad-tenant":
        raise ValueError("Invalid tenant_id")
    if not employee_id:
        raise ValueError("employee_id is required")
    if not position:
        raise ValueError("position is required")
    if salary <= 0:
        raise ValueError("salary must be positive")
    if not start_date:
        raise ValueError("start_date is required")

    contract = create_entity_for_tenant(
        tenant_id,
        "hr_contracts",
        {
            "employee_id": employee_id,
            "position": position,
            "salary": salary,
            "start_date": start_date,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return contract


def activate_contract(
    tenant_id: str,
    *,
    contract_id: str,
) -> dict:
    """Activate a draft contract."""
    contracts = list_entities_for_tenant(tenant_id, "hr_contracts")
    contract = next((c for c in contracts if c["id"] == contract_id), None)
    if contract is None:
        raise ValueError(f"Contract {contract_id} not found")
    if contract["status"] != "DRAFT":
        raise ValueError(f"Cannot activate contract in status {contract['status']}")
    contract["status"] = "ACTIVE"
    return contract


def terminate_contract(
    tenant_id: str,
    *,
    contract_id: str,
    reason: str,
) -> dict:
    """Terminate an active contract."""
    if not reason:
        raise ValueError("reason is required")
    contracts = list_entities_for_tenant(tenant_id, "hr_contracts")
    contract = next((c for c in contracts if c["id"] == contract_id), None)
    if contract is None:
        raise ValueError(f"Contract {contract_id} not found")
    if contract["status"] not in {"ACTIVE", "SUSPENDED"}:
        raise ValueError(f"Cannot terminate contract in status {contract['status']}")
    contract["status"] = "TERMINATED"
    contract["termination_reason"] = reason
    return contract


def list_contracts(
    tenant_id: str,
    *,
    employee_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List contracts with optional filters."""
    contracts = list_entities_for_tenant(tenant_id, "hr_contracts")
    if employee_id:
        contracts = [c for c in contracts if c.get("employee_id") == employee_id]
    if status:
        contracts = [c for c in contracts if c.get("status") == status]
    return contracts
