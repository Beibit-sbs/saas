"use client";

import type { ReactNode } from "react";
import { useAdminAuth } from "@/shared/auth/context";

export function AdmissionsPermissionGate({
  permissions,
  children,
  fallback,
}: {
  permissions: readonly string[];
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { hasPermission } = useAdminAuth();
  const allowed = permissions.some((permission) => hasPermission(permission as never));
  if (allowed) {
    return <>{children}</>;
  }
  return <>{fallback ?? null}</>;
}

export function AdmissionsRequirePermission({
  permissions,
  children,
}: {
  permissions: readonly string[];
  children: ReactNode;
}) {
  return (
    <AdmissionsPermissionGate
      permissions={permissions}
      fallback={<div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">Access denied for this admissions action.</div>}
    >
      {children}
    </AdmissionsPermissionGate>
  );
}
