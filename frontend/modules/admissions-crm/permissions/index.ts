import { useAdminAuth } from "@/shared/auth/context";

export const ADMISSIONS_CRM_RUNTIME_PERMISSIONS = {
  READ: "admin.admissions_crm.read",
  WRITE: "admin.admissions_crm.write",
  QUALIFY: "admin.admissions_crm.qualify",
  CONVERT: "admin.admissions_crm.convert",
  SUBMIT: "admin.admissions_crm.submit",
  AUDIT_READ: "admin.admissions_crm.audit.read",
} as const;

export const ADMISSIONS_CRM_PERMISSION_MATRIX_64 = [
  "admissions_crm.read",
  "admissions_crm.create",
  "admissions_crm.update",
  "admissions_crm.delete",
  "admissions_crm.lead.read",
  "admissions_crm.lead.create",
  "admissions_crm.lead.update",
  "admissions_crm.lead.delete",
  "admissions_crm.lead.qualify",
  "admissions_crm.lead.assign",
  "admissions_crm.lead.nurture",
  "admissions_crm.lead.review",
  "admissions_crm.applicant.read",
  "admissions_crm.applicant.create",
  "admissions_crm.applicant.update",
  "admissions_crm.applicant.delete",
  "admissions_crm.applicant.convert",
  "admissions_crm.applicant.profile.manage",
  "admissions_crm.applicant.consent.manage",
  "admissions_crm.application.read",
  "admissions_crm.application.create",
  "admissions_crm.application.update",
  "admissions_crm.application.delete",
  "admissions_crm.application.submit",
  "admissions_crm.application.intake.check",
  "admissions_crm.application.program.manage",
  "admissions_crm.application.review.queue",
  "admissions_crm.document.read",
  "admissions_crm.document.submit",
  "admissions_crm.document.update",
  "admissions_crm.document.verify",
  "admissions_crm.document.reject",
  "admissions_crm.document.exception.manage",
  "admissions_crm.communication.read",
  "admissions_crm.communication.thread.create",
  "admissions_crm.communication.thread.update",
  "admissions_crm.communication.template.manage",
  "admissions_crm.communication.dispatch.log",
  "admissions_crm.communication.audit.read",
  "admissions_crm.campaign.read",
  "admissions_crm.campaign.create",
  "admissions_crm.campaign.update",
  "admissions_crm.campaign.delete",
  "admissions_crm.campaign.target.manage",
  "admissions_crm.campaign.event.manage",
  "admissions_crm.interview.read",
  "admissions_crm.interview.schedule",
  "admissions_crm.interview.reschedule",
  "admissions_crm.interview.cancel",
  "admissions_crm.interview.evaluate",
  "admissions_crm.decision.read",
  "admissions_crm.decision.create",
  "admissions_crm.decision.review",
  "admissions_crm.decision.approve",
  "admissions_crm.decision.publish",
  "admissions_crm.decision.condition.manage",
  "admissions_crm.handoff.read",
  "admissions_crm.handoff.create",
  "admissions_crm.handoff.send",
  "admissions_crm.handoff.acknowledge",
  "admissions_crm.analytics.read",
  "admissions_crm.analytics.export",
  "admissions_crm.dashboard.read",
  "admissions_crm.dashboard.executive.read",
] as const;

export type AdmissionsCrmPersona =
  | "read-only"
  | "editor"
  | "reviewer"
  | "administrator"
  | "auditor";

export const ADMISSIONS_CRM_VISIBILITY_MODEL: Record<AdmissionsCrmPersona, readonly string[]> = {
  "read-only": [ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ],
  editor: [
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.QUALIFY,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.CONVERT,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.SUBMIT,
  ],
  reviewer: [
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.AUDIT_READ,
  ],
  administrator: [
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.QUALIFY,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.CONVERT,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.SUBMIT,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.AUDIT_READ,
  ],
  auditor: [
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ,
    ADMISSIONS_CRM_RUNTIME_PERMISSIONS.AUDIT_READ,
  ],
};

export function hasAdmissionsCrmPermission(
  userPermissions: ReadonlyArray<string> | null | undefined,
  required: string,
): boolean {
  if (!userPermissions || userPermissions.length === 0) {
    return false;
  }
  return userPermissions.includes(required);
}

export function hasAnyAdmissionsCrmPermission(
  userPermissions: ReadonlyArray<string> | null | undefined,
  required: ReadonlyArray<string>,
): boolean {
  if (!userPermissions || userPermissions.length === 0) {
    return false;
  }
  return required.some((permission) => userPermissions.includes(permission));
}

export function useAdmissionsCrmPermissionChecker() {
  const { user, hasPermission } = useAdminAuth();
  const stringPermissions = (user?.permissions ?? []) as string[];
  return {
    permissions: stringPermissions,
    has: (permission: string) => hasPermission(permission as never),
    hasAny: (permissions: readonly string[]) => permissions.some((permission) => hasPermission(permission as never)),
  };
}
