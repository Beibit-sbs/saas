import type { Permission } from '@/shared/config/permissions';
import { PERMISSIONS } from '@/shared/config/permissions';

type PermissionUser =
  | {
      permissions?: Array<string | Permission>;
      rolePermissions?: Array<string | Permission>;
      grantedPermissions?: Array<string | Permission>;
    }
  | null
  | undefined;

function permissionSet(user: PermissionUser) {
  const values = new Set<string>();
  for (const source of [user?.permissions, user?.rolePermissions, user?.grantedPermissions]) {
    for (const permission of source ?? []) {
      values.add(String(permission));
    }
  }
  return values;
}

export const COMMUNICATIONS_PERMISSIONS = {
  summaryRead: PERMISSIONS.COMMUNICATIONS_SUMMARY_READ,
  notificationsRead: PERMISSIONS.COMMUNICATIONS_NOTIFICATIONS_READ,
  announcementsRead: PERMISSIONS.COMMUNICATIONS_ANNOUNCEMENTS_READ,
  templatesRead: PERMISSIONS.COMMUNICATIONS_TEMPLATES_READ,
  preferencesRead: PERMISSIONS.COMMUNICATIONS_PREFERENCES_READ,
  auditRead: PERMISSIONS.COMMUNICATIONS_AUDIT_READ,
  escalationsRead: PERMISSIONS.COMMUNICATIONS_ESCALATIONS_READ,
  emergencyRead: PERMISSIONS.COMMUNICATIONS_EMERGENCY_READ,
  providersRead: PERMISSIONS.COMMUNICATIONS_PROVIDERS_READ,
  brainActionsRead: PERMISSIONS.COMMUNICATIONS_BRAIN_ACTIONS_READ,
} as const;

export function hasCommunicationsPermission(user: PermissionUser, permission: Permission) {
  return permissionSet(user).has(permission);
}
