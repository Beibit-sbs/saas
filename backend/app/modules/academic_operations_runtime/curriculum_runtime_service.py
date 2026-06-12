"""Read-only Curriculum runtime service (A-052.7-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.curriculum_runtime_schemas import (
    CurriculumRuntimeHealth,
    CurriculumRuntimeOverview,
    CurriculumRuntimeReadiness,
    CurriculumRuntimeResponse,
    CurriculumRuntimeRisks,
    CurriculumRuntimeSection,
    CurriculumRuntimeStatistics,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _sum_status_counts(payload: dict[str, int]) -> int:
    return sum(int(v) for v in payload.values())


def _bridge_count(bridge_summary: dict[str, int], *tokens: str) -> int:
    lowered = tuple(token.lower() for token in tokens)
    total = 0
    for key, value in bridge_summary.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in lowered):
            total += int(value)
    return total


def get_curriculum_runtime(db: Session, tenant_id: int) -> CurriculumRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)
    course_registration_total = len(repository.list_course_registration_metadata(db, tenant))

    gradebook_total = _sum_status_counts(dashboard_summary["gradebook_metadata"])
    retake_total = _sum_status_counts(dashboard_summary["retake_plans"])
    terms_total = _sum_status_counts(dashboard_summary["summer_semester_terms"])

    program_structures_total = course_registration_total + gradebook_total
    curriculum_versions_total = max(course_registration_total, gradebook_total)
    academic_plans_total = retake_total + terms_total

    course_catalog_linkage_total = max(
        course_registration_total,
        _bridge_count(bridge_summary, "course_catalog", "catalog"),
    )
    prerequisite_chains_total = max(
        retake_total,
        _bridge_count(bridge_summary, "prerequisite", "prereq"),
    )
    learning_outcomes_total = max(
        gradebook_total,
        _bridge_count(
            bridge_summary,
            "learning_outcome",
            "course_learning_outcomes",
            "program_learning_outcomes",
            "outcome",
        ),
    )
    canonical_bridge_total = sum(int(v) for v in bridge_summary.values())

    consistency_score = min(
        100,
        program_structures_total * 3
        + curriculum_versions_total * 4
        + prerequisite_chains_total * 2
        + learning_outcomes_total * 2,
    )
    health_score = min(100, consistency_score + min(20, course_catalog_linkage_total))

    risk_indicators: list[str] = []
    if prerequisite_chains_total == 0:
        risk_indicators.append("missing_prerequisite_chain_visibility")
    if learning_outcomes_total == 0:
        risk_indicators.append("missing_learning_outcomes_visibility")
    if course_catalog_linkage_total == 0:
        risk_indicators.append("missing_course_catalog_linkage")

    open_risks = len(risk_indicators)
    risk_score = max(0, min(100, open_risks * 30 + max(0, 60 - consistency_score)))

    readiness_score = max(0, min(100, health_score - (open_risks * 10) + min(20, canonical_bridge_total)))

    return CurriculumRuntimeResponse(
        tenant_id=tenant,
        overview=CurriculumRuntimeOverview(generated_at=_now()),
        curriculum_statistics=CurriculumRuntimeStatistics(
            program_structures_total=program_structures_total,
            curriculum_versions_total=curriculum_versions_total,
            curriculum_health_score=health_score,
            course_catalog_linkage_total=course_catalog_linkage_total,
            prerequisite_chains_total=prerequisite_chains_total,
            learning_outcomes_total=learning_outcomes_total,
            academic_plans_total=academic_plans_total,
            canonical_bridge_total=canonical_bridge_total,
        ),
        program_structures=CurriculumRuntimeSection(
            records=program_structures_total,
            source_modules=["curriculum_management", "course_catalog_management"],
        ),
        curriculum_versions=CurriculumRuntimeSection(
            records=curriculum_versions_total,
            source_modules=["curriculum_management", "academic_operations"],
        ),
        curriculum_health=CurriculumRuntimeHealth(
            healthy=open_risks == 0,
            consistency_score=health_score,
            issues=risk_indicators,
        ),
        course_catalog_linkage=CurriculumRuntimeSection(
            records=course_catalog_linkage_total,
            source_modules=["course_catalog_management", "curriculum_management"],
        ),
        prerequisite_chains=CurriculumRuntimeSection(
            records=prerequisite_chains_total,
            source_modules=["prerequisite_management", "course_catalog_management"],
        ),
        learning_outcomes_summary=CurriculumRuntimeSection(
            records=learning_outcomes_total,
            source_modules=["course_learning_outcomes", "program_learning_outcomes"],
        ),
        curriculum_risks=CurriculumRuntimeRisks(
            risk_score=risk_score,
            open_risks=open_risks,
            indicators=risk_indicators,
        ),
        curriculum_readiness=CurriculumRuntimeReadiness(
            ready_for_runtime=open_risks == 0,
            checklist=[
                "read_only_runtime",
                "aggregator_only_runtime",
                "tenant_scoped_visibility",
                "summary_read_rbac_required",
                "no_mutation_operations",
            ],
            readiness_score=readiness_score,
        ),
    )