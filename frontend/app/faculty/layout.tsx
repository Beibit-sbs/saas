import { RoleZoneLayout } from "@/app/components/role-zone-layout";
import { FACULTY_NAV_ITEMS } from "./sections";

export default function FacultyLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Faculty Zone"
      navItems={[...FACULTY_NAV_ITEMS]}
    >
      {children}
    </RoleZoneLayout>
  );
}
