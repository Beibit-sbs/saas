import { RoleZoneLayout } from "@/app/components/role-zone-layout";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Student Zone"
      navItems={[
        { href: "/student", label: "Home" },
        { href: "/console/enrollments", label: "Enrollments" },
        { href: "/console/grades", label: "Grades" },
        { href: "/console/transcripts", label: "Transcripts" },
      ]}
    >
      {children}
    </RoleZoneLayout>
  );
}
