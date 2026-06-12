"""Read-only runtime shell service for Academic Operations (A-052.5-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.runtime_shell_schemas import (
    AcademicOperationsRuntimeShellResponse,
    AcademicOperationsRuntimeShellSafety,
    AcademicOperationsRuntimeShellSection,
)


REQUIRED_LIMITATIONS = [
    "read_only_runtime",
    "aggregator_only_runtime",
    "tenant_scoped_visibility",
    "summary_read_rbac_required",
    "no_workflow_execution",
    "no_approval_execution",
    "no_background_jobs",
    "no_provider_mutation",
]


def _now() -> datetime:
    return datetime.now(UTC)


def get_runtime_shell(db: Session, tenant_id: int) -> AcademicOperationsRuntimeShellResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)

    groups_total = sum(dashboard_summary["academic_groups"].values())
    cohorts_total = sum(dashboard_summary["cohorts"].values())
    gradebook_total = sum(dashboard_summary["gradebook_metadata"].values())
    retake_total = sum(dashboard_summary["retake_plans"].values())
    summer_total = sum(dashboard_summary["summer_semester_terms"].values())
    advisor_total = sum(dashboard_summary["advisor_tutor_assignments"].values())
    bridges_total = sum(bridge_summary.values())

    summary_records = groups_total + cohorts_total + gradebook_total + retake_total + summer_total + advisor_total
    domain_records = groups_total + cohorts_total + retake_total + summer_total
    runtime_records = summary_records + bridges_total
    integration_records = bridges_total
    readiness_records = int(summary_records > 0) + int(integration_records >= 0)

    return AcademicOperationsRuntimeShellResponse(
        tenant_id=tenant,
        generated_at=_now(),
        runtime_shell_summary=AcademicOperationsRuntimeShellSection(
            owner_module="academic_operations",
            records=summary_records,
            source_modules=["academic_operations"],
        ),
        runtime_shell_domain=AcademicOperationsRuntimeShellSection(
            owner_module="academic_operations",
            records=domain_records,
            source_modules=[
                "academic_operations",
                "course_catalog_management",
                "prerequisite_management",
                "teaching_load_contracts",
            ],
        ),
        runtime_shell_runtime=AcademicOperationsRuntimeShellSection(
            owner_module="academic_operations_runtime",
            records=runtime_records,
            source_modules=["academic_operations", "scheduling", "grades", "exam_governance", "internship"],
        ),
        runtime_shell_integration=AcademicOperationsRuntimeShellSection(
            owner_module="academic_operations_runtime",
            records=integration_records,
            source_modules=["student_information_system_integration", "learning_management_system_integration"],
        ),
        runtime_shell_readiness=AcademicOperationsRuntimeShellSection(
            owner_module="academic_operations_runtime",
            records=readiness_records,
            source_modules=["academic_operations_runtime"],
        ),
        safety=AcademicOperationsRuntimeShellSafety(
            limitations=list(REQUIRED_LIMITATIONS),
        ),
    )
