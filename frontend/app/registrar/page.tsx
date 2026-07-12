import { RolePortalShell } from "@/app/components/role-portal-shell";
import { REGISTRAR_HOME_CARDS } from "./sections";

export default function RegistrarPortalPage() {
  return (
    <RolePortalShell
      roleKey="registrar"
      roleLabel="Registrar Zone"
      title="Registrar and Dean Office"
      subtitle="Academic governance surface for admissions control, policy review, and evidence-driven registrar operations."
      accentFrom="#4c1d95"
      accentTo="#7c2d12"
      cards={REGISTRAR_HOME_CARDS}
    />
  );
}
