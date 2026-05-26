import type { Permission } from '@/shared/config/permissions';
import { HR_STAFF_GOVERNANCE_PERMISSION_VALUES, HR_STAFF_GOVERNANCE_ROUTES } from './constants';

type PermissionUser =
  | { permissions?: Array<string | Permission>; rolePermissions?: Array<string | Permission>; grantedPermissions?: Array<string | Permission> }
  | Array<string | Permission>
  | null
  | undefined;

function permissionSet(userPermissions: PermissionUser) {
  const values = new Set<string>();
  if (Array.isArray(userPermissions)) {
    for (const permission of userPermissions) values.add(String(permission));
    return values;
  }
  for (const source of [userPermissions?.permissions, userPermissions?.rolePermissions, userPermissions?.grantedPermissions]) {
    for (const permission of source ?? []) values.add(String(permission));
  }
  return values;
}

export const HR_STAFF_GOVERNANCE_PERMISSION_KEYS = {
  ...HR_STAFF_GOVERNANCE_PERMISSION_VALUES,
} as const;

export const HR_STAFF_GOVERNANCE_PERMISSIONS = Object.values(HR_STAFF_GOVERNANCE_PERMISSION_KEYS);
export const HR_STAFF_GOVERNANCE_PERMISSION_COUNT = HR_STAFF_GOVERNANCE_PERMISSIONS.length;

export const HR_STAFF_GOVERNANCE_ROUTE_PERMISSION_MAP = Object.fromEntries(
  HR_STAFF_GOVERNANCE_ROUTES.map((route) => [route.key, route.requiredPermission]),
) as Record<(typeof HR_STAFF_GOVERNANCE_ROUTES)[number]['key'], Permission>;

export function hasHrPermission(userPermissions: PermissionUser, permission: Permission) {
  return permissionSet(userPermissions).has(permission);
}

export function hasAnyHrPermission(userPermissions: PermissionUser, permissions: Permission[]) {
  const granted = permissionSet(userPermissions);
  return permissions.some((permission) => granted.has(permission));
}

export function getAllowedHrRoutes(userPermissions: PermissionUser) {
  return HR_STAFF_GOVERNANCE_ROUTES.filter((route) => hasHrPermission(userPermissions, route.requiredPermission));
}

export function canReadHrOverview(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.overviewRead); }
export function canReadHrDashboard(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.dashboardRead); }
export function canReadRecruitment(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.recruitmentRead); }
export function canReviewRecruitment(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.recruitmentReview); }
export function canReadOnboarding(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.onboardingRead); }
export function canUpdateOnboarding(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.onboardingUpdate); }
export function canReadEmployeeRecords(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.employeeRecordsRead); }
export function canUpdateEmployeeRecords(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.employeeRecordsUpdate); }
export function canReadStaffProfiles(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.staffProfilesRead); }
export function canUpdateStaffProfiles(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.staffProfilesUpdate); }
export function canReadLeave(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.leaveRead); }
export function canReviewLeave(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.leaveReview); }
export function canReadAppraisals(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.appraisalsRead); }
export function canReviewAppraisals(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.appraisalsReview); }
export function canReadTraining(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.trainingRead); }
export function canUpdateTraining(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.trainingUpdate); }
export function canReadStaffRequests(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.staffRequestsRead); }
export function canReviewStaffRequests(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.staffRequestsReview); }
export function canReadStaffAppeals(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.staffAppealsRead); }
export function canReviewStaffAppeals(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.staffAppealsReview); }
export function canReadPolicyExceptions(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.policyExceptionsRead); }
export function canReviewPolicyExceptions(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.policyExceptionsReview); }
export function canReadDisciplinaryCases(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.disciplinaryCasesRead); }
export function canReviewDisciplinaryCases(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.disciplinaryCasesReview); }
export function canReadOffboarding(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.offboardingRead); }
export function canUpdateOffboarding(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.offboardingUpdate); }
export function canReadAccessLifecycle(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.accessLifecycleRead); }
export function canReviewAccessLifecycle(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.accessLifecycleReview); }
export function canReadWorkloadBridge(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.workloadBridgeRead); }
export function canReadPayrollReadiness(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.payrollReadinessRead); }
export function canReviewPayrollReadiness(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.payrollReadinessReview); }
export function canReadProviderReadiness(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.providerReadinessRead); }
export function canReadLimitations(userPermissions: PermissionUser) { return hasHrPermission(userPermissions, HR_STAFF_GOVERNANCE_PERMISSION_KEYS.limitationsRead); }