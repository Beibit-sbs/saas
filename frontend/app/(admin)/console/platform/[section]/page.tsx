"use client";

import { notFound } from "next/navigation";
import { PlatformSectionView } from "../platform-section-view";
import { isPlatformSectionSlug } from "../platform-sections";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { canAccessPlatformBillingForRoles } from "@/shared/config/role-catalog";

type PlatformSectionPageProps = {
  params: {
    section: string;
  };
};

export default function PlatformSectionPage({ params }: PlatformSectionPageProps) {
  const { hasPermission, roles } = usePermissions();
  if (!isPlatformSectionSlug(params.section)) {
    notFound();
  }

  if (!hasPermission(PERMISSIONS.DEVELOPER_PLATFORM_READ)) {
    return <AccessDenied />;
  }

  if (!canAccessPlatformBillingForRoles(roles)) {
    return <AccessDenied message="Platform control plane is available only to the platform superadmin." />;
  }

  return <PlatformSectionView section={params.section} />;
}
