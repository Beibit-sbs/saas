import { RoleZoneLayout } from "@/app/components/role-zone-layout";
import { REGISTRAR_NAV_ITEMS } from "./sections";

export default function RegistrarLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Registrar Zone"
      navItems={[...REGISTRAR_NAV_ITEMS]}
    >
      {children}
    </RoleZoneLayout>
  );
}
