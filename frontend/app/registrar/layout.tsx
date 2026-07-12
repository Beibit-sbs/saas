import { RoleZoneLayout } from "@/app/components/role-zone-layout";
import { getRolePortalNavItems } from "@/app/components/role-portal-registry";

export default function RegistrarLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Registrar Zone"
      navItems={getRolePortalNavItems("registrar")}
    >
      {children}
    </RoleZoneLayout>
  );
}
