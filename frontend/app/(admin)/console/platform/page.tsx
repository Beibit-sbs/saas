"use client";

import { PlatformSectionView } from "./platform-section-view";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";

export default function PlatformControlPlanePage() {
  const { hasPermission } = usePermissions();
  if (!hasPermission(PERMISSIONS.TENANTS_READ)) {
    return <AccessDenied />;
  }

  return <PlatformSectionView section="overview" />;
}
