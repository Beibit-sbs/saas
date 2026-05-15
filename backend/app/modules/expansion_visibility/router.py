from collections import Counter
from typing import Annotated, Any, Callable

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.accreditation_dashboard.service import get_accreditation_dashboard_l4_visibility_summary
from app.modules.archive_retention_management.service import get_archive_retention_management_l4_visibility_summary
from app.modules.committee_decision_registry.service import get_committee_decision_registry_l4_visibility_summary
from app.modules.compliance_calendar_dashboard.service import get_compliance_calendar_dashboard_l4_visibility_summary
from app.modules.document_template_library.service import get_document_template_library_l4_visibility_summary
from app.modules.document_workflow.service import get_document_workflow_l4_visibility_summary
from app.modules.incoming_outgoing_correspondence.service import get_incoming_outgoing_correspondence_l4_visibility_summary
from app.modules.international_office.service import get_international_office_l4_visibility_summary
from app.modules.ministry_reporting_dashboard.service import get_ministry_reporting_dashboard_l4_visibility_summary
from app.modules.order_decree_registry.service import get_order_decree_registry_l4_visibility_summary
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rector_strategy_dashboard.service import get_rector_strategy_dashboard_l4_visibility_summary
from app.modules.rector_resolution_tracking_workflow.service import (
    get_rector_resolution_tracking_workflow_l4_visibility_summary,
)
from app.modules.curriculum_mapping.service import get_curriculum_mapping_l4_visibility_summary
from app.modules.syllabus_management.service import get_syllabus_management_l4_visibility_summary
from app.modules.competency_framework.service import get_competency_framework_l4_visibility_summary
from app.modules.program_learning_outcomes.service import get_program_learning_outcomes_l4_visibility_summary
from app.modules.course_learning_outcomes.service import get_course_learning_outcomes_l4_visibility_summary
from app.modules.elective_course_selection.service import get_elective_course_selection_l4_visibility_summary
from app.modules.prerequisite_management.service import get_prerequisite_management_l4_visibility_summary
from app.modules.transfer_credit_management.service import get_transfer_credit_management_l4_visibility_summary
from app.modules.course_catalog_management.service import get_course_catalog_management_l4_visibility_summary
from app.modules.degree_audit.service import get_degree_audit_l4_visibility_summary
from app.modules.staff_recruitment.service import get_staff_recruitment_l4_visibility_summary
from app.modules.staff_onboarding.service import get_staff_onboarding_l4_visibility_summary
from app.modules.employee_records.service import get_employee_records_l4_visibility_summary
from app.modules.leave_management.service import get_leave_management_l4_visibility_summary
from app.modules.dormitory_management.service import get_dormitory_management_l4_visibility_summary
from app.modules.partnership_registry.service import get_partnership_registry_l4_visibility_summary
from app.modules.mou_lifecycle.service import get_mou_lifecycle_l4_visibility_summary
from app.modules.scholarship_committee_workflow.service import get_scholarship_committee_workflow_l4_visibility_summary
from app.modules.student_appeals_workflow.service import get_student_appeals_workflow_l4_visibility_summary
from app.modules.consent_management_policy.service import get_consent_management_policy_l4_visibility_summary
from app.modules.timesheet_management.service import get_timesheet_management_l4_visibility_summary
from app.modules.faculty_attestation.service import get_faculty_attestation_l4_visibility_summary
from app.modules.teaching_load_contracts.service import get_teaching_load_contracts_l4_visibility_summary
from app.modules.staff_exit_offboarding.service import get_staff_exit_offboarding_l4_visibility_summary
from app.modules.thesis_dissertation_management.service import get_thesis_dissertation_management_l4_visibility_summary
from app.modules.joint_program_management.service import get_joint_program_management_l4_visibility_summary
from app.modules.inbound_exchange_management.service import get_inbound_exchange_management_l4_visibility_summary
from app.modules.outbound_exchange_management.service import get_outbound_exchange_management_l4_visibility_summary


router = APIRouter(prefix="/api/admin/expansion/l4", tags=["expansion-l4-visibility"])

Actor = Annotated[str, Depends(get_actor)]
TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
ExpansionRead = Annotated[None, Depends(permission_dependency("admin.expansion.read"))]
SummaryBuilder = Callable[[int], dict[str, Any]]


CONSOLIDATED_SOURCE_ACTIONS = [
    "A-028.1", "A-028.2", "A-028.3",
    "A-028.6", "A-028.7", "A-028.8",
    "A-028.9", "A-028.10", "A-028.11",
]
CONSOLIDATED_MODULE_CATALOG: list[dict[str, Any]] = [
    {
        "uce_id": "UCE-009",
        "module": "document_workflow",
        "domain": "Document Workflow",
        "builder": get_document_workflow_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-011",
        "module": "order_decree_registry",
        "domain": "Governance / Document",
        "builder": get_order_decree_registry_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-013",
        "module": "incoming_outgoing_correspondence",
        "domain": "Communications",
        "builder": get_incoming_outgoing_correspondence_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-089",
        "module": "document_template_library",
        "domain": "Document Workflow",
        "builder": get_document_template_library_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-090",
        "module": "committee_decision_registry",
        "domain": "Governance",
        "builder": get_committee_decision_registry_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-099",
        "module": "rector_resolution_tracking_workflow",
        "domain": "Governance",
        "builder": get_rector_resolution_tracking_workflow_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-122",
        "module": "compliance_calendar_dashboard",
        "domain": "Legal / Audit",
        "builder": get_compliance_calendar_dashboard_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-114",
        "module": "accreditation_dashboard",
        "domain": "Accreditation",
        "builder": get_accreditation_dashboard_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-032",
        "module": "ministry_reporting_dashboard",
        "domain": "Regulatory Reporting",
        "builder": get_ministry_reporting_dashboard_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-031",
        "module": "rector_strategy_dashboard",
        "domain": "Governance / Rectorate",
        "builder": get_rector_strategy_dashboard_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-012",
        "module": "archive_retention_management",
        "domain": "Library / Archive",
        "builder": get_archive_retention_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-019",
        "module": "international_office",
        "domain": "International Office",
        "builder": get_international_office_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-014",
        "module": "curriculum_mapping",
        "domain": "Academic / Curriculum",
        "builder": get_curriculum_mapping_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-015",
        "module": "syllabus_management",
        "domain": "Academic / Curriculum",
        "builder": get_syllabus_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-016",
        "module": "competency_framework",
        "domain": "Academic / Competencies",
        "builder": get_competency_framework_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-071",
        "module": "program_learning_outcomes",
        "domain": "Academic / Outcomes",
        "builder": get_program_learning_outcomes_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-072",
        "module": "course_learning_outcomes",
        "domain": "Academic / Outcomes",
        "builder": get_course_learning_outcomes_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-073",
        "module": "elective_course_selection",
        "domain": "Academic / Enrollment",
        "builder": get_elective_course_selection_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-074",
        "module": "prerequisite_management",
        "domain": "Academic / Prerequisites",
        "builder": get_prerequisite_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-075",
        "module": "transfer_credit_management",
        "domain": "Academic / Transfer",
        "builder": get_transfer_credit_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-076",
        "module": "course_catalog_management",
        "domain": "Academic / Catalog",
        "builder": get_course_catalog_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-092",
        "module": "degree_audit",
        "domain": "Academic / Audit",
        "builder": get_degree_audit_l4_visibility_summary,
    },
    # Wave 3 — A-028.9/A-028.10 candidates (added in A-028.11-RUNTIME)
    {
        "uce_id": "UCE-001",
        "module": "staff_recruitment",
        "domain": "HR / Recruitment",
        "builder": get_staff_recruitment_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-002",
        "module": "staff_onboarding",
        "domain": "HR / Onboarding",
        "builder": get_staff_onboarding_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-003",
        "module": "employee_records",
        "domain": "HR / Records",
        "builder": get_employee_records_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-004",
        "module": "leave_management",
        "domain": "HR / Leave",
        "builder": get_leave_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-017",
        "module": "dormitory_management",
        "domain": "Campus Operations / Dormitory",
        "builder": get_dormitory_management_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-022",
        "module": "partnership_registry",
        "domain": "International Office / Partnerships",
        "builder": get_partnership_registry_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-023",
        "module": "mou_lifecycle",
        "domain": "International Office / Partnerships",
        "builder": get_mou_lifecycle_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-037",
        "module": "scholarship_committee_workflow",
        "domain": "Student Lifecycle / Scholarships",
        "builder": get_scholarship_committee_workflow_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-038",
        "module": "student_appeals_workflow",
        "domain": "Student Lifecycle / Appeals",
        "builder": get_student_appeals_workflow_l4_visibility_summary,
    },
    {
        "uce_id": "UCE-046",
        "module": "consent_management_policy",
        "domain": "Legal / Compliance",
        "builder": get_consent_management_policy_l4_visibility_summary,
    },
]


def _build_summary_response(tenant: dict[str, object], builder: SummaryBuilder) -> dict[str, Any]:
    return builder(int(tenant["id"]))


def _aggregate_modules_by_domain() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for item in CONSOLIDATED_MODULE_CATALOG:
        grouped.setdefault(str(item["domain"]), []).append(str(item["module"]))
    return grouped


def _aggregate_status_counts(modules: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for module in modules:
        status = module.get("readiness_summary", {}).get("status")
        if isinstance(status, str) and status.strip():
            counts[status] += 1
        else:
            counts["UNKNOWN_OR_NOT_REPORTED"] += 1
    return dict(counts)


def _aggregate_risk_counts(modules: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for module in modules:
        risk = module.get("risk_summary", {}).get("risk_band")
        if isinstance(risk, str) and risk.strip():
            counts[risk] += 1
        else:
            counts["UNKNOWN_OR_NOT_REPORTED"] += 1
    return dict(counts)


def _aggregate_missing_evidence(modules: list[dict[str, Any]]) -> dict[str, Any]:
    unique_items: list[str] = []
    seen: set[str] = set()
    total_missing_entries = 0

    for module in modules:
        summary = module.get("missing_evidence_summary")
        # Handle both dict format (with "items" key) and list format
        if isinstance(summary, dict):
            items = summary.get("items", [])
        elif isinstance(summary, list):
            items = summary
        else:
            items = []
            
        if isinstance(items, list):
            total_missing_entries += len(items)
            for item in items:
                if isinstance(item, str) and item not in seen:
                    seen.add(item)
                    unique_items.append(item)

    return {
        "total_missing_entries": total_missing_entries,
        "unique_missing_evidence_items": unique_items,
        "unique_missing_evidence_count": len(unique_items),
    }


def _aggregate_human_review_rollup(modules: list[dict[str, Any]]) -> dict[str, int]:
    rollup = {
        "candidate_count": 0,
        "ready_for_human_review_count": 0,
        "pending_manual_evidence_count": 0,
        "blocked_count": 0,
        "modules_requiring_human_review_count": 0,
    }
    for module in modules:
        queue = module.get("human_review_queue_summary")
        # Handle both dict format and string format
        if isinstance(queue, dict):
            rollup["candidate_count"] += int(queue.get("candidate_count", 0) or 0)
            rollup["ready_for_human_review_count"] += int(queue.get("ready_for_human_review_count", 0) or 0)
            rollup["pending_manual_evidence_count"] += int(queue.get("pending_manual_evidence_count", 0) or 0)
            rollup["blocked_count"] += int(queue.get("blocked_count", 0) or 0)
        elif isinstance(queue, str) and queue:
            # String format means there's a review item present
            rollup["modules_requiring_human_review_count"] += 1
            
        if module.get("human_review_required") is True:
            rollup["modules_requiring_human_review_count"] += 1
    return rollup


def _aggregate_forbidden_actions(modules: list[dict[str, Any]]) -> list[str]:
    merged: set[str] = set()
    for module in modules:
        actions = module.get("forbidden_actions", [])
        if isinstance(actions, list):
            merged.update(action for action in actions if isinstance(action, str))
    return sorted(merged)


def _build_consolidated_summary(tenant_id: int) -> dict[str, Any]:
    module_summaries: list[dict[str, Any]] = []
    for item in CONSOLIDATED_MODULE_CATALOG:
        module_summaries.append(item["builder"](tenant_id))

    return {
        "tenant_id": tenant_id,
        "visibility_level": "L4",
        "summary_type": "EXPANSION_L4_CONSOLIDATED_ADMIN_SUMMARY",
        "coverage_version": "A-028.11",
        "source_actions": list(CONSOLIDATED_SOURCE_ACTIONS),
        "total_l4_visibility_candidates": len(CONSOLIDATED_MODULE_CATALOG),
        "total_api_routed_candidates": len(CONSOLIDATED_MODULE_CATALOG),
        "total_consolidated_candidates": len(CONSOLIDATED_MODULE_CATALOG),
        "modules": module_summaries,
        "modules_by_domain": _aggregate_modules_by_domain(),
        "readiness_status_counts": _aggregate_status_counts(module_summaries),
        "risk_band_counts": _aggregate_risk_counts(module_summaries),
        "missing_evidence_rollup": _aggregate_missing_evidence(module_summaries),
        "human_review_queue_rollup": _aggregate_human_review_rollup(module_summaries),
        "forbidden_actions_rollup": _aggregate_forbidden_actions(module_summaries),
        "safety_flags": {
            "read_only": True,
            "no_db_mutation": True,
            "no_provider_call": True,
            "no_external_submission": True,
            "no_brain_execution": True,
            "no_autonomous_execution": True,
            "no_workflow_execution": True,
            "no_decision_execution": True,
            "no_fake_kpi": True,
            "no_synthetic_dashboard": True,
            "no_synthetic_score": True,
            "no_ranking": True,
            "tenant_safe_visibility": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
        "read_only": True,
        "no_mutation": True,
        "no_fake_kpi": True,
        "no_synthetic_dashboard": True,
        "no_synthetic_score": True,
        "no_ranking": True,
        "no_provider_call": True,
        "no_external_submission": True,
        "no_brain_execution": True,
        "no_autonomous_execution": True,
        "no_workflow_execution": True,
        "no_decision_execution": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
    }


@router.get("/document-workflow/summary")
def get_document_workflow_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_document_workflow_l4_visibility_summary)


@router.get("/order-decree-registry/summary")
def get_order_decree_registry_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_order_decree_registry_l4_visibility_summary)


@router.get("/committee-decision-registry/summary")
def get_committee_decision_registry_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_committee_decision_registry_l4_visibility_summary)


@router.get("/rector-resolution-tracking-workflow/summary")
def get_rector_resolution_tracking_workflow_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_rector_resolution_tracking_workflow_l4_visibility_summary)


@router.get("/compliance-calendar-dashboard/summary")
def get_compliance_calendar_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_compliance_calendar_dashboard_l4_visibility_summary)


@router.get("/accreditation-dashboard/summary")
def get_accreditation_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_accreditation_dashboard_l4_visibility_summary)


@router.get("/incoming-outgoing-correspondence/summary")
def get_incoming_outgoing_correspondence_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_incoming_outgoing_correspondence_l4_visibility_summary)


@router.get("/document-template-library/summary")
def get_document_template_library_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_document_template_library_l4_visibility_summary)


@router.get("/ministry-reporting-dashboard/summary")
def get_ministry_reporting_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_ministry_reporting_dashboard_l4_visibility_summary)


@router.get("/rector-strategy-dashboard/summary")
def get_rector_strategy_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_rector_strategy_dashboard_l4_visibility_summary)


@router.get("/archive-retention-management/summary")
def get_archive_retention_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_archive_retention_management_l4_visibility_summary)


@router.get("/international-office/summary")
def get_international_office_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_international_office_l4_visibility_summary)


@router.get("/curriculum-mapping/summary")
def get_curriculum_mapping_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_curriculum_mapping_l4_visibility_summary)


@router.get("/syllabus-management/summary")
def get_syllabus_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_syllabus_management_l4_visibility_summary)


@router.get("/competency-framework/summary")
def get_competency_framework_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_competency_framework_l4_visibility_summary)


@router.get("/program-learning-outcomes/summary")
def get_program_learning_outcomes_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_program_learning_outcomes_l4_visibility_summary)


@router.get("/course-learning-outcomes/summary")
def get_course_learning_outcomes_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_course_learning_outcomes_l4_visibility_summary)


@router.get("/elective-course-selection/summary")
def get_elective_course_selection_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_elective_course_selection_l4_visibility_summary)


@router.get("/prerequisite-management/summary")
def get_prerequisite_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_prerequisite_management_l4_visibility_summary)


@router.get("/transfer-credit-management/summary")
def get_transfer_credit_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_transfer_credit_management_l4_visibility_summary)


@router.get("/course-catalog-management/summary")
def get_course_catalog_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_course_catalog_management_l4_visibility_summary)


@router.get("/degree-audit/summary")
def get_degree_audit_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_degree_audit_l4_visibility_summary)


@router.get("/staff-recruitment/summary")
def get_staff_recruitment_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_staff_recruitment_l4_visibility_summary)


@router.get("/staff-onboarding/summary")
def get_staff_onboarding_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_staff_onboarding_l4_visibility_summary)


@router.get("/employee-records/summary")
def get_employee_records_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_employee_records_l4_visibility_summary)


@router.get("/leave-management/summary")
def get_leave_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_leave_management_l4_visibility_summary)


@router.get("/dormitory-management/summary")
def get_dormitory_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_dormitory_management_l4_visibility_summary)


@router.get("/partnership-registry/summary")
def get_partnership_registry_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_partnership_registry_l4_visibility_summary)


@router.get("/mou-lifecycle/summary")
def get_mou_lifecycle_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_mou_lifecycle_l4_visibility_summary)


@router.get("/scholarship-committee-workflow/summary")
def get_scholarship_committee_workflow_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_scholarship_committee_workflow_l4_visibility_summary)


@router.get("/student-appeals-workflow/summary")
def get_student_appeals_workflow_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_student_appeals_workflow_l4_visibility_summary)


@router.get("/consent-management-policy/summary")
def get_consent_management_policy_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_consent_management_policy_l4_visibility_summary)


# A-028.14 — Expansion L4 API Routes Batch 5 (UCE-060, 061, 067, 070, 077, 085, 086, 087)
# Read-only GET wrappers over A-028.13 L4 service summaries.
# Consolidated summary refresh deferred to A-028.15.

@router.get("/timesheet-management/summary")
def get_timesheet_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_timesheet_management_l4_visibility_summary)


@router.get("/faculty-attestation/summary")
def get_faculty_attestation_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_faculty_attestation_l4_visibility_summary)


@router.get("/teaching-load-contracts/summary")
def get_teaching_load_contracts_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_teaching_load_contracts_l4_visibility_summary)


@router.get("/staff-exit-offboarding/summary")
def get_staff_exit_offboarding_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_staff_exit_offboarding_l4_visibility_summary)


@router.get("/thesis-dissertation-management/summary")
def get_thesis_dissertation_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_thesis_dissertation_management_l4_visibility_summary)


@router.get("/joint-program-management/summary")
def get_joint_program_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_joint_program_management_l4_visibility_summary)


@router.get("/inbound-exchange-management/summary")
def get_inbound_exchange_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_inbound_exchange_management_l4_visibility_summary)


@router.get("/outbound-exchange-management/summary")
def get_outbound_exchange_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_outbound_exchange_management_l4_visibility_summary)


@router.get("/summary", include_in_schema=False)
def get_expansion_l4_consolidated_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_consolidated_summary(int(tenant["id"]))