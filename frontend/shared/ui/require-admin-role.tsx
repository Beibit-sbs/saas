"use client";

import type { ReactNode } from "react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { AccessDenied } from "@/shared/ui/permission-gate";

interface RequireAdminRoleProps {
  children: ReactNode;
  message?: string;
}

export function RequireAdminRole({ children, message }: RequireAdminRoleProps) {
  const { roles } = usePermissions();
  const hasPlatformAdminRole = roles.includes("superadmin") || roles.includes("admin");

  if (!hasPlatformAdminRole) {
    return <AccessDenied message={message ?? "This section is available only to platform administrators."} />;
  }

  return <>{children}</>;
}
