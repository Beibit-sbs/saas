import { RoleZoneLayout } from "@/app/components/role-zone-layout";
import { getRolePortalNavItems } from "@/app/components/role-portal-registry";

export default function FacultyLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Faculty Zone"
      navItems={getRolePortalNavItems("faculty")}
      backHref={null}
    >
      {children}
    </RoleZoneLayout>
  );
}
