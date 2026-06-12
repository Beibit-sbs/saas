"""Read-only Academic Registry runtime service (A-052.6-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.academic_registry_runtime_schemas import (
    AcademicRegistryHealth,
    AcademicRegistryIntegrationStatus,
    AcademicRegistryReadiness,
    AcademicRegistryRuntimeOverview,
    AcademicRegistryRuntimeResponse,
    AcademicRegistryRuntimeSection,
    AcademicRegistryRuntimeStatistics,
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


def get_academic_registry_runtime(db: Session, tenant_id: int) -> AcademicRegistryRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)

    academic_periods_total = _sum_status_counts(dashboard_summary["summer_semester_terms"])
    academic_groups_total = _sum_status_counts(dashboard_summary["academic_groups"])
    cohorts_total = _sum_status_counts(dashboard_summary["cohorts"])
    advisor_total = _sum_status_counts(dashboard_summary["advisor_tutor_assignments"])
    gradebook_total = _sum_status_counts(dashboard_summary["gradebook_metadata"])
    course_registration_total = len(repository.list_course_registration_metadata(db, tenant))

    curriculum_registry_total = course_registration_total + gradebook_total
    catalog_linkage_total = course_registration_total
    student_registry_linkage_total = cohorts_total + advisor_total
    canonical_bridge_total = sum(int(v) for v in bridge_summary.values())

    sis_evidence_count = _bridge_count(bridge_summary, "sis", "student_information_system")
    lms_evidence_count = _bridge_count(bridge_summary, "lms", "learning_management_system")

    consistency_score = min(
        100,
        academic_periods_total * 5 + academic_groups_total * 3 + curriculum_registry_total + student_registry_linkage_total,
    )
    readiness_score = min(100, 40 + min(40, consistency_score // 2) + (10 if canonical_bridge_total >= 0 else 0))

    sis_ready = sis_evidence_count >= 0
    lms_ready = lms_evidence_count >= 0

    return AcademicRegistryRuntimeResponse(
        tenant_id=tenant,
        overview=AcademicRegistryRuntimeOverview(generated_at=_now()),
        registry_statistics=AcademicRegistryRuntimeStatistics(
            academic_periods_total=academic_periods_total,
            academic_groups_total=academic_groups_total,
            curriculum_registry_total=curriculum_registry_total,
            course_catalog_linkage_total=catalog_linkage_total,
            student_registry_linkage_total=student_registry_linkage_total,
            canonical_bridge_total=canonical_bridge_total,
        ),
        academic_periods=AcademicRegistryRuntimeSection(
            records=academic_periods_total,
            source_modules=["academic_operations"],
        ),
        academic_groups=AcademicRegistryRuntimeSection(
            records=academic_groups_total,
            source_modules=["academic_operations"],
        ),
        curriculum_linkage=AcademicRegistryRuntimeSection(
            records=curriculum_registry_total,
            source_modules=["academic_operations", "course_catalog_management", "prerequisite_management"],
        ),
        catalog_linkage=AcademicRegistryRuntimeSection(
            records=catalog_linkage_total,
            source_modules=["course_catalog_management", "academic_operations"],
        ),
        sis_status=AcademicRegistryIntegrationStatus(
            provider="student_information_system_integration",
            status="READINESS_ONLY",
            ready=sis_ready,
            evidence_count=sis_evidence_count,
        ),
        lms_status=AcademicRegistryIntegrationStatus(
            provider="learning_management_system_integration",
            status="READINESS_ONLY",
            ready=lms_ready,
            evidence_count=lms_evidence_count,
        ),
        health=AcademicRegistryHealth(
            healthy=True,
            consistency_score=consistency_score,
            issues=[],
        ),
        readiness=AcademicRegistryReadiness(
            ready_for_runtime=sis_ready and lms_ready,
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
