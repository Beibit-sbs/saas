"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useCreateIdentityMapping,
  useDirectoryProviders,
  useIdentityMappings,
  useIdentityProviders,
  useTestDirectoryProvider,
} from "@/modules/identity-admin/hooks";
import type {
  DirectoryProvider,
  IdentityMapping,
  IdentityProvider,
} from "@/modules/identity-admin/types";

export default function IdentityPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [providerId, setProviderId] = useState("");
  const [externalGroup, setExternalGroup] = useState("");
  const [platformRole, setPlatformRole] = useState("");
  const [testLogin, setTestLogin] = useState("");
  const [lastTestResult, setLastTestResult] = useState("");

  const providersQuery = useIdentityProviders();
  const directoryProvidersQuery = useDirectoryProviders();
  const mappingsQuery = useIdentityMappings();

  const createMapping = useCreateIdentityMapping();
  const testDirectoryProvider = useTestDirectoryProvider();

  if (
    providersQuery.error ||
    directoryProvidersQuery.error ||
    mappingsQuery.error
  ) {
    return (
      <ErrorState
        title="Failed to load identity data"
        onRetry={() => {
          providersQuery.refetch();
          directoryProvidersQuery.refetch();
          mappingsQuery.refetch();
        }}
      />
    );
  }

  const providerColumns: Column<IdentityProvider>[] = [
    {
      key: "provider",
      header: tAny("identityProvider"),
      cell: (r) => r.provider,
      sortValue: (r) => r.provider,
    },
    {
      key: "type",
      header: tAny("identityType"),
      cell: (r) => r.type,
      sortValue: (r) => r.type,
    },
    {
      key: "enabled",
      header: tAny("identityEnabled"),
      cell: (r) => String(r.enabled),
      sortValue: (r) => (r.enabled ? "1" : "0"),
    },
  ];

  const directoryColumns: Column<DirectoryProvider>[] = [
    {
      key: "id",
      header: "ID",
      cell: (r) => String(r.id),
      sortValue: (r) => r.id,
    },
    {
      key: "name",
      header: tAny("identityProvider"),
      cell: (r) => r.name,
      sortValue: (r) => r.name,
    },
    {
      key: "type",
      header: tAny("identityType"),
      cell: (r) => r.type,
      sortValue: (r) => r.type,
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
          <Button
            variant="outline"
            size="sm"
            disabled={testDirectoryProvider.isPending}
            onClick={() =>
              testDirectoryProvider.mutate(
                { providerId: r.id, login: testLogin.trim() || undefined },
                {
                  ...getHandlers({ successTitle: tAny("identityTested") }),
                  onSuccess: (payload) => {
                    getHandlers({
                      successTitle: tAny("identityTested"),
                    }).onSuccess(undefined);
                    setLastTestResult(JSON.stringify(payload.result));
                  },
                },
              )
            }
          >
            {tAny("identityTest")}
          </Button>
        </PermissionGate>
      ),
    },
  ];

  const mappingColumns: Column<IdentityMapping>[] = [
    {
      key: "id",
      header: "ID",
      cell: (r) => String(r.id),
      sortValue: (r) => r.id,
    },
    {
      key: "provider_id",
      header: tAny("identityProviderId"),
      cell: (r) => String(r.provider_id),
      sortValue: (r) => r.provider_id,
    },
    {
      key: "external_group",
      header: tAny("identityExternalGroup"),
      cell: (r) => r.external_group,
      sortValue: (r) => r.external_group,
    },
    {
      key: "platform_role",
      header: tAny("identityPlatformRole"),
      cell: (r) => r.platform_role,
      sortValue: (r) => r.platform_role,
    },
  ];

  const parsedProviderId = Number.parseInt(providerId, 10);
  const canCreateMapping =
    Number.isFinite(parsedProviderId) &&
    parsedProviderId > 0 &&
    externalGroup.trim().length > 0 &&
    platformRole.trim().length > 0;

  return (
    <RequirePermission permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
    <div className="space-y-6" data-testid="identity-page">
      <PageHeader
        title={t("nav.identityAccess")}
        description={tAny("identityHelp")}
        icon={ShieldCheck}
      />

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("identityProviders")}</h2>
        <DataTable
          columns={providerColumns}
          data={providersQuery.data?.providers ?? []}
          isLoading={providersQuery.isLoading}
          getRowKey={(r) => r.provider}
          emptyTitle={tAny("identityNoProviders")}
        />
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("directoryProviders")}</h2>
        <div className="space-y-1.5">
          <Label htmlFor="identity-test-login">Login (optional)</Label>
          <Input
            id="identity-test-login"
            value={testLogin}
            onChange={(e) => setTestLogin(e.target.value)}
            placeholder="john.doe"
          />
        </div>
        <DataTable
          columns={directoryColumns}
          data={directoryProvidersQuery.data?.providers ?? []}
          isLoading={directoryProvidersQuery.isLoading}
          getRowKey={(r) => String(r.id)}
          emptyTitle={tAny("identityNoProviders")}
        />
        {lastTestResult ? (
          <pre className="rounded-md border bg-muted p-3 text-xs overflow-x-auto">
            {lastTestResult}
          </pre>
        ) : null}
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("identityMappings")}</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="mapping-provider-id">
              {tAny("identityProviderId")}
            </Label>
            <Input
              id="mapping-provider-id"
              type="number"
              min={1}
              value={providerId}
              onChange={(e) => setProviderId(e.target.value)}
              placeholder="1"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mapping-group">
              {tAny("identityExternalGroup")}
            </Label>
            <Input
              id="mapping-group"
              value={externalGroup}
              onChange={(e) => setExternalGroup(e.target.value)}
              placeholder="cn=registrar,ou=groups,dc=example,dc=edu"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mapping-role">{tAny("identityPlatformRole")}</Label>
            <Input
              id="mapping-role"
              value={platformRole}
              onChange={(e) => setPlatformRole(e.target.value)}
              placeholder="registrar"
            />
          </div>
        </div>
        <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
          <Button
            disabled={!canCreateMapping || createMapping.isPending}
            onClick={() =>
              createMapping.mutate(
                {
                  provider_id: parsedProviderId,
                  external_group: externalGroup.trim(),
                  platform_role: platformRole.trim(),
                },
                {
                  ...getHandlers({
                    successTitle: tAny("identityMappingCreated"),
                  }),
                  onSuccess: () => {
                    getHandlers({
                      successTitle: tAny("identityMappingCreated"),
                    }).onSuccess(undefined);
                    setProviderId("");
                    setExternalGroup("");
                    setPlatformRole("");
                  },
                },
              )
            }
          >
            {tAny("add")}
          </Button>
        </PermissionGate>
        <DataTable
          columns={mappingColumns}
          data={mappingsQuery.data?.mappings ?? []}
          isLoading={mappingsQuery.isLoading}
          getRowKey={(r) => String(r.id)}
          emptyTitle={tAny("identityNoMappings")}
        />
      </section>
    </div>
    </RequirePermission>
  );
}
