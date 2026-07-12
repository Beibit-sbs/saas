import { RolePortalShell } from "@/app/components/role-portal-shell";
import { getRolePortalConfig, getRolePortalHomeCards } from "@/app/components/role-portal-registry";

export default function RegistrarPortalPage() {
  const config = getRolePortalConfig("registrar");
  return (
    <RolePortalShell
      roleKey={config.roleKey}
      roleLabel={config.roleLabel}
      title={config.title}
      subtitle={config.subtitle}
      accentFrom={config.accentFrom}
      accentTo={config.accentTo}
      cards={getRolePortalHomeCards("registrar")}
    />
  );
}
