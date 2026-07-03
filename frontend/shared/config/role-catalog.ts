export type PlatformRole =
  | "superadmin"
  | "admin"
  | "auditor"
  | "dean"
  | "teacher"
  | "student"
  | "faculty"
  | "registrar";

export type NavigationProfile =
  | "superadmin"
  | "admin"
  | "auditor"
  | "dean"
  | "teacher"
  | "student"
  | "faculty"
  | "registrar"
  | "default";

export interface RoleDefinition {
  role: PlatformRole;
  label: string;
  responsibility: string;
  defaultPath: string;
  navigationProfile: NavigationProfile;
  consoleAccess: boolean;
  platformBillingAccess: boolean;
}

export const ROLE_PRIORITY: readonly PlatformRole[] = [
  "superadmin",
  "admin",
  "auditor",
  "dean",
  "teacher",
  "student",
  "faculty",
  "registrar",
] as const;

export const ROLE_CATALOG: Record<PlatformRole, RoleDefinition> = {
  superadmin: {
    role: "superadmin",
    label: "Platform Superadmin",
    responsibility: "Cross-tenant platform governance, billing, quotas, onboarding, automation, and global operations.",
    defaultPath: "/console/platform/tenants",
    navigationProfile: "superadmin",
    consoleAccess: true,
    platformBillingAccess: true,
  },
  admin: {
    role: "admin",
    label: "Tenant Administrator",
    responsibility: "Single-tenant university administration across users, academics, workflows, feature flags, jobs, and operations.",
    defaultPath: "/console",
    navigationProfile: "admin",
    consoleAccess: true,
    platformBillingAccess: false,
  },
  auditor: {
    role: "auditor",
    label: "Auditor",
    responsibility: "Read-only governance, audit, KPI, operational, and evidence review across allowed university surfaces.",
    defaultPath: "/console/audit",
    navigationProfile: "auditor",
    consoleAccess: true,
    platformBillingAccess: false,
  },
  dean: {
    role: "dean",
    label: "Dean Office",
    responsibility: "Faculty-level academic oversight for students, enrollments, grades, and scheduling coordination.",
    defaultPath: "/console",
    navigationProfile: "dean",
    consoleAccess: true,
    platformBillingAccess: false,
  },
  teacher: {
    role: "teacher",
    label: "Teacher",
    responsibility: "Teaching workflow access for students, grades, schedules, and academic requests.",
    defaultPath: "/console",
    navigationProfile: "teacher",
    consoleAccess: true,
    platformBillingAccess: false,
  },
  student: {
    role: "student",
    label: "Student",
    responsibility: "Self-service academic experience: schedule, grades, transcript, and student-focused insights.",
    defaultPath: "/student",
    navigationProfile: "student",
    consoleAccess: true,
    platformBillingAccess: false,
  },
  faculty: {
    role: "faculty",
    label: "Faculty Portal",
    responsibility: "Faculty-facing portal shell for teaching and advisory workflows.",
    defaultPath: "/faculty",
    navigationProfile: "faculty",
    consoleAccess: false,
    platformBillingAccess: false,
  },
  registrar: {
    role: "registrar",
    label: "Registrar Portal",
    responsibility: "Registrar-facing portal shell for academic record and enrollment coordination.",
    defaultPath: "/registrar",
    navigationProfile: "registrar",
    consoleAccess: false,
    platformBillingAccess: false,
  },
};

export function isPlatformRole(value: string): value is PlatformRole {
  return Object.prototype.hasOwnProperty.call(ROLE_CATALOG, value);
}

export function getKnownRoles(roles: string[]): PlatformRole[] {
  return roles.filter(isPlatformRole);
}

export function getPrimaryRole(roles: string[]): PlatformRole | null {
  const known = new Set(getKnownRoles(roles));
  for (const role of ROLE_PRIORITY) {
    if (known.has(role)) {
      return role;
    }
  }
  return null;
}

export function hasConsoleAccessForRoles(roles: string[]): boolean {
  return getKnownRoles(roles).some((role) => ROLE_CATALOG[role].consoleAccess);
}

export function canAccessPlatformBillingForRoles(roles: string[]): boolean {
  return getKnownRoles(roles).some((role) => ROLE_CATALOG[role].platformBillingAccess);
}

export function getDefaultPathForRoles(roles: string[]): string {
  const primaryRole = getPrimaryRole(roles);
  return primaryRole ? ROLE_CATALOG[primaryRole].defaultPath : "/login";
}

export function getNavigationProfileForRoles(roles: string[]): NavigationProfile {
  const primaryRole = getPrimaryRole(roles);
  return primaryRole ? ROLE_CATALOG[primaryRole].navigationProfile : "default";
}
