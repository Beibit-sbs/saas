"use client";

import type { ReactNode } from "react";
import { ShieldOff } from "lucide-react";
import { useAdminAuth } from "@/shared/auth/context";
import type { Permission } from "@/shared/config/permissions";

// ---------------------------------------------------------------------------
// AccessDenied — full-panel "no permission" placeholder
// ---------------------------------------------------------------------------

interface AccessDeniedProps {
  message?: string;
}

export function AccessDenied({ message = "You don't have permission to view this content." }: AccessDeniedProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <ShieldOff className="h-12 w-12 text-muted-foreground/40 mb-4" />
      <h3 className="font-medium text-muted-foreground">Access Denied</h3>
      <p className="text-sm text-muted-foreground/70 mt-1 max-w-xs">{message}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PermissionGate — renders children only when the user has permission
// ---------------------------------------------------------------------------

interface PermissionGateProps {
  permission: Permission;
  /** Rendered when permission is absent. Defaults to null (silent hide). */
  fallback?: ReactNode;
  children: ReactNode;
}

export function PermissionGate({ permission, fallback = null, children }: PermissionGateProps) {
  const { hasPermission } = useAdminAuth();
  return hasPermission(permission) ? <>{children}</> : <>{fallback}</>;
}

// ---------------------------------------------------------------------------
// RequirePermission — renders AccessDenied block when permission is absent
// ---------------------------------------------------------------------------

interface RequirePermissionProps {
  permission: Permission;
  children: ReactNode;
  message?: string;
}

export function RequirePermission({ permission, message, children }: RequirePermissionProps) {
  return (
    <PermissionGate permission={permission} fallback={<AccessDenied message={message} />}>
      {children}
    </PermissionGate>
  );
}
