// Permission constants matching backend RBAC definitions

export const PERMISSIONS = {
  // Tenant management
  TENANTS_READ: "admin.tenants.read",
  TENANTS_WRITE: "admin.tenants.write",

  // Feature flags (backend guards both read and write with admin.integrations.manage)
  FEATURE_FLAGS_READ: "admin.integrations.manage",
  FEATURE_FLAGS_WRITE: "admin.integrations.manage",

  // Billing (platform billing routes are under router_admin, guarded by platform.admin.read/write)
  BILLING_READ: "platform.admin.read",
  BILLING_WRITE: "platform.admin.write",

  // Jobs
  JOBS_READ: "admin.jobs.read",
  JOBS_WRITE: "admin.jobs.write",

  // Notifications (under platform admin router, guarded by platform.admin.read/write)
  NOTIFICATIONS_READ: "platform.admin.read",
  NOTIFICATIONS_WRITE: "platform.admin.write",

  // Health / metrics
  HEALTH_READ: "health.read",
  METRICS_READ: "metrics.read",

  // Platform Ops Console
  OPS_READ: "ops.read",
  OPS_WRITE: "ops.write",

  // RBAC
  RBAC_READ: "admin.roles.manage",
  RBAC_WRITE: "admin.roles.manage",
  ROLES_MANAGE: "admin.roles.manage",

  // Local Users
  LOCAL_USERS_MANAGE: "admin.users.manage",

  // Org Units
  ORG_UNITS_READ: "admin.org_units.read",
  ORG_UNITS_WRITE: "admin.org_units.write",

  // Integrations / Service Accounts
  INTEGRATIONS_MANAGE: "admin.integrations.manage",

  // Programs
  PROGRAMS_READ: "admin.programs.read",
  PROGRAMS_WRITE: "admin.programs.write",

  // Courses
  COURSES_READ: "admin.courses.read",
  COURSES_WRITE: "admin.courses.write",

  // Faculty
  FACULTY_READ: "admin.faculty.read",
  FACULTY_WRITE: "admin.faculty.write",

  // HR / Payroll (Phase X)
  HR_READ: "hr.read",
  HR_WRITE: "hr.write",

  // Finance / Collections (Phase X)
  FINANCE_READ: "finance.read",
  FINANCE_WRITE: "finance.write",

  // Backups
  BACKUP_MANAGE: "admin.backup.manage",

  // Academic records
  RECORDS_READ: "admin.records.read",
  RECORDS_WRITE: "admin.records.write",
  ACADEMIC_RECORDS_READ: "admin.records.read",
  ACADEMIC_RECORDS_WRITE: "admin.records.write",

  // i18n
  I18N_MANAGE: "admin.i18n.manage",

  // Workflows
  WORKFLOWS_READ: "workflows.read",
  WORKFLOWS_WRITE: "workflows.write",

  // Profiles
  PROFILES_READ: "profiles.read",
  PROFILES_WRITE: "profiles.write",

  // Dashboard
  DASHBOARD_READ: "admin.dashboard.read",

  // Audit
  AUDIT_READ: "admin.audit.read",

  // Students
  STUDENTS_READ: "students.read",
  STUDENTS_WRITE: "students.write",

  // Enrollments
  ENROLLMENTS_READ: "enrollments.read",
  ENROLLMENTS_WRITE: "enrollments.write",

  // Grades
  GRADES_READ: "grades.read",
  GRADES_WRITE: "grades.write",

  // Transcripts
  TRANSCRIPTS_READ: "transcripts.read",
  TRANSCRIPTS_WRITE: "transcripts.write",

  // Scheduling
  SCHEDULING_READ: "scheduling.read",
  SCHEDULING_WRITE: "scheduling.write",

  // Advising & Mentoring
  ADVISING_READ: "advising.read",
  ADVISING_WRITE: "advising.write",

  // Student Services Ticketing
  STUDENT_SERVICES_READ: "student_services.read",
  STUDENT_SERVICES_WRITE: "student_services.write",

  // Student Life (counseling, wellbeing, accessibility, disciplinary)
  STUDENT_LIFE_READ: "student_life.read",
  STUDENT_LIFE_WRITE: "student_life.write",

  // Career Services & Employability
  CAREER_SERVICES_READ: "career_services.read",
  CAREER_SERVICES_WRITE: "career_services.write",

  // Scholarship & Financial Aid
  FINANCIAL_AID_READ: "financial_aid.read",
  FINANCIAL_AID_WRITE: "financial_aid.write",

  // Dormitory & Housing
  HOUSING_READ: "housing.read",
  HOUSING_WRITE: "housing.write",

  // Alumni lifecycle
  ALUMNI_READ: "alumni.read",
  ALUMNI_WRITE: "alumni.write",

  // Degree progress
  DEGREE_PROGRESS_READ: "degree_progress.read",

  // Admissions
  ADMISSIONS_READ: "admissions.read",
  ADMISSIONS_WRITE: "admissions.write",
  ADMISSIONS_DECIDE: "admissions.decide",
  ADMISSIONS_DOCUMENTS_WRITE: "admissions.documents.write",

  // Automation / Workflow Engine (routes under platform admin router, guarded by platform.admin.read/write)
  AUTOMATION_READ: "platform.admin.read",
  AUTOMATION_WRITE: "platform.admin.write",

  // AI Copilot (read-only foundation v1)
  AI_COPILOT_READ: "ai.chat.execute",

  // AI Gateway (model / provider management)
  AI_PROVIDERS_MANAGE: "admin.ai.providers.manage",
  AI_MODELS_MANAGE: "admin.ai.models.manage",

  // Federation Layer v1 (currently served under platform admin router, guarded by platform.admin.read/write)
  FEDERATION_READ: "platform.admin.read",
  FEDERATION_WRITE: "platform.admin.write",

  // Developer Platform v1
  DEVELOPER_PLATFORM_READ: "platform.admin.read",
  DEVELOPER_PLATFORM_WRITE: "platform.admin.write",

  // Interventions
  INTERVENTIONS_VIEW: "interventions:view",
  INTERVENTIONS_MANAGE_PLAYBOOKS: "interventions:manage_playbooks",
  INTERVENTIONS_EXECUTE_PLAYBOOK: "interventions:execute_playbook",

  // Research Contour (grants, publications, labs, projects)
  RESEARCH_READ: "research.read",
  RESEARCH_WRITE: "research.write",

  // Facilities & Work Orders (Phase XI)
  FACILITIES_READ: "facilities.read",
  FACILITIES_WRITE: "facilities.write",

  // Asset Inventory (Phase XI)
  ASSET_INVENTORY_READ: "asset_inventory.read",
  ASSET_INVENTORY_WRITE: "asset_inventory.write",

  // Faculty Copilot (Phase XII)
  FACULTY_COPILOT_READ: "faculty_copilot.read",
  FACULTY_COPILOT_WRITE: "faculty_copilot.write",

  // Knowledge Retrieval (Phase XII2)
  KNOWLEDGE_RETRIEVAL_READ: "knowledge_retrieval.read",
  KNOWLEDGE_RETRIEVAL_WRITE: "knowledge_retrieval.write",

  // Prompt Management (Phase XII3)
  PROMPT_MANAGEMENT_READ: "prompt_management.read",
  PROMPT_MANAGEMENT_WRITE: "prompt_management.write",

  // Model Evaluation (Phase XII4)
  MODEL_EVALUATION_READ: "model_evaluation.read",
  MODEL_EVALUATION_WRITE: "model_evaluation.write",

  // Rector Assignments (Wave 20 / A-031.1)
  RECTOR_ASSIGNMENTS_DASHBOARD_READ: "admin.rector_assignments.dashboard.read",
  RECTOR_ASSIGNMENTS_LIST: "admin.rector_assignments.read",
  RECTOR_ASSIGNMENTS_LIST_ALL: "admin.rector_assignments.read_all",
  RECTOR_ASSIGNMENTS_LIST_DEPARTMENT: "admin.rector_assignments.read_department",
  RECTOR_ASSIGNMENTS_CREATE: "admin.rector_assignments.create",
  RECTOR_ASSIGNMENTS_ASSIGN: "admin.rector_assignments.assign",
  RECTOR_ASSIGNMENTS_ACCEPT: "admin.rector_assignments.accept",
  RECTOR_ASSIGNMENTS_RETURN: "admin.rector_assignments.return",
  RECTOR_ASSIGNMENTS_COMPLETE: "admin.rector_assignments.complete",
  RECTOR_ASSIGNMENTS_ESCALATE: "admin.rector_assignments.escalate",
  RECTOR_ASSIGNMENTS_CANCEL: "admin.rector_assignments.cancel",
  RECTOR_ASSIGNMENTS_ARCHIVE: "admin.rector_assignments.archive",
  RECTOR_ASSIGNMENTS_STATUS_CHANGE: "admin.rector_assignments.status.change",
  RECTOR_ASSIGNMENTS_REPORT_SUBMIT: "admin.rector_assignments.report.submit",
  RECTOR_ASSIGNMENTS_REPORT_REVIEW: "admin.rector_assignments.report.review",
  RECTOR_ASSIGNMENTS_EVIDENCE_ATTACH: "admin.rector_assignments.evidence.attach",
  RECTOR_ASSIGNMENTS_COMMENT: "admin.rector_assignments.comment",
  RECTOR_ASSIGNMENTS_AUDIT_READ: "admin.rector_assignments.audit.read",
  RECTOR_ASSIGNMENTS_TEMPLATES_MANAGE: "admin.rector_assignments.templates.manage",
  // A-031.5 expansion permissions
  RECTOR_ASSIGNMENTS_OUTBOX_READ: "admin.rector_assignments.outbox.read",
  RECTOR_ASSIGNMENTS_OUTBOX_MANAGE: "admin.rector_assignments.outbox.manage",
  RECTOR_ASSIGNMENTS_SLA_MANAGE: "admin.rector_assignments.sla.manage",
  RECTOR_ASSIGNMENTS_ESCALATION_POLICY_MANAGE: "admin.rector_assignments.escalation_policy.manage",

  // Document Workflow OS (Wave 21 / A-032.2)
  DOCUMENTS_DASHBOARD_READ: "admin.documents.dashboard.read",
  DOCUMENTS_ADMIN: "admin.documents.admin",
  DOCUMENTS_READ: "admin.documents.read",
  DOCUMENTS_CREATE: "admin.documents.create",
  DOCUMENTS_UPDATE: "admin.documents.update",
  DOCUMENTS_REGISTER: "admin.documents.register",
  DOCUMENTS_REVIEW: "admin.documents.review",
  DOCUMENTS_APPROVE: "admin.documents.approve",
  DOCUMENTS_SIGNED_METADATA_RECORD: "admin.documents.signed_metadata.record",
  DOCUMENTS_ARCHIVE: "admin.documents.archive",
  DOCUMENTS_AUDIT_READ: "admin.documents.audit.read",
  DOCUMENTS_LINK_ASSIGNMENT: "admin.documents.link_assignment",
  DECREES_READ: "admin.decrees.read",
  DECREES_CREATE: "admin.decrees.create",
  DECREES_UPDATE: "admin.decrees.update",
  DECREES_LEGAL_REVIEW: "admin.decrees.legal_review",
  DECREES_APPROVE_SIGNING: "admin.decrees.approve_signing",
  DECREES_SIGNED_METADATA_RECORD: "admin.decrees.signed_metadata.record",
  DECREES_REGISTER: "admin.decrees.register",
  DECREES_ARCHIVE: "admin.decrees.archive",
  CORRESPONDENCE_READ: "admin.correspondence.read",
  CORRESPONDENCE_CREATE: "admin.correspondence.create",
  CORRESPONDENCE_REGISTER: "admin.correspondence.register",
  CORRESPONDENCE_ROUTE: "admin.correspondence.route",
  CORRESPONDENCE_SENT_METADATA_RECORD: "admin.correspondence.sent_metadata.record",
  CORRESPONDENCE_ARCHIVE: "admin.correspondence.archive",
  RESOLUTIONS_CREATE: "admin.resolutions.create",
  RESOLUTIONS_LINK_ASSIGNMENT: "admin.resolutions.link_assignment",

  // Student Lifecycle Suite (Wave 24 / A-035.3)
  STUDENT_LIFECYCLE_APPLICANTS_READ: "student_lifecycle.applicants.read",
  STUDENT_LIFECYCLE_APPLICANTS_CREATE: "student_lifecycle.applicants.create",
  STUDENT_LIFECYCLE_APPLICANTS_UPDATE: "student_lifecycle.applicants.update",
  STUDENT_LIFECYCLE_APPLICANTS_STATUS_UPDATE: "student_lifecycle.applicants.status.update",
  STUDENT_LIFECYCLE_STUDENTS_READ: "student_lifecycle.students.read",
  STUDENT_LIFECYCLE_STUDENTS_CREATE: "student_lifecycle.students.create",
  STUDENT_LIFECYCLE_STUDENTS_UPDATE: "student_lifecycle.students.update",
  STUDENT_LIFECYCLE_STUDENTS_STATUS_UPDATE: "student_lifecycle.students.status.update",
  STUDENT_LIFECYCLE_ENROLLMENT_READ: "student_lifecycle.enrollment.read",
  STUDENT_LIFECYCLE_ENROLLMENT_CREATE: "student_lifecycle.enrollment.create",
  STUDENT_LIFECYCLE_ENROLLMENT_UPDATE: "student_lifecycle.enrollment.update",
  STUDENT_LIFECYCLE_ENROLLMENT_REVIEW: "student_lifecycle.enrollment.review",
  STUDENT_LIFECYCLE_RECORDS_READ: "student_lifecycle.records.read",
  STUDENT_LIFECYCLE_RECORDS_CREATE: "student_lifecycle.records.create",
  STUDENT_LIFECYCLE_RECORDS_RESULT_METADATA_WRITE: "student_lifecycle.records.result_metadata.write",
  STUDENT_LIFECYCLE_TRANSCRIPTS_READ: "student_lifecycle.transcripts.read",
  STUDENT_LIFECYCLE_TRANSCRIPTS_PREVIEW: "student_lifecycle.transcripts.preview",
  STUDENT_LIFECYCLE_DEGREE_PROGRESS_READ: "student_lifecycle.degree_progress.read",
  STUDENT_LIFECYCLE_DEGREE_PROGRESS_COMPUTE: "student_lifecycle.degree_progress.compute",
  STUDENT_LIFECYCLE_GRADUATION_READINESS_REVIEW: "student_lifecycle.graduation_readiness.review",
  STUDENT_LIFECYCLE_REQUESTS_READ: "student_lifecycle.requests.read",
  STUDENT_LIFECYCLE_REQUESTS_CREATE: "student_lifecycle.requests.create",
  STUDENT_LIFECYCLE_REQUESTS_REVIEW: "student_lifecycle.requests.review",
  STUDENT_LIFECYCLE_APPEALS_READ: "student_lifecycle.appeals.read",
  STUDENT_LIFECYCLE_APPEALS_CREATE: "student_lifecycle.appeals.create",
  STUDENT_LIFECYCLE_APPEALS_REVIEW: "student_lifecycle.appeals.review",
  STUDENT_LIFECYCLE_INTERVENTIONS_READ: "student_lifecycle.interventions.read",
  STUDENT_LIFECYCLE_INTERVENTIONS_SIGNAL_CREATE: "student_lifecycle.interventions.signal.create",
  STUDENT_LIFECYCLE_INTERVENTIONS_PLAN_CREATE: "student_lifecycle.interventions.plan.create",
  STUDENT_LIFECYCLE_INTERVENTIONS_FOLLOWUP_WRITE: "student_lifecycle.interventions.followup.write",
  STUDENT_LIFECYCLE_AUDIT_READ: "student_lifecycle.audit.read",
  STUDENT_LIFECYCLE_EVIDENCE_READ: "student_lifecycle.evidence.read",
  STUDENT_LIFECYCLE_EVIDENCE_ATTACH: "student_lifecycle.evidence.attach",
  STUDENT_LIFECYCLE_DASHBOARD_READ: "student_lifecycle.dashboard.read",
  STUDENT_LIFECYCLE_HEALTH_READ: "student_lifecycle.health.read",
  STUDENT_LIFECYCLE_ADMIN_READ: "student_lifecycle.admin.read",

  // Academic Operations Suite (Wave 25 / A-036.3)
  ACADEMIC_OPERATIONS_OVERVIEW_READ: "academic_operations.overview.read",
  ACADEMIC_OPERATIONS_DASHBOARD_READ: "academic_operations.dashboard.read",
  ACADEMIC_OPERATIONS_HEALTH_READ: "academic_operations.health.read",
  ACADEMIC_OPERATIONS_AUDIT_READ: "academic_operations.audit.read",
  ACADEMIC_OPERATIONS_EVIDENCE_READ: "academic_operations.evidence.read",
  ACADEMIC_OPERATIONS_EVIDENCE_ATTACH: "academic_operations.evidence.attach",
  ACADEMIC_OPERATIONS_ACADEMIC_GROUPS_READ: "academic_operations.academic_groups.read",
  ACADEMIC_OPERATIONS_ACADEMIC_GROUPS_CREATE: "academic_operations.academic_groups.create",
  ACADEMIC_OPERATIONS_ACADEMIC_GROUPS_UPDATE: "academic_operations.academic_groups.update",
  ACADEMIC_OPERATIONS_COHORTS_READ: "academic_operations.cohorts.read",
  ACADEMIC_OPERATIONS_COHORTS_CREATE: "academic_operations.cohorts.create",
  ACADEMIC_OPERATIONS_COHORTS_UPDATE: "academic_operations.cohorts.update",
  ACADEMIC_OPERATIONS_GRADEBOOK_METADATA_READ: "academic_operations.gradebook_metadata.read",
  ACADEMIC_OPERATIONS_GRADEBOOK_METADATA_CREATE: "academic_operations.gradebook_metadata.create",
  ACADEMIC_OPERATIONS_GRADEBOOK_METADATA_UPDATE: "academic_operations.gradebook_metadata.update",
  ACADEMIC_OPERATIONS_RETAKE_MANAGEMENT_READ: "academic_operations.retake_management.read",
  ACADEMIC_OPERATIONS_RETAKE_MANAGEMENT_CREATE: "academic_operations.retake_management.create",
  ACADEMIC_OPERATIONS_RETAKE_MANAGEMENT_UPDATE: "academic_operations.retake_management.update",
  ACADEMIC_OPERATIONS_SUMMER_SEMESTER_READ: "academic_operations.summer_semester.read",
  ACADEMIC_OPERATIONS_SUMMER_SEMESTER_CREATE: "academic_operations.summer_semester.create",
  ACADEMIC_OPERATIONS_SUMMER_SEMESTER_UPDATE: "academic_operations.summer_semester.update",
  ACADEMIC_OPERATIONS_ADVISOR_TUTOR_READ: "academic_operations.advisor_tutor.read",
  ACADEMIC_OPERATIONS_ADVISOR_TUTOR_CREATE: "academic_operations.advisor_tutor.create",
  ACADEMIC_OPERATIONS_ADVISOR_TUTOR_UPDATE: "academic_operations.advisor_tutor.update",
  ACADEMIC_OPERATIONS_CANONICAL_BRIDGE_READ: "academic_operations.canonical_bridge.read",
  ACADEMIC_OPERATIONS_CANONICAL_BRIDGE_CREATE: "academic_operations.canonical_bridge.create",
  ACADEMIC_OPERATIONS_CANONICAL_BRIDGE_UPDATE: "academic_operations.canonical_bridge.update",
  ACADEMIC_OPERATIONS_STUDENT_LIFECYCLE_BRIDGE_READ: "academic_operations.student_lifecycle_bridge.read",
  ACADEMIC_OPERATIONS_DOCUMENT_WORKFLOW_BRIDGE_READ: "academic_operations.document_workflow_bridge.read",
  ACADEMIC_OPERATIONS_EXECUTIVE_GOVERNANCE_BRIDGE_READ: "academic_operations.executive_governance_bridge.read",
  ACADEMIC_OPERATIONS_QUALITY_ACCREDITATION_BRIDGE_READ: "academic_operations.quality_accreditation_bridge.read",
  ACADEMIC_OPERATIONS_COURSE_CATALOG_BRIDGE_READ: "academic_operations.course_catalog_bridge.read",
  ACADEMIC_OPERATIONS_ELECTIVE_SELECTION_BRIDGE_READ: "academic_operations.elective_selection_bridge.read",
  ACADEMIC_OPERATIONS_COMMITTEE_DECISION_BRIDGE_READ: "academic_operations.committee_decision_bridge.read",
  ACADEMIC_OPERATIONS_PREREQUISITE_BRIDGE_READ: "academic_operations.prerequisite_bridge.read",
  ACADEMIC_OPERATIONS_TEACHING_LOAD_BRIDGE_READ: "academic_operations.teaching_load_bridge.read",
  ACADEMIC_OPERATIONS_THESIS_BRIDGE_READ: "academic_operations.thesis_bridge.read",
  ACADEMIC_OPERATIONS_DEGREE_AUDIT_BRIDGE_READ: "academic_operations.degree_audit_bridge.read",
  ACADEMIC_OPERATIONS_ADMIN_READ: "academic_operations.admin.read",
  ACADEMIC_OPERATIONS_ADMIN_CONFIGURE: "academic_operations.admin.configure",

  // Research / Science Suite (Wave 26 / A-037.3)
  RESEARCH_SCIENCE_OVERVIEW_READ: "research_science.overview.read",
  RESEARCH_SCIENCE_DASHBOARD_READ: "research_science.dashboard.read",
  RESEARCH_SCIENCE_HEALTH_READ: "research_science.health.read",
  RESEARCH_SCIENCE_MATRIX_READ: "research_science.matrix.read",
  RESEARCH_SCIENCE_LIMITATIONS_READ: "research_science.limitations.read",
  RESEARCH_SCIENCE_PROJECTS_READ: "research_science.projects.read",
  RESEARCH_SCIENCE_PROJECTS_CREATE: "research_science.projects.create",
  RESEARCH_SCIENCE_PROJECTS_UPDATE: "research_science.projects.update",
  RESEARCH_SCIENCE_STUDENT_RESEARCH_READ: "research_science.student_research.read",
  RESEARCH_SCIENCE_STUDENT_RESEARCH_CREATE: "research_science.student_research.create",
  RESEARCH_SCIENCE_STUDENT_RESEARCH_UPDATE: "research_science.student_research.update",
  RESEARCH_SCIENCE_SUPERVISION_READ: "research_science.supervision.read",
  RESEARCH_SCIENCE_SUPERVISION_CREATE: "research_science.supervision.create",
  RESEARCH_SCIENCE_SUPERVISION_UPDATE: "research_science.supervision.update",
  RESEARCH_SCIENCE_PUBLICATIONS_READ: "research_science.publications.read",
  RESEARCH_SCIENCE_PUBLICATIONS_CREATE: "research_science.publications.create",
  RESEARCH_SCIENCE_PUBLICATIONS_UPDATE: "research_science.publications.update",
  RESEARCH_SCIENCE_CONFERENCES_READ: "research_science.conferences.read",
  RESEARCH_SCIENCE_CONFERENCES_CREATE: "research_science.conferences.create",
  RESEARCH_SCIENCE_CONFERENCES_UPDATE: "research_science.conferences.update",
  RESEARCH_SCIENCE_GRANTS_READ: "research_science.grants.read",
  RESEARCH_SCIENCE_GRANTS_CREATE: "research_science.grants.create",
  RESEARCH_SCIENCE_GRANTS_UPDATE: "research_science.grants.update",
  RESEARCH_SCIENCE_GRANT_DELIVERABLES_READ: "research_science.grant_deliverables.read",
  RESEARCH_SCIENCE_GRANT_DELIVERABLES_CREATE: "research_science.grant_deliverables.create",
  RESEARCH_SCIENCE_GRANT_DELIVERABLES_UPDATE: "research_science.grant_deliverables.update",
  RESEARCH_SCIENCE_ETHICS_READ: "research_science.ethics.read",
  RESEARCH_SCIENCE_ETHICS_CREATE: "research_science.ethics.create",
  RESEARCH_SCIENCE_ETHICS_UPDATE: "research_science.ethics.update",
  RESEARCH_SCIENCE_ETHICS_AMENDMENTS_READ: "research_science.ethics_amendments.read",
  RESEARCH_SCIENCE_ETHICS_AMENDMENTS_CREATE: "research_science.ethics_amendments.create",
  RESEARCH_SCIENCE_ETHICS_AMENDMENTS_UPDATE: "research_science.ethics_amendments.update",
  RESEARCH_SCIENCE_EVIDENCE_READ: "research_science.evidence.read",
  RESEARCH_SCIENCE_EVIDENCE_ATTACH: "research_science.evidence.attach",
  RESEARCH_SCIENCE_AUDIT_READ: "research_science.audit.read",
  RESEARCH_SCIENCE_BRIDGES_READ: "research_science.bridges.read",
  RESEARCH_SCIENCE_BRIDGES_CREATE: "research_science.bridges.create",
  RESEARCH_SCIENCE_BRIDGES_UPDATE: "research_science.bridges.update",
  RESEARCH_SCIENCE_ADMIN_READ: "research_science.admin.read",
  RESEARCH_SCIENCE_ADMIN_CONFIGURE: "research_science.admin.configure",

  // Quality / Accreditation Suite (Wave 27 / A-038.3)
  QUALITY_ACCREDITATION_OVERVIEW_READ: "quality_accreditation.overview.read",
  QUALITY_ACCREDITATION_DASHBOARD_READ: "quality_accreditation.dashboard.read",
  QUALITY_ACCREDITATION_HEALTH_READ: "quality_accreditation.health.read",
  QUALITY_ACCREDITATION_MATRIX_READ: "quality_accreditation.matrix.read",
  QUALITY_ACCREDITATION_LIMITATIONS_READ: "quality_accreditation.limitations.read",
  QUALITY_ACCREDITATION_STANDARDS_READ: "quality_accreditation.standards.read",
  QUALITY_ACCREDITATION_STANDARDS_CREATE: "quality_accreditation.standards.create",
  QUALITY_ACCREDITATION_STANDARDS_UPDATE: "quality_accreditation.standards.update",
  QUALITY_ACCREDITATION_CRITERIA_READ: "quality_accreditation.criteria.read",
  QUALITY_ACCREDITATION_CRITERIA_CREATE: "quality_accreditation.criteria.create",
  QUALITY_ACCREDITATION_CRITERIA_UPDATE: "quality_accreditation.criteria.update",
  QUALITY_ACCREDITATION_EVIDENCE_READ: "quality_accreditation.evidence.read",
  QUALITY_ACCREDITATION_EVIDENCE_ATTACH: "quality_accreditation.evidence.attach",
  QUALITY_ACCREDITATION_EVIDENCE_REVIEW: "quality_accreditation.evidence.review",
  QUALITY_ACCREDITATION_EVIDENCE_LIMITATIONS_MANAGE: "quality_accreditation.evidence.limitations.manage",
  QUALITY_ACCREDITATION_PROGRAM_READINESS_READ: "quality_accreditation.program_readiness.read",
  QUALITY_ACCREDITATION_PROGRAM_READINESS_UPDATE: "quality_accreditation.program_readiness.update",
  QUALITY_ACCREDITATION_INSTITUTIONAL_READINESS_READ: "quality_accreditation.institutional_readiness.read",
  QUALITY_ACCREDITATION_INSTITUTIONAL_READINESS_UPDATE: "quality_accreditation.institutional_readiness.update",
  QUALITY_ACCREDITATION_SELF_ASSESSMENT_READ: "quality_accreditation.self_assessment.read",
  QUALITY_ACCREDITATION_SELF_ASSESSMENT_CREATE: "quality_accreditation.self_assessment.create",
  QUALITY_ACCREDITATION_SELF_ASSESSMENT_UPDATE: "quality_accreditation.self_assessment.update",
  QUALITY_ACCREDITATION_IMPROVEMENT_PLANS_READ: "quality_accreditation.improvement_plans.read",
  QUALITY_ACCREDITATION_IMPROVEMENT_PLANS_CREATE: "quality_accreditation.improvement_plans.create",
  QUALITY_ACCREDITATION_IMPROVEMENT_PLANS_UPDATE: "quality_accreditation.improvement_plans.update",
  QUALITY_ACCREDITATION_INTERNAL_AUDITS_READ: "quality_accreditation.internal_audits.read",
  QUALITY_ACCREDITATION_INTERNAL_AUDITS_CREATE: "quality_accreditation.internal_audits.create",
  QUALITY_ACCREDITATION_INTERNAL_AUDITS_UPDATE: "quality_accreditation.internal_audits.update",
  QUALITY_ACCREDITATION_AUDIT_FINDINGS_READ: "quality_accreditation.audit_findings.read",
  QUALITY_ACCREDITATION_AUDIT_FINDINGS_UPDATE: "quality_accreditation.audit_findings.update",
  QUALITY_ACCREDITATION_PROGRAM_REVIEW_READ: "quality_accreditation.program_review.read",
  QUALITY_ACCREDITATION_PROGRAM_REVIEW_CREATE: "quality_accreditation.program_review.create",
  QUALITY_ACCREDITATION_PROGRAM_REVIEW_UPDATE: "quality_accreditation.program_review.update",
  QUALITY_ACCREDITATION_LEARNING_OUTCOMES_READ: "quality_accreditation.learning_outcomes.read",
  QUALITY_ACCREDITATION_FEEDBACK_READ: "quality_accreditation.feedback.read",
  QUALITY_ACCREDITATION_FEEDBACK_METADATA_CREATE: "quality_accreditation.feedback.metadata.create",
  QUALITY_ACCREDITATION_COMMITTEE_READ: "quality_accreditation.committee.read",
  QUALITY_ACCREDITATION_COMMITTEE_UPDATE: "quality_accreditation.committee.update",
  QUALITY_ACCREDITATION_EXTERNAL_REVIEW_READ: "quality_accreditation.external_review.read",
  QUALITY_ACCREDITATION_EXTERNAL_REVIEW_CREATE: "quality_accreditation.external_review.create",
  QUALITY_ACCREDITATION_EXTERNAL_REVIEW_UPDATE: "quality_accreditation.external_review.update",
  QUALITY_ACCREDITATION_GAP_ANALYSIS_READ: "quality_accreditation.gap_analysis.read",
  QUALITY_ACCREDITATION_GAP_ANALYSIS_UPDATE: "quality_accreditation.gap_analysis.update",
  QUALITY_ACCREDITATION_CALENDAR_READ: "quality_accreditation.calendar.read",
  QUALITY_ACCREDITATION_CALENDAR_UPDATE: "quality_accreditation.calendar.update",
  QUALITY_ACCREDITATION_RISK_REGISTER_READ: "quality_accreditation.risk_register.read",
  QUALITY_ACCREDITATION_RISK_REGISTER_UPDATE: "quality_accreditation.risk_register.update",
  QUALITY_ACCREDITATION_BRIDGES_READ: "quality_accreditation.bridges.read",
  QUALITY_ACCREDITATION_BRIDGES_CREATE: "quality_accreditation.bridges.create",
  QUALITY_ACCREDITATION_BRIDGES_UPDATE: "quality_accreditation.bridges.update",
  QUALITY_ACCREDITATION_BRAIN_SIGNALS_READ: "quality_accreditation.brain_signals.read",
  QUALITY_ACCREDITATION_AUDIT_READ: "quality_accreditation.audit.read",
  QUALITY_ACCREDITATION_STATUS_HISTORY_READ: "quality_accreditation.status_history.read",
  QUALITY_ACCREDITATION_ADMIN_READ: "quality_accreditation.admin.read",
  QUALITY_ACCREDITATION_ADMIN_CONFIGURE: "quality_accreditation.admin.configure",

  // Executive Control Tower (Wave 22 / A-033.2)
  EXECUTIVE_CONTROL_TOWER_READ: "admin.executive_control_tower.read",
  EXECUTIVE_CONTROL_TOWER_SUMMARY_READ: "admin.executive_control_tower.summary.read",
  EXECUTIVE_CONTROL_TOWER_ASSIGNMENTS_READ: "admin.executive_control_tower.assignments.read",
  EXECUTIVE_CONTROL_TOWER_DOCUMENTS_READ: "admin.executive_control_tower.documents.read",
  EXECUTIVE_CONTROL_TOWER_SLA_RISK_READ: "admin.executive_control_tower.sla_risk.read",
  EXECUTIVE_CONTROL_TOWER_STRATEGY_READ: "admin.executive_control_tower.strategy.read",
  EXECUTIVE_CONTROL_TOWER_AUDIT_READ: "admin.executive_control_tower.audit.read",
  EXECUTIVE_CONTROL_TOWER_DEPARTMENT_READ: "admin.executive_control_tower.department.read",
  EXECUTIVE_CONTROL_TOWER_METRIC_REGISTRY_READ: "admin.executive_control_tower.metric_registry.read",
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];
