"""Academic Operations backend foundation permission constants."""

from __future__ import annotations

OVERVIEW_READ = "academic_operations.overview.read"
DASHBOARD_READ = "academic_operations.dashboard.read"
HEALTH_READ = "academic_operations.health.read"
AUDIT_READ = "academic_operations.audit.read"
EVIDENCE_READ = "academic_operations.evidence.read"
EVIDENCE_ATTACH = "academic_operations.evidence.attach"

ACADEMIC_GROUPS_READ = "academic_operations.academic_groups.read"
ACADEMIC_GROUPS_CREATE = "academic_operations.academic_groups.create"
ACADEMIC_GROUPS_UPDATE = "academic_operations.academic_groups.update"

COHORTS_READ = "academic_operations.cohorts.read"
COHORTS_CREATE = "academic_operations.cohorts.create"
COHORTS_UPDATE = "academic_operations.cohorts.update"

GRADEBOOK_METADATA_READ = "academic_operations.gradebook_metadata.read"
GRADEBOOK_METADATA_CREATE = "academic_operations.gradebook_metadata.create"
GRADEBOOK_METADATA_UPDATE = "academic_operations.gradebook_metadata.update"

RETAKE_MANAGEMENT_READ = "academic_operations.retake_management.read"
RETAKE_MANAGEMENT_CREATE = "academic_operations.retake_management.create"
RETAKE_MANAGEMENT_UPDATE = "academic_operations.retake_management.update"

SUMMER_SEMESTER_READ = "academic_operations.summer_semester.read"
SUMMER_SEMESTER_CREATE = "academic_operations.summer_semester.create"
SUMMER_SEMESTER_UPDATE = "academic_operations.summer_semester.update"

ADVISOR_TUTOR_READ = "academic_operations.advisor_tutor.read"
ADVISOR_TUTOR_CREATE = "academic_operations.advisor_tutor.create"
ADVISOR_TUTOR_UPDATE = "academic_operations.advisor_tutor.update"

CANONICAL_BRIDGE_READ = "academic_operations.canonical_bridge.read"
CANONICAL_BRIDGE_CREATE = "academic_operations.canonical_bridge.create"
CANONICAL_BRIDGE_UPDATE = "academic_operations.canonical_bridge.update"
STUDENT_LIFECYCLE_BRIDGE_READ = "academic_operations.student_lifecycle_bridge.read"
DOCUMENT_WORKFLOW_BRIDGE_READ = "academic_operations.document_workflow_bridge.read"
EXECUTIVE_GOVERNANCE_BRIDGE_READ = "academic_operations.executive_governance_bridge.read"
QUALITY_ACCREDITATION_BRIDGE_READ = "academic_operations.quality_accreditation_bridge.read"

COURSE_CATALOG_BRIDGE_READ = "academic_operations.course_catalog_bridge.read"
ELECTIVE_SELECTION_BRIDGE_READ = "academic_operations.elective_selection_bridge.read"
COMMITTEE_DECISION_BRIDGE_READ = "academic_operations.committee_decision_bridge.read"
PREREQUISITE_BRIDGE_READ = "academic_operations.prerequisite_bridge.read"
TEACHING_LOAD_BRIDGE_READ = "academic_operations.teaching_load_bridge.read"
THESIS_BRIDGE_READ = "academic_operations.thesis_bridge.read"
DEGREE_AUDIT_BRIDGE_READ = "academic_operations.degree_audit_bridge.read"

ADMIN_READ = "academic_operations.admin.read"
ADMIN_CONFIGURE = "academic_operations.admin.configure"

ALL_PERMISSIONS: frozenset[str] = frozenset({
    OVERVIEW_READ,
    DASHBOARD_READ,
    HEALTH_READ,
    AUDIT_READ,
    EVIDENCE_READ,
    EVIDENCE_ATTACH,
    ACADEMIC_GROUPS_READ,
    ACADEMIC_GROUPS_CREATE,
    ACADEMIC_GROUPS_UPDATE,
    COHORTS_READ,
    COHORTS_CREATE,
    COHORTS_UPDATE,
    GRADEBOOK_METADATA_READ,
    GRADEBOOK_METADATA_CREATE,
    GRADEBOOK_METADATA_UPDATE,
    RETAKE_MANAGEMENT_READ,
    RETAKE_MANAGEMENT_CREATE,
    RETAKE_MANAGEMENT_UPDATE,
    SUMMER_SEMESTER_READ,
    SUMMER_SEMESTER_CREATE,
    SUMMER_SEMESTER_UPDATE,
    ADVISOR_TUTOR_READ,
    ADVISOR_TUTOR_CREATE,
    ADVISOR_TUTOR_UPDATE,
    CANONICAL_BRIDGE_READ,
    CANONICAL_BRIDGE_CREATE,
    CANONICAL_BRIDGE_UPDATE,
    STUDENT_LIFECYCLE_BRIDGE_READ,
    DOCUMENT_WORKFLOW_BRIDGE_READ,
    EXECUTIVE_GOVERNANCE_BRIDGE_READ,
    QUALITY_ACCREDITATION_BRIDGE_READ,
    COURSE_CATALOG_BRIDGE_READ,
    ELECTIVE_SELECTION_BRIDGE_READ,
    COMMITTEE_DECISION_BRIDGE_READ,
    PREREQUISITE_BRIDGE_READ,
    TEACHING_LOAD_BRIDGE_READ,
    THESIS_BRIDGE_READ,
    DEGREE_AUDIT_BRIDGE_READ,
    ADMIN_READ,
    ADMIN_CONFIGURE,
})

ACADEMIC_OPERATIONS_PERMISSIONS = sorted(ALL_PERMISSIONS)