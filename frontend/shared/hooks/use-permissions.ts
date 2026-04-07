"use client";

import { useAdminAuth } from "../auth/context";
import type { Permission } from "../config/permissions";

export function usePermissions() {
  const { hasPermission, hasAnyPermission, user } = useAdminAuth();
  return { hasPermission, hasAnyPermission, roles: user?.roles ?? [] };
}

export function useRequirePermission(permission: Permission): boolean {
  const { hasPermission } = useAdminAuth();
  return hasPermission(permission);
}
