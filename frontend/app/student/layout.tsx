import { RoleZoneLayout } from "@/app/components/role-zone-layout";
import { getRolePortalNavItems } from "@/app/components/role-portal-registry";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Student Zone"
      navItems={getRolePortalNavItems("student")}
    >
      {children}
    </RoleZoneLayout>
  );
}
