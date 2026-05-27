import type { Permission } from '@/shared/config/permissions';
import {
  STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES,
  STUDENT_SERVICES_SUPPORT_ROUTES,
} from './constants';

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

export const STUDENT_SERVICES_SUPPORT_PERMISSIONS = {
  ...STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES,
} as const;

export const STUDENT_SERVICES_SUPPORT_PERMISSION_COUNT = Object.keys(STUDENT_SERVICES_SUPPORT_PERMISSIONS).length;

export const STUDENT_SERVICES_SUPPORT_ROUTE_PERMISSION_MAP = Object.fromEntries(
  STUDENT_SERVICES_SUPPORT_ROUTES.map((route) => [route.key, route.requiredPermission]),
);

export function hasStudentServicesSupportPermission(userPermissions: PermissionUser, permission: Permission) {
  return permissionSet(userPermissions).has(permission);
}

export function hasAnyStudentServicesSupportPermission(userPermissions: PermissionUser, permissions: Permission[]) {
  const granted = permissionSet(userPermissions);
  return permissions.some((permission) => granted.has(permission));
}

export function getAllowedStudentServicesSupportRoutes(userPermissions: PermissionUser) {
  return STUDENT_SERVICES_SUPPORT_ROUTES.filter((route) =>
    hasStudentServicesSupportPermission(userPermissions, route.requiredPermission),
  );
}
