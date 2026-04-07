import { RoleZoneLayout } from "@/app/components/role-zone-layout";

export default function RegistrarLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleZoneLayout
      zoneTitle="Registrar Zone"
      navItems={[
        { href: "/registrar", label: "Home" },
        { href: "/console/admissions", label: "Admissions" },
        { href: "/console/tenants", label: "Governance" },
        { href: "/console/audit", label: "Audit" },
      ]}
    >
      {children}
    </RoleZoneLayout>
  );
}
