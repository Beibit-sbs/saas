from __future__ import annotations

import hashlib
from typing import Any

from app.modules.brain_core.schemas import BrainSignalCandidateSummarySchema
from app.platform.kpi import service as kpi_service

ALLOWED_SIGNAL_TYPES: frozenset[str] = frozenset(
    {"risk", "drift", "gap", "anomaly", "readiness", "compliance", "cost", "quality"}
)
ALLOWED_SEVERITIES: frozenset[str] = frozenset({"info", "watch", "review_required", "high", "critical"})
ALLOWED_CONFIDENCE_LEVELS: frozenset[str] = frozenset({"high", "medium", "low", "unknown"})
ALLOWED_ACTION_TYPES: frozenset[str] = frozenset({"read_only", "draft_recommendation", "human_review_queue"})
FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "auto_execute",
    "auto_enforce",
    "auto_penalize",
    "auto_pay",
    "auto_approve",
    "auto_reject",
    "auto_block_access",
    "auto_remediate",
)

DOMAIN_SIGNAL_MAP: dict[str, dict[str, str]] = {
    "academic-governance": {"signal_type": "quality", "review_role": "rector_reviewer"},
    "finance-procurement-assets": {"signal_type": "cost", "review_role": "finance_reviewer"},
    "campus-operations": {"signal_type": "readiness", "review_role": "platform_ops_reviewer"},
    "security-visitor-operations": {"signal_type": "risk", "review_role": "security_reviewer"},
    "room-allocation-scheduling-intelligence": {"signal_type": "readiness", "review_role": "scheduling_reviewer"},
    "brain-review-required": {"signal_type": "compliance", "review_role": "brain_governance_reviewer"},
    "student-risk-interventions": {"signal_type": "risk", "review_role": "student_success_reviewer"},
    "research-accreditation-quality": {"signal_type": "gap", "review_role": "research_governance_reviewer"},
}

DOMAIN_ALIAS_MAP: dict[str, str] = {
    "academic_quality": "academic-governance",
    "student_outcomes": "student-risk-interventions",
    "research_output": "research-accreditation-quality",
    "financial_health": "finance-procurement-assets",
    "faculty_engagement": "brain-review-required",
    "digital_infrastructure": "campus-operations",
    "compliance_governance": "brain-review-required",
    "enrollment_pipeline": "student-risk-interventions",
}


def validate_brain_signal_tenant(tenant_id: int) -> int:
    normalized = int(tenant_id)
    if normalized <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return normalized


def classify_signal_type_for_domain(domain_key: str) -> str:
    normalized = str(domain_key).strip().lower()
    normalized = DOMAIN_ALIAS_MAP.get(normalized, normalized)
    mapping = DOMAIN_SIGNAL_MAP.get(normalized)
    if mapping is None:
        raise ValueError(f"unknown rector KPI drilldown domain: {domain_key!r}")
    signal_type = mapping["signal_type"]
    if signal_type not in ALLOWED_SIGNAL_TYPES:
        raise ValueError(f"unsupported signal type: {signal_type!r}")
    return signal_type


def classify_signal_severity(*, drilldown: dict[str, Any], available_count: int, total_count: int) -> str:
    risk_level = str(drilldown.get("risk_level") or "").strip().lower()
    review_required = bool(drilldown.get("review_required", False))

    if risk_level == "critical":
        severity = "critical"
    elif risk_level == "high":
        severity = "high"
    elif risk_level in {"medium", "review_required"} or review_required:
        severity = "review_required"
    elif risk_level == "low":
        severity = "watch"
    elif risk_level == "unavailable":
        severity = "info"
    else:
        severity = "info"

    if total_count > 0 and available_count == 0:
        return "info"
    if total_count > 0 and available_count < total_count and severity in {"review_required", "high", "critical"}:
        return "review_required"
    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(f"unsupported severity: {severity!r}")
    return severity


def classify_signal_confidence(*, available_count: int, total_count: int, severity: str) -> str:
    normalized_severity = str(severity).strip().lower()
    if total_count <= 0 or available_count <= 0:
        return "unknown"
    if available_count < total_count:
        return "low"
    if normalized_severity in {"review_required", "high", "critical"}:
        return "high"
    if normalized_severity in {"info", "watch"}:
        return "medium"
    return "low"


def build_brain_signal_candidate(*, tenant_id: int, drilldown: dict[str, Any]) -> dict[str, Any]:
    normalized_tenant_id = validate_brain_signal_tenant(tenant_id)
    domain_key = str(drilldown.get("domain_id") or "").strip().lower()
    normalized_domain_key = DOMAIN_ALIAS_MAP.get(domain_key, domain_key)
    mapping = DOMAIN_SIGNAL_MAP.get(normalized_domain_key)
    if mapping is None:
        raise ValueError(f"unknown rector KPI drilldown domain: {domain_key!r}")

    evidence_sources = list(drilldown.get("evidence_sources") or [])
    source_metrics = [str(metric).strip() for metric in list(drilldown.get("source_metrics") or []) if str(metric).strip()]
    available_sources = [source for source in evidence_sources if bool(source.get("available", False))]
    available_count = len(available_sources)
    total_count = len(evidence_sources)

    severity = classify_signal_severity(
        drilldown=drilldown,
        available_count=available_count,
        total_count=total_count,
    )
    confidence_level = classify_signal_confidence(
        available_count=available_count,
        total_count=total_count,
        severity=severity,
    )
    signal_type = classify_signal_type_for_domain(domain_key)
    recommended_review_role = mapping["review_role"]
    human_approval_required = severity in {"review_required", "high", "critical"}
    allowed_action_type = "human_review_queue" if human_approval_required else "draft_recommendation" if severity == "watch" else "read_only"

    if allowed_action_type not in ALLOWED_ACTION_TYPES:
        raise ValueError(f"unsupported allowed_action_type: {allowed_action_type!r}")

    evidence_refs: list[dict[str, Any]] = [
        {
            "ref_type": "rector_kpi_drilldown",
            "ref_id": f"rector-kpi-drilldown:{normalized_domain_key}",
            "description": f"Rector KPI drilldown for {normalized_domain_key}",
        },
    ]
    for source in available_sources:
        metric_key = str(source.get("metric_key") or "").strip()
        if metric_key:
            evidence_refs.append(
                {
                    "ref_type": "kpi_metric",
                    "ref_id": metric_key,
                    "description": str(source.get("label") or metric_key),
                }
            )

    rationale = (
        f"{drilldown.get('evidence_summary') or 'No drilldown evidence available.'} "
        "Candidate generated from Rector KPI drilldown evidence only."
    )
    kpi_refs = source_metrics
    signal_id_input = "|".join(
        [
            str(normalized_tenant_id),
            domain_key,
            signal_type,
            severity,
            confidence_level,
            allowed_action_type,
            ",".join(sorted(evidence_ref["ref_id"] for evidence_ref in evidence_refs)),
            ",".join(sorted(kpi_refs)),
            recommended_review_role,
        ]
    )
    digest = hashlib.sha256(signal_id_input.encode("utf-8")).hexdigest()[:16]

    candidate = {
        "signal_id": f"brain-signal-candidate-{normalized_domain_key}-{normalized_tenant_id}-{digest}",
        "signal_type": signal_type,
        "source_domain": normalized_domain_key,
        "tenant_id": normalized_tenant_id,
        "evidence_refs": evidence_refs,
        "kpi_refs": kpi_refs,
        "confidence_level": confidence_level,
        "rationale": rationale,
        "severity": severity,
        "recommended_review_role": recommended_review_role,
        "allowed_action_type": allowed_action_type,
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "human_approval_required": human_approval_required,
        "generated_from_evidence": True,
        "read_only": True,
        "tenant_scoped": True,
        "no_autonomous_execution": True,
        "no_policy_enforcement": True,
        "no_remediation_action": True,
        "no_fake_signal": True,
    }
    return candidate


def build_brain_signal_candidate_summary(*, tenant_id: int, signals: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_tenant_id = validate_brain_signal_tenant(tenant_id)
    summary = {
        "tenant_id": normalized_tenant_id,
        "source": "rector_kpi_drilldown",
        "signals": signals,
        "total_signals": len(signals),
        "review_required_count": sum(
            1 for signal in signals if str(signal.get("severity") or "").strip().lower() in {"review_required", "high", "critical"}
        ),
        "high_priority_count": sum(
            1 for signal in signals if str(signal.get("severity") or "").strip().lower() in {"high", "critical"}
        ),
        "source_domains": sorted({str(signal.get("source_domain") or "").strip() for signal in signals if str(signal.get("source_domain") or "").strip()}),
        "generated_from_existing_drilldowns": True,
        "generated_from_evidence": True,
        "read_only": True,
        "tenant_scoped": True,
        "no_autonomous_action": True,
        "no_policy_enforcement": True,
        "no_remediation_action": True,
        "no_fake_signal": True,
        "no_fake_kpi": True,
        "no_fake_event": True,
    }
    validated = BrainSignalCandidateSummarySchema.model_validate(summary)
    return validated.model_dump()


def map_rector_kpi_drilldown_to_brain_signal_candidates(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    normalized_tenant_id = validate_brain_signal_tenant(tenant_id)
    rector_kpi_drilldown = kpi_service.get_rector_kpi_drilldown(tenant_id=normalized_tenant_id, uow=uow)
    domains = list(rector_kpi_drilldown.get("domains") or [])

    signals = [build_brain_signal_candidate(tenant_id=normalized_tenant_id, drilldown=domain) for domain in domains]
    return build_brain_signal_candidate_summary(tenant_id=normalized_tenant_id, signals=signals)