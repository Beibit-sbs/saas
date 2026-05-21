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
