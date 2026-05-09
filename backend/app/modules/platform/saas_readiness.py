"""A-024.6 SaaS readiness consolidation contract.

Deterministic, tenant-safe, read-only consolidation for the 8 A-024 operational
backbone modules. This contract does not execute feature flags, billing plans,
runtime events, KPI writes, or Brain actions.
"""

from __future__ import annotations

from typing import Any


A024_OPERATIONAL_BACKBONE_MODULES: tuple[str, ...] = (
    "ai_routing_control",
    "platform_health",
    "ai_copilot_ops",
    "procurement_approval_workflow",
    "observability",
    "attendance",
    "student_portal",
    "university_core",
)

A024_MODULE_LEVELS: dict[str, int] = {
    "ai_routing_control": 3,
    "platform_health": 3,
    "ai_copilot_ops": 3,
    "procurement_approval_workflow": 3,
    "observability": 4,
    "attendance": 4,
    "student_portal": 4,
    "university_core": 4,
}

A024_VISIBLE_SURFACES: dict[str, str | None] = {
    "ai_routing_control": None,
    "platform_health": None,
    "ai_copilot_ops": None,
    "procurement_approval_workflow": None,
    "observability": "/api/admin/observability/summary",
    "attendance": "/api/admin/attendance/summary",
    "student_portal": "/api/admin/student-portal/summary",
    "university_core": "/api/admin/university-core/readiness",
}


SAAS_READINESS_MODULE_STATUSES: frozenset[str] = frozenset(
    {"ready", "partially_ready", "not_ready", "blocked", "unknown"}
)

SAAS_READINESS_DIMENSIONS: tuple[str, ...] = (
    "tenant_isolation",
    "visible_surface",
    "evidence_payload",
    "event_readiness",
    "kpi_readiness",
    "feature_flag_readiness",
    "billing_plan_readiness",
    "audit_readiness",
    "governance_readiness",
    "brain_signal_readiness",
)


def validate_saas_readiness_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted({str(item).strip() for item in values if str(item).strip()})


def _feature_flag_status_for_module(module: str) -> str:
    if module in {
        "observability",
        "attendance",
        "student_portal",
        "university_core",
        "ai_routing_control",
        "platform_health",
        "ai_copilot_ops",
        "procurement_approval_workflow",
    }:
        return "ready_for_mapping"
    return "unknown"


def _billing_plan_status_for_module(module: str) -> str:
    if module in {"procurement_approval_workflow", "ai_copilot_ops", "student_portal"}:
        return "ready_for_mapping"
    if module in {"observability", "platform_health", "ai_routing_control", "attendance", "university_core"}:
        return "deferred"
    return "unknown"


def _event_readiness_for_module(module: str) -> str:
    if module in {
        "ai_routing_control",
        "platform_health",
        "ai_copilot_ops",
        "procurement_approval_workflow",
    }:
        return "ready_for_mapping"
    if module in {"observability", "attendance", "student_portal", "university_core"}:
        return "partially_mapped"
    return "unknown"


def _kpi_readiness_for_module(module: str) -> str:
    if module == "observability":
        return "partially_mapped"
    if module in {"attendance", "student_portal", "university_core"}:
        return "ready_for_mapping"
    if module in {
        "ai_routing_control",
        "platform_health",
        "ai_copilot_ops",
        "procurement_approval_workflow",
    }:
        return "deferred"
    return "unknown"


def _governance_readiness_for_module(module: str, level: int) -> str:
    if level >= 4:
        return "ready_for_mapping"
    if level == 3:
        return "deferred"
    return "unknown"


def _brain_signal_readiness_for_module(module: str, level: int) -> str:
    if level == 4:
        return "ready_for_mapping"
    if level == 3:
        return "deferred"
    return "unknown"


def build_saas_readiness_module_summary(
    *,
    module: str,
    current_level: int,
    tenant_safe: bool,
    visible_surface: str | None,
    evidence_items: list[str],
    known_conditions: list[str],
) -> dict[str, Any]:
    if module not in A024_OPERATIONAL_BACKBONE_MODULES:
        raise ValueError("module is not in A-024 operational backbone")
    if current_level not in {3, 4}:
        raise ValueError("current_level must be 3 or 4 for A-024.6")

    event_readiness = _event_readiness_for_module(module)
    kpi_readiness = _kpi_readiness_for_module(module)
    feature_flag_readiness = _feature_flag_status_for_module(module)
    billing_plan_readiness = _billing_plan_status_for_module(module)
    governance_readiness = _governance_readiness_for_module(module, current_level)
    brain_signal_readiness = _brain_signal_readiness_for_module(module, current_level)

    ready_dimensions: list[str] = ["tenant_isolation", "evidence_payload", "audit_readiness"]
    deferred_dimensions: list[str] = []
    blockers: list[str] = []

    if visible_surface:
        ready_dimensions.append("visible_surface")
    else:
        deferred_dimensions.append("visible_surface")

    for dimension, state in (
        ("event_readiness", event_readiness),
        ("kpi_readiness", kpi_readiness),
        ("feature_flag_readiness", feature_flag_readiness),
        ("billing_plan_readiness", billing_plan_readiness),
        ("governance_readiness", governance_readiness),
        ("brain_signal_readiness", brain_signal_readiness),
    ):
        if state in {"supported", "mapped", "partially_mapped", "ready_for_mapping"}:
            if state == "ready_for_mapping":
                deferred_dimensions.append(dimension)
            else:
                ready_dimensions.append(dimension)
        elif state in {"deferred", "unknown"}:
            deferred_dimensions.append(dimension)
        elif state == "not_applicable":
            deferred_dimensions.append(dimension)
        else:
            blockers.append(f"{dimension}:{state}")

    readiness_status = "partially_ready"
    if tenant_safe and visible_surface and not blockers and current_level == 4:
        readiness_status = "ready"
    if not tenant_safe:
        readiness_status = "blocked"
        blockers.append("tenant_isolation")

    return {
        "module": module,
        "current_level": current_level,
        "readiness_status": readiness_status,
        "tenant_safe": tenant_safe,
        "visible_surface": visible_surface,
        "evidence_items": _sorted_unique(evidence_items),
        "ready_dimensions": _sorted_unique(ready_dimensions),
        "deferred_dimensions": _sorted_unique(deferred_dimensions),
        "blockers": _sorted_unique(blockers),
        "known_conditions": _sorted_unique(known_conditions),
        "feature_flag_status": feature_flag_readiness,
        "billing_plan_status": billing_plan_readiness,
        "event_readiness_status": event_readiness,
        "kpi_readiness_status": kpi_readiness,
        "governance_readiness_status": governance_readiness,
        "brain_signal_readiness_status": brain_signal_readiness,
        "no_fake_saas_claim": True,
        "no_fake_brain_claim": True,
        "no_full_production_claim": True,
    }


def classify_operational_backbone_status(
    *,
    ready_count: int,
    partially_ready_count: int,
    blocked_count: int,
    unknown_count: int,
) -> str:
    if blocked_count > 0:
        return "blocked"
    if ready_count == len(A024_OPERATIONAL_BACKBONE_MODULES):
        return "ready"
    if ready_count > 0 or partially_ready_count > 0:
        return "partially_ready"
    if unknown_count > 0:
        return "unknown"
    return "not_ready"


def build_a024_event_kpi_brain_mapping() -> list[dict[str, Any]]:
    mapping: list[dict[str, Any]] = []
    for module in A024_OPERATIONAL_BACKBONE_MODULES:
        level = A024_MODULE_LEVELS[module]
        mapping.append(
            {
                "module": module,
                "event_mapping_status": _event_readiness_for_module(module),
                "kpi_mapping_status": _kpi_readiness_for_module(module),
                "brain_mapping_status": _brain_signal_readiness_for_module(module, level),
                "decision": "readiness_mapping_only",
                "no_runtime_event_emission_added": True,
                "no_fake_kpi_values": True,
                "no_brain_autonomy_claim": True,
            }
        )
    return mapping


def build_a024_operational_backbone_summary(*, tenant_id: int) -> dict[str, Any]:
    validate_saas_readiness_tenant(tenant_id)

    module_summaries: list[dict[str, Any]] = []

    for module in A024_OPERATIONAL_BACKBONE_MODULES:
        current_level = A024_MODULE_LEVELS[module]
        visible_surface = A024_VISIBLE_SURFACES[module]
        known_conditions: list[str] = []

        evidence_items = [
            f"module:{module}",
            f"level:{current_level}",
            "tenant_fail_closed_contract",
            "deterministic_evidence_payload",
            "no_auto_action",
        ]

        if visible_surface:
            evidence_items.append(f"visible_surface:{visible_surface}")
        else:
            known_conditions.append("visible_surface_not_present_for_l3_module")

        if module == "university_core":
            known_conditions.append("known_table_coverage_condition_from_a0229")

        module_summaries.append(
            build_saas_readiness_module_summary(
                module=module,
                current_level=current_level,
                tenant_safe=True,
                visible_surface=visible_surface,
                evidence_items=evidence_items,
                known_conditions=known_conditions,
            )
        )

    ready_count = sum(1 for item in module_summaries if item["readiness_status"] == "ready")
    partially_ready_count = sum(
        1 for item in module_summaries if item["readiness_status"] == "partially_ready"
    )
    blocked_count = sum(1 for item in module_summaries if item["readiness_status"] == "blocked")
    unknown_count = sum(1 for item in module_summaries if item["readiness_status"] == "unknown")

    operational_backbone_status = classify_operational_backbone_status(
        ready_count=ready_count,
        partially_ready_count=partially_ready_count,
        blocked_count=blocked_count,
        unknown_count=unknown_count,
    )

    visible_surface_inventory = [
        {
            "module": module,
            "visible_surface": surface,
            "level": A024_MODULE_LEVELS[module],
        }
        for module, surface in A024_VISIBLE_SURFACES.items()
        if surface is not None
    ]

    deferred_work = [
        "event_registry_and_ingestion_wiring_for_a024_l3_modules",
        "kpi_lineage_mapping_for_all_a024_modules",
        "governance_dashboard_operational_readiness_panel_mapping",
        "feature_flag_policy_binding_without_fake_enforcement",
        "billing_plan_policy_binding_without_fake_enforcement",
        "brain_signal_mapping_readiness_without_autonomy_claim",
    ]

    known_conditions = [
        "a0246_is_consolidation_only_no_full_saas_production_claim",
        "a0246_no_level5_or_level6_claim",
        "university_core_table_coverage_known_condition_tracked",
        "event_kpi_brain_runtime_wiring_deferred_to_next_slice",
    ]

    return {
        "tenant_id": tenant_id,
        "total_modules_reviewed": len(A024_OPERATIONAL_BACKBONE_MODULES),
        "ready_count": ready_count,
        "partially_ready_count": partially_ready_count,
        "blocked_count": blocked_count,
        "unknown_count": unknown_count,
        "module_summaries": sorted(module_summaries, key=lambda item: str(item["module"])),
        "operational_backbone_status": operational_backbone_status,
        "visible_surface_inventory": sorted(
            visible_surface_inventory,
            key=lambda item: str(item["module"]),
        ),
        "event_kpi_brain_mapping": build_a024_event_kpi_brain_mapping(),
        "evidence_items": sorted(
            [
                "a024_operational_backbone_module_inventory",
                "tenant_safe_contract_review",
                "visible_surface_inventory_review",
                "feature_flag_billing_readiness_review",
                "event_kpi_brain_readiness_mapping",
            ]
        ),
        "deferred_work": deferred_work,
        "known_conditions": known_conditions,
        "module_count_expansion": 0,
        "baseline_total_target_modules": 150,
        "no_level5_or_level6_claim": True,
        "no_fake_kpi_values": True,
        "no_automatic_action": True,
        "no_db_mutation": True,
        "no_fake_saas_claim": True,
        "no_fake_brain_claim": True,
        "no_full_production_claim": True,
    }


__all__ = [
    "A024_OPERATIONAL_BACKBONE_MODULES",
    "A024_MODULE_LEVELS",
    "A024_VISIBLE_SURFACES",
    "SAAS_READINESS_MODULE_STATUSES",
    "SAAS_READINESS_DIMENSIONS",
    "validate_saas_readiness_tenant",
    "build_saas_readiness_module_summary",
    "classify_operational_backbone_status",
    "build_a024_event_kpi_brain_mapping",
    "build_a024_operational_backbone_summary",
]
