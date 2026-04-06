import { RoleZoneLayout } from "@/app/components/role-zone-layout";

export default function FacultyLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Faculty Zone"
      navItems={[
        { href: "/faculty", label: "Home" },
        { href: "/console/students", label: "Roster" },
        { href: "/console/grades", label: "Grades" },
        { href: "/console/scheduling", label: "Schedule" },
      ]}
    >
      {children}
    </RoleZoneLayout>
  );
}
