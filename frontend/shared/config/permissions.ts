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

  // RBAC
  RBAC_READ: "rbac.read",
  RBAC_WRITE: "rbac.write",

  // Audit
  AUDIT_READ: "audit.read",

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
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

// Role → base permissions mapping (mirrors backend BASELINE_ROLE_PERMISSIONS)
export const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  admin: Object.values(PERMISSIONS),
  operator: [
    PERMISSIONS.TENANTS_READ,
    PERMISSIONS.FEATURE_FLAGS_READ,
    PERMISSIONS.JOBS_READ,
    PERMISSIONS.JOBS_WRITE,
    PERMISSIONS.NOTIFICATIONS_READ,
    PERMISSIONS.HEALTH_READ,
    PERMISSIONS.METRICS_READ,
    PERMISSIONS.AI_COPILOT_READ,
    PERMISSIONS.STUDENTS_READ,
    PERMISSIONS.ENROLLMENTS_READ,
    PERMISSIONS.GRADES_READ,
    PERMISSIONS.TRANSCRIPTS_READ,
    PERMISSIONS.SCHEDULING_READ,
      PERMISSIONS.AUTOMATION_READ,
  ],
  viewer: [
    PERMISSIONS.TENANTS_READ,
    PERMISSIONS.JOBS_READ,
    PERMISSIONS.NOTIFICATIONS_READ,
    PERMISSIONS.HEALTH_READ,
    PERMISSIONS.STUDENTS_READ,
    PERMISSIONS.ENROLLMENTS_READ,
    PERMISSIONS.TRANSCRIPTS_READ,
    PERMISSIONS.SCHEDULING_READ,
  ],
};
