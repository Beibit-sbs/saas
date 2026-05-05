"""A-015.5 — Inventory Low Stock / Supply Risk Brain helper.

Deterministic, tenant-scoped supply risk classification based on
quantity/threshold relationship. No LLM, no external services,
no cross-tenant aggregation.

Flow:
  inventory item data (item_id, current_quantity, reorder_threshold, ...)
  → risk classification (critical / high / medium / low)
  → recommended_actions
  → Brain-Core-compatible decision dict
"""
from __future__ import annotations

import uuid
from typing import Any


# ──────────────────────────────────────────────────────────────────────────────
# Deterministic risk classification
# ──────────────────────────────────────────────────────────────────────────────

def classify_supply_risk(
    current_quantity: float | int | None,
    reorder_threshold: float | int | None,
) -> str:
    """Classify supply risk level from quantity vs. threshold.

    Rules (deterministic, in priority order):
    - quantity is None or threshold is None → medium (unknown state)
    - quantity <= 0                          → critical
    - quantity < threshold * 0.5            → high
    - quantity < threshold                  → medium
    - quantity >= threshold                 → low
    """
    if current_quantity is None or reorder_threshold is None:
        return "medium"
    qty = float(current_quantity)
    thr = float(reorder_threshold)
    if qty <= 0:
        return "critical"
    if thr > 0 and qty < thr * 0.5:
        return "high"
    if thr > 0 and qty < thr:
        return "medium"
    return "low"


def build_shortage_amount(
    current_quantity: float | int | None,
    reorder_threshold: float | int | None,
) -> float:
    """How many units below reorder threshold (0 if at/above threshold)."""
    if current_quantity is None or reorder_threshold is None:
        return 0.0
    shortage = float(reorder_threshold) - float(current_quantity)
    return max(0.0, shortage)


# ──────────────────────────────────────────────────────────────────────────────
# Recommended actions builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_supply_risk_actions(
    risk_level: str,
    *,
    vendor_id: str | None,
    budget_id: str | None,
    shortage_amount: float,
    item_id: str | None,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    if risk_level in ("critical", "high"):
        actions.append({
            "type": "create_procurement_request",
            "severity": "critical" if risk_level == "critical" else "high",
            "reason": f"Stock critically low; shortage_amount={shortage_amount:.1f}; item_id={item_id}",
            "source": "inventory",
        })
        if vendor_id:
            actions.append({
                "type": "vendor_followup",
                "severity": risk_level,
                "reason": f"Vendor escalation required for low-stock item_id={item_id}; vendor={vendor_id}",
                "source": "procurement",
            })
    elif risk_level == "medium":
        actions.append({
            "type": "reorder_review",
            "severity": "medium",
            "reason": f"Stock below reorder threshold; shortage_amount={shortage_amount:.1f}",
            "source": "inventory",
        })

    if budget_id and risk_level in ("critical", "high", "medium"):
        actions.append({
            "type": "budget_review",
            "severity": "low",
            "reason": f"Procurement spend may be required for reorder; budget_id={budget_id}",
            "source": "budget",
        })

    return actions


# ──────────────────────────────────────────────────────────────────────────────
# Evidence builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_evidence(
    *,
    item_id: str | None,
    current_quantity: float | int | None,
    reorder_threshold: float | int | None,
    shortage_amount: float,
    department: str | None,
    location: str | None,
    vendor_id: str | None,
    budget_id: str | None,
    missing_fields: list[str],
) -> list[str]:
    evidence: list[str] = []
    if item_id:
        evidence.append(f"item_id={item_id}")
    if current_quantity is not None:
        evidence.append(f"current_quantity={current_quantity}")
    if reorder_threshold is not None:
        evidence.append(f"reorder_threshold={reorder_threshold}")
    if shortage_amount > 0:
        evidence.append(f"shortage_amount={shortage_amount:.1f}")
    if department:
        evidence.append(f"department={department}")
    if location:
        evidence.append(f"location={location}")
    if vendor_id:
        evidence.append(f"vendor_id={vendor_id}")
    if budget_id:
        evidence.append(f"budget_id={budget_id}")
    if missing_fields:
        evidence.append(f"missing_optional_fields={missing_fields}")
    return evidence


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

def compute_inventory_supply_risk(
    *,
    tenant_id: int,
    item_id: str | None = None,
    item_name: str | None = None,
    current_quantity: float | int | None = None,
    reorder_threshold: float | int | None = None,
    required_quantity: float | int | None = None,
    department: str | None = None,
    location: str | None = None,
    vendor_id: str | None = None,
    budget_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Compute deterministic Inventory / Supply Risk Brain decision.

    Fail-closed: raises ValueError if tenant_id <= 0 or item_id is missing.
    All other parameters are optional; missing optional data appears in evidence
    and does not prevent classification.

    Returns a Brain-Core-compatible decision dict.
    """
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id is required and must be > 0")
    if not item_id:
        raise ValueError("item_id is required for supply risk classification")

    # Track which optional context fields were absent
    missing_fields: list[str] = []
    if current_quantity is None:
        missing_fields.append("current_quantity")
    if reorder_threshold is None:
        missing_fields.append("reorder_threshold")
    if vendor_id is None:
        missing_fields.append("vendor_id")
    if budget_id is None:
        missing_fields.append("budget_id")

    risk_level = classify_supply_risk(current_quantity, reorder_threshold)
    shortage_amount = build_shortage_amount(current_quantity, reorder_threshold)

    recommended_actions = _build_supply_risk_actions(
        risk_level,
        vendor_id=vendor_id,
        budget_id=budget_id,
        shortage_amount=shortage_amount,
        item_id=item_id,
    )

    evidence = _build_evidence(
        item_id=item_id,
        current_quantity=current_quantity,
        reorder_threshold=reorder_threshold,
        shortage_amount=shortage_amount,
        department=department,
        location=location,
        vendor_id=vendor_id,
        budget_id=budget_id,
        missing_fields=missing_fields,
    )

    explanation_parts = [
        f"risk_level={risk_level}",
        f"item_id={item_id}",
    ]
    if current_quantity is not None:
        explanation_parts.append(f"current_quantity={current_quantity}")
    if reorder_threshold is not None:
        explanation_parts.append(f"reorder_threshold={reorder_threshold}")
    if shortage_amount > 0:
        explanation_parts.append(f"shortage_amount={shortage_amount:.1f}")
    if missing_fields:
        explanation_parts.append(f"missing_context={missing_fields}")

    return {
        "tenant_id": tenant_id,
        "decision_type": "supply_risk",
        "scenario": "inventory_low_stock",
        "risk_level": risk_level,
        "item_id": item_id,
        "item_name": item_name,
        "current_quantity": current_quantity,
        "reorder_threshold": reorder_threshold,
        "shortage_amount": shortage_amount,
        "recommended_actions": recommended_actions,
        "evidence": evidence,
        "explanation": "; ".join(explanation_parts),
        "correlation_id": correlation_id or str(uuid.uuid4()),
    }
