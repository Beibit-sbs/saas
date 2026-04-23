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
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];
