import type { Permission } from '@/shared/config/permissions';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES, FINANCE_PROCUREMENT_ASSET_ROUTES } from './constants';

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

export const FINANCE_PROCUREMENT_ASSET_PERMISSION_KEYS = {
  ...FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES,
} as const;

export const FINANCE_PROCUREMENT_ASSET_PERMISSIONS = Object.values(FINANCE_PROCUREMENT_ASSET_PERMISSION_KEYS);
export const FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT = FINANCE_PROCUREMENT_ASSET_PERMISSIONS.length;

export const FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP = Object.fromEntries(
  FINANCE_PROCUREMENT_ASSET_ROUTES.map((route) => [route.key, route.requiredPermission]),
) as Record<(typeof FINANCE_PROCUREMENT_ASSET_ROUTES)[number]['key'], Permission>;

export function hasFpaPermission(userPermissions: PermissionUser, permission: Permission) {
  return permissionSet(userPermissions).has(permission);
}

export function hasAnyFpaPermission(userPermissions: PermissionUser, permissions: Permission[]) {
  const granted = permissionSet(userPermissions);
  return permissions.some((permission) => granted.has(permission));
}

export function getAllowedFpaRoutes(userPermissions: PermissionUser) {
  return FINANCE_PROCUREMENT_ASSET_ROUTES.filter((route) => hasFpaPermission(userPermissions, route.requiredPermission));
}
