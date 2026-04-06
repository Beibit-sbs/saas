import { RolePortalShell } from "@/app/components/role-portal-shell";

export default function RegistrarPortalPage() {
  return (
    <RolePortalShell
      roleKey="registrar"
      roleLabel="Registrar Zone"
      title="Registrar and Dean Office"
      subtitle="Academic governance surface for admissions control, tenant policy oversight, and evidence-driven compliance."
      accentFrom="#4c1d95"
      accentTo="#7c2d12"
      cards={[
        {
          title: "Admissions Pipeline",
          description: "Track applicant lifecycle and approve stage transitions with explicit governance trace.",
          href: "/console/admissions",
          cta: "Open admissions",
        },
        {
          title: "Institution Governance",
          description: "Review tenant status, plans, and policy settings for institution-level operations.",
          href: "/console/tenants",
          cta: "Open governance",
        },
        {
          title: "Audit and Evidence",
          description: "Inspect operational logs and audit events used in release and compliance decisions.",
          href: "/console/audit",
          cta: "View audit",
        },
        {
          title: "Platform Controls",
          description: "Use platform controls for environment configuration and release-time checks.",
          href: "/console/platform",
          cta: "Open controls",
        },
      ]}
    />
  );
}
