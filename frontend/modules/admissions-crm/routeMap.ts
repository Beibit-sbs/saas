export type AdmissionsCrmRouteKey =
  | "overview"
  | "leads"
  | "leads-new"
  | "lead-detail"
  | "applicants"
  | "applicants-new"
  | "applicant-detail"
  | "applications"
  | "applications-new"
  | "application-detail"
  | "workflows"
  | "audit"
  | "dashboard"
  | "settings-permissions";

export interface AdmissionsCrmRouteDefinition {
  key: AdmissionsCrmRouteKey;
  path: string;
  title: string;
  requiredPermissions: string[];
  tenantScoped: true;
}

export const ADMISSIONS_CRM_BASE_ROUTE = "/console/admissions";

export const ADMISSIONS_CRM_ROUTES: AdmissionsCrmRouteDefinition[] = [
  {
    key: "overview",
    path: ADMISSIONS_CRM_BASE_ROUTE,
    title: "Admissions Overview",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "leads",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/leads`,
    title: "Lead Registry",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "leads-new",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/leads/new`,
    title: "New Lead",
    requiredPermissions: ["admin.admissions_crm.write"],
    tenantScoped: true,
  },
  {
    key: "lead-detail",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/leads/:leadId`,
    title: "Lead Detail",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "applicants",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/applicants`,
    title: "Applicant Registry",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "applicants-new",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/applicants/new`,
    title: "New Applicant",
    requiredPermissions: ["admin.admissions_crm.convert", "admin.admissions_crm.write"],
    tenantScoped: true,
  },
  {
    key: "applicant-detail",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/applicants/:applicantId`,
    title: "Applicant Detail",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "applications",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/applications`,
    title: "Application Registry",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "applications-new",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/applications/new`,
    title: "New Application",
    requiredPermissions: ["admin.admissions_crm.write"],
    tenantScoped: true,
  },
  {
    key: "application-detail",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/applications/:applicationId`,
    title: "Application Detail",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "workflows",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/workflows`,
    title: "Workflow Health",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "audit",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/audit`,
    title: "Audit",
    requiredPermissions: ["admin.admissions_crm.audit.read"],
    tenantScoped: true,
  },
  {
    key: "dashboard",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/dashboard`,
    title: "Admissions Dashboard",
    requiredPermissions: ["admin.admissions_crm.read"],
    tenantScoped: true,
  },
  {
    key: "settings-permissions",
    path: `${ADMISSIONS_CRM_BASE_ROUTE}/settings/permissions`,
    title: "Permissions Matrix",
    requiredPermissions: ["admin.admissions_crm.audit.read"],
    tenantScoped: true,
  },
];

export const ADMISSIONS_CRM_ROUTE_COUNT = ADMISSIONS_CRM_ROUTES.length;
