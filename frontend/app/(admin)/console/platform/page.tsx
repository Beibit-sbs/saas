"use client";

import { PlatformSectionView } from "./platform-section-view";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { canAccessPlatformBillingForRoles } from "@/shared/config/role-catalog";

export default function PlatformControlPlanePage() {
  const { hasPermission, roles } = usePermissions();
  if (!hasPermission(PERMISSIONS.DEVELOPER_PLATFORM_READ)) {
    return <AccessDenied />;
  }
  if (!canAccessPlatformBillingForRoles(roles)) {
    return <AccessDenied message="Platform control plane is available only to the platform superadmin." />;
  }

  if (!hasPermission(PERMISSIONS.DEVELOPER_PLATFORM_READ)) {
    return <AccessDenied />;
  }

  return <PlatformSectionView section="overview" />;
}
