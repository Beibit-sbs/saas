// Permission constants matching backend RBAC definitions

export const PERMISSIONS = {
  // Tenant management
  TENANTS_READ: "tenants.read",
  TENANTS_WRITE: "tenants.write",

  // Feature flags
  FEATURE_FLAGS_READ: "feature_flags.read",
  FEATURE_FLAGS_WRITE: "feature_flags.write",

  // Billing
  BILLING_READ: "billing.read",
  BILLING_WRITE: "billing.write",

  // Jobs
  JOBS_READ: "jobs.read",
  JOBS_WRITE: "jobs.write",

  // Notifications
  NOTIFICATIONS_READ: "notifications.read",
  NOTIFICATIONS_WRITE: "notifications.write",

  // Health / metrics
  HEALTH_READ: "health.read",
  METRICS_READ: "metrics.read",

  // Platform Ops Console
  OPS_READ: "ops.read",
  OPS_WRITE: "ops.write",

  // RBAC
  RBAC_READ: "rbac.read",
  RBAC_WRITE: "rbac.write",
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

  // Degree progress
  DEGREE_PROGRESS_READ: "degree_progress.read",

  // Admissions
  ADMISSIONS_READ: "admissions.read",
  ADMISSIONS_WRITE: "admissions.write",

    // Automation / Workflow Engine
    AUTOMATION_READ: "automation.read",
    AUTOMATION_WRITE: "automation.write",

  // AI Copilot (read-only foundation v1)
  AI_COPILOT_READ: "metrics.read",

  // Federation Layer v1
  FEDERATION_READ: "federation.read",
  FEDERATION_WRITE: "federation.write",

  // Developer Platform v1
  DEVELOPER_PLATFORM_READ: "developer_platform.read",
  DEVELOPER_PLATFORM_WRITE: "developer_platform.write",
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];
