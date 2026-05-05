"""A-015.4 — Finance Operations Health Brain helper.

Deterministic, tenant-scoped health computation for 5 finance/procurement/asset
dimensions. No LLM, no external services, no cross-tenant aggregation.

Flow:
  budget/expense/procurement/asset data
  → per-dimension score + status + evidence
  → overall_score + risk_level
  → recommended_actions + explanation
"""
from __future__ import annotations

import uuid
from typing import Any


# ──────────────────────────────────────────────────────────────────────────────
# Scoring helpers
# ──────────────────────────────────────────────────────────────────────────────

def _score_to_status(score: float) -> str:
    if score >= 80:
        return "healthy"
    if score >= 60:
        return "watch"
    if score >= 40:
        return "risk"
    return "critical"


def _overall_risk_level(score: float) -> str:
    if score < 40:
        return "critical"
    if score < 60:
        return "high"
    if score < 75:
        return "medium"
    return "low"


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


# ──────────────────────────────────────────────────────────────────────────────
# Per-dimension scoring
# ──────────────────────────────────────────────────────────────────────────────

def _score_budget_health(budget_ctx: dict[str, Any] | None) -> dict[str, Any]:
    """Score budget health from get_budget_brain_context output."""
    if not budget_ctx:
        return {
            "score": 50,
            "status": "watch",
            "evidence": ["budget_context_unavailable"],
        }
    risk_level = str(budget_ctx.get("risk_level") or "low").lower()
    drift_rate = float(budget_ctx.get("drift_rate") or 0.0)
    drift_alerts = int(budget_ctx.get("drift_alerts") or 0)

    if risk_level == "high" or drift_alerts > 0 or drift_rate > 0.9:
        score = _clamp(30.0 - drift_alerts * 5)
        evidence = [f"budget_drift_rate={drift_rate:.2f}", f"drift_alerts={drift_alerts}"]
    elif risk_level == "medium" or drift_rate > 0.7:
        score = 60.0
        evidence = [f"budget_drift_rate={drift_rate:.2f}"]
    else:
        score = 90.0
        evidence = [f"budget_drift_rate={drift_rate:.2f}"]

    return {"score": score, "status": _score_to_status(score), "evidence": evidence}


def _score_procurement_health(procurement_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """Score procurement pipeline health from procurement health snapshot."""
    if not procurement_snapshot:
        return {
            "score": 50,
            "status": "watch",
            "evidence": ["procurement_context_unavailable"],
        }
    contracts_total = int(procurement_snapshot.get("contracts_total") or 0)
    contracts_high_risk = int(procurement_snapshot.get("contracts_high_risk") or 0)
    vendors_sla_breached = int(procurement_snapshot.get("vendors_sla_breached") or 0)

    penalty = contracts_high_risk * 15 + vendors_sla_breached * 10
    score = _clamp(100.0 - penalty)
    evidence = [
        f"contracts_total={contracts_total}",
        f"contracts_high_risk={contracts_high_risk}",
        f"vendors_sla_breached={vendors_sla_breached}",
    ]
    return {"score": score, "status": _score_to_status(score), "evidence": evidence}


def _score_po_delivery_health(procurement_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """Score PO delivery health based on at-risk contracts ratio."""
    if not procurement_snapshot:
        return {
            "score": 50,
            "status": "watch",
            "evidence": ["po_delivery_context_unavailable"],
        }
    contracts_total = int(procurement_snapshot.get("contracts_total") or 0)
    at_risk_contracts = int(procurement_snapshot.get("at_risk_contracts") or 0)

    if contracts_total == 0:
        score = 80.0
        evidence = ["no_contracts_present"]
    else:
        at_risk_ratio = at_risk_contracts / contracts_total
        score = _clamp(100.0 - at_risk_ratio * 100)
        evidence = [
            f"contracts_total={contracts_total}",
            f"at_risk_contracts={at_risk_contracts}",
            f"at_risk_ratio={at_risk_ratio:.2f}",
        ]
    return {"score": score, "status": _score_to_status(score), "evidence": evidence}


def _score_asset_conversion_health(asset_inventory_rows: list[dict] | None) -> dict[str, Any]:
    """Score asset conversion health from asset_inventory_items rows.

    Assets created by procurement delivery (PROC-* prefix) should be in
    'active' status. Constrained (maintenance/retired) items lower the score.
    """
    if asset_inventory_rows is None:
        return {
            "score": 50,
            "status": "watch",
            "evidence": ["asset_inventory_context_unavailable"],
        }
    proc_assets = [r for r in asset_inventory_rows if str(r.get("asset_code") or "").startswith("PROC-")]
    total = len(proc_assets)
    if total == 0:
        return {
            "score": 80,
            "status": "healthy",
            "evidence": ["no_procurement_assets_registered"],
        }
    constrained = sum(
        1 for r in proc_assets
        if str(r.get("status") or "").lower() in {"maintenance", "retired", "inactive"}
    )
    constrained_ratio = constrained / total
    score = _clamp(100.0 - constrained_ratio * 100)
    evidence = [
        f"procurement_assets_total={total}",
        f"constrained_assets={constrained}",
        f"constrained_ratio={constrained_ratio:.2f}",
    ]
    return {"score": score, "status": _score_to_status(score), "evidence": evidence}


def _score_risk_signal_health(active_risk_signals: int) -> dict[str, Any]:
    """Score risk signal health based on count of active finance/procurement risk signals."""
    score = _clamp(100.0 - active_risk_signals * 20)
    evidence = [f"active_finance_risk_signals={active_risk_signals}"]
    return {"score": score, "status": _score_to_status(score), "evidence": evidence}


# ──────────────────────────────────────────────────────────────────────────────
# Recommended actions builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_recommended_actions(dimensions: dict[str, dict]) -> list[dict]:
    actions: list[dict] = []

    budget = dimensions["budget_health"]
    if budget["status"] in ("risk", "critical"):
        actions.append({
            "type": "budget_review",
            "severity": "high" if budget["status"] == "critical" else "medium",
            "reason": "; ".join(budget["evidence"]),
            "source": "budget",
        })

    procurement = dimensions["procurement_health"]
    if procurement["status"] in ("risk", "critical", "watch"):
        severity = "high" if procurement["status"] in ("risk", "critical") else "low"
        actions.append({
            "type": "procurement_followup",
            "severity": severity,
            "reason": "; ".join(procurement["evidence"]),
            "source": "procurement",
        })

    po = dimensions["po_delivery_health"]
    if po["status"] in ("risk", "critical", "watch"):
        severity = "high" if po["status"] in ("risk", "critical") else "low"
        actions.append({
            "type": "po_delivery_followup",
            "severity": severity,
            "reason": "; ".join(po["evidence"]),
            "source": "po_delivery",
        })

    asset = dimensions["asset_conversion_health"]
    if asset["status"] in ("risk", "critical"):
        actions.append({
            "type": "asset_reconciliation",
            "severity": "high" if asset["status"] == "critical" else "medium",
            "reason": "; ".join(asset["evidence"]),
            "source": "asset",
        })

    risk_sig = dimensions["risk_signal_health"]
    if risk_sig["status"] in ("risk", "critical"):
        actions.append({
            "type": "risk_review",
            "severity": "high",
            "reason": "; ".join(risk_sig["evidence"]),
            "source": "risk_signal",
        })

    return actions


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

def compute_finance_operations_health(
    *,
    tenant_id: int,
    budget_context: dict[str, Any] | None = None,
    expense_context: dict[str, Any] | None = None,
    procurement_snapshot: dict[str, Any] | None = None,
    asset_inventory_rows: list[dict] | None = None,
    active_risk_signals: int = 0,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Compute deterministic Finance Operations Health decision.

    Parameters are injected (testable, no side-effects per call). All are
    optional except tenant_id — missing data produces neutral/unknown scores,
    not false green.

    Returns a Brain-Core-compatible decision dict with dimensions, score,
    risk_level, recommended_actions, and explanation.
    """
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id is required and must be > 0")

    # Procurement snapshot may come as a dict or pydantic model dump
    snap_dict: dict[str, Any] | None = None
    if procurement_snapshot is not None:
        if hasattr(procurement_snapshot, "model_dump"):
            snap_dict = procurement_snapshot.model_dump()
        elif hasattr(procurement_snapshot, "dict"):
            snap_dict = procurement_snapshot.dict()
        else:
            snap_dict = dict(procurement_snapshot)

    budget_dim = _score_budget_health(budget_context)
    procurement_dim = _score_procurement_health(snap_dict)
    po_delivery_dim = _score_po_delivery_health(snap_dict)
    asset_dim = _score_asset_conversion_health(asset_inventory_rows)
    risk_sig_dim = _score_risk_signal_health(active_risk_signals)

    dimensions = {
        "budget_health": budget_dim,
        "procurement_health": procurement_dim,
        "po_delivery_health": po_delivery_dim,
        "asset_conversion_health": asset_dim,
        "risk_signal_health": risk_sig_dim,
    }

    # Weighted average (budget and procurement are primary indicators)
    weights = {
        "budget_health": 0.30,
        "procurement_health": 0.25,
        "po_delivery_health": 0.20,
        "asset_conversion_health": 0.15,
        "risk_signal_health": 0.10,
    }
    overall_score = sum(
        dimensions[k]["score"] * w for k, w in weights.items()
    )
    overall_score = round(_clamp(overall_score), 2)
    risk_level = _overall_risk_level(overall_score)

    recommended_actions = _build_recommended_actions(dimensions)

    # Summary evidence for explanation
    statuses = {k: v["status"] for k, v in dimensions.items()}
    critical_dims = [k for k, s in statuses.items() if s == "critical"]
    risk_dims = [k for k, s in statuses.items() if s == "risk"]
    explanation_parts = [f"overall_score={overall_score}", f"risk_level={risk_level}"]
    if critical_dims:
        explanation_parts.append(f"critical_dimensions={critical_dims}")
    if risk_dims:
        explanation_parts.append(f"risk_dimensions={risk_dims}")
    if not critical_dims and not risk_dims:
        explanation_parts.append("finance_operations_health=acceptable")

    return {
        "tenant_id": tenant_id,
        "decision_type": "finance_operations_health",
        "scenario": "finance_operations_health",
        "overall_score": overall_score,
        "risk_level": risk_level,
        "dimensions": dimensions,
        "recommended_actions": recommended_actions,
        "explanation": "; ".join(explanation_parts),
        "correlation_id": correlation_id or str(uuid.uuid4()),
    }
