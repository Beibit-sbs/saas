"use client";

import type { ReactNode } from "react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { hasConsoleAccessForRoles } from "@/shared/config/role-catalog";

interface RequireAdminRoleProps {
  children: ReactNode;
  message?: string;
}

export function RequireAdminRole({ children, message }: RequireAdminRoleProps) {
  const { roles } = usePermissions();
  const hasConsoleAccess = hasConsoleAccessForRoles(roles);

  if (!hasConsoleAccess) {
    return <AccessDenied message={message ?? "This section is available only to roles with console access."} />;
  }

  return <>{children}</>;
}
