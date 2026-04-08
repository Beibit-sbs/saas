"use client";

import { useState } from "react";
import { Network } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLdapStatus, useTestLdapConnection } from "@/modules/ldap-admin/hooks";

export default function LdapPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [lastResult, setLastResult] = useState<string>("");

  const statusQuery = useLdapStatus();
  const testConnection = useTestLdapConnection();

  if (statusQuery.error) {
    return <ErrorState title="Failed to load LDAP status" onRetry={statusQuery.refetch} />;
  }

  const ldap = statusQuery.data?.ldap;

  return (
    <RequirePermission permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
    <div className="space-y-6" data-testid="ldap-page">
      <PageHeader
        title={t("nav.ldap")}
        description={tAny("ldapSettings")}
        icon={Network}
      />

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("ldapConfigTitle")}</h2>
        {statusQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">{tAny("loading")}</p>
        ) : (
          <div className="grid gap-2 text-sm md:grid-cols-2">
            <div>
              <span className="text-muted-foreground">{tAny("status")}: </span>
              <span>{ldap?.enabled ? tAny("enabled") : tAny("disabled")}</span>
            </div>
            <div>
              <span className="text-muted-foreground">{tAny("ldapServerUri")}: </span>
              <span>{ldap?.host ?? "-"}{ldap?.port ? `:${ldap.port}` : ""}</span>
            </div>
            <div>
              <span className="text-muted-foreground">{tAny("ldapBaseDn")}: </span>
              <span>{ldap?.base_dn ?? "-"}</span>
            </div>
            <div>
              <span className="text-muted-foreground">{tAny("ldapBindDn")}: </span>
              <span>{ldap?.bind_dn ?? "-"}</span>
            </div>
          </div>
        )}
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("testConnection")}</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="ldap-login">{tAny("ldapLoginAttr")}</Label>
            <Input
              id="ldap-login"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={tAny("ldapLoginPlaceholder")}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ldap-password">{tAny("ldapBindPassword")}</Label>
            <Input
              id="ldap-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tAny("ldapPasswordPlaceholder")}
            />
          </div>
        </div>
        <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
          <Button
            disabled={testConnection.isPending}
            onClick={() =>
              testConnection.mutate(
                {
                  username: username.trim() || undefined,
                  password: password || undefined,
                },
                {
                  ...getHandlers({ successTitle: tAny("testConnection") }),
                  onSuccess: (payload) => {
                    getHandlers({ successTitle: tAny("testConnection") }).onSuccess(undefined);
                    setLastResult(JSON.stringify(payload.result));
                  },
                },
              )
            }
          >
            {tAny("testConnection")}
          </Button>
        </PermissionGate>
        {lastResult ? (
          <pre className="rounded-md border bg-muted p-3 text-xs overflow-x-auto">{lastResult}</pre>
        ) : null}
      </section>
    </div>
    </RequirePermission>
  );
}
