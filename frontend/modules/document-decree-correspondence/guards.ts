import type { Permission } from '@/shared/config/permissions';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTES,
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

export const DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_KEYS = {
  ...DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES,
} as const;

export const DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS = Object.values(DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_KEYS);
export const DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT = DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS.length;

export const DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_PERMISSION_MAP = Object.fromEntries(
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTES.map((route) => [route.key, route.requiredPermission]),
) as Record<(typeof DOCUMENT_DECREE_CORRESPONDENCE_ROUTES)[number]['key'], Permission>;

export function hasDdcPermission(userPermissions: PermissionUser, permission: Permission) {
  return permissionSet(userPermissions).has(permission);
}

export function hasAnyDdcPermission(userPermissions: PermissionUser, permissions: Permission[]) {
  const granted = permissionSet(userPermissions);
  return permissions.some((permission) => granted.has(permission));
}

export function getAllowedDdcRoutes(userPermissions: PermissionUser) {
  return DOCUMENT_DECREE_CORRESPONDENCE_ROUTES.filter((route) => hasDdcPermission(userPermissions, route.requiredPermission));
}
