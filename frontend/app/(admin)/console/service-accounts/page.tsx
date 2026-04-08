"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useServiceAccounts,
  useCreateServiceAccount,
  useIssueServiceToken,
  useRevokeServiceAccount,
} from "@/modules/service-accounts/hooks";
import { ServiceAccount } from "@/modules/service-accounts/types";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { KeyRound } from "lucide-react";

export default function ServiceAccountsPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newPerms, setNewPerms] = useState("");

  const [tokenOpen, setTokenOpen] = useState(false);
  const [tokenAccountId, setTokenAccountId] = useState("");
  const [tokenSecret, setTokenSecret] = useState("");
  const [issuedToken, setIssuedToken] = useState("");

  const { data, isLoading, error, refetch } = useServiceAccounts();
  const createAccount = useCreateServiceAccount();
  const revokeAccount = useRevokeServiceAccount();
  const issueToken = useIssueServiceToken(tokenAccountId);

  const canCreate =
    newName.trim().length >= 2 && newPerms.trim().length > 0;

  if (error) {
    return (
      <ErrorState title="Failed to load service accounts" onRetry={refetch} />
    );
  }

  const columns: Column<ServiceAccount>[] = [
    {
      key: "name",
      header: tAny("serviceAccountName"),
      cell: (r) => (
        <span className={r.revoked ? "line-through text-muted-foreground" : "font-medium"}>
          {r.name}
        </span>
      ),
      sortValue: (r) => r.name.toLowerCase(),
    },
    {
      key: "account_id",
      header: "ID",
      cell: (r) => <code className="text-xs">{r.account_id}</code>,
      sortValue: (r) => r.account_id,
    },
    {
      key: "permissions",
      header: tAny("serviceAccountPerms"),
      cell: (r) => (
        <span className="text-xs text-muted-foreground">
          {r.permissions.join(", ") || "—"}
        </span>
      ),
      sortValue: (r) => r.permissions.join(","),
    },
    {
      key: "status",
      header: "Status",
      cell: (r) => (
        <span
          className={
            r.revoked ? "text-destructive text-xs" : "text-green-600 text-xs"
          }
        >
          {r.revoked ? "Revoked" : "Active"}
        </span>
      ),
      sortValue: (r) => (r.revoked ? 1 : 0),
    },
    {
      key: "actions",
      header: "",
      width: "180px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
          <div className="flex gap-1">
            {!r.revoked && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(event) => {
                    event.stopPropagation();
                    setTokenAccountId(r.account_id);
                    setTokenSecret("");
                    setIssuedToken("");
                    setTokenOpen(true);
                  }}
                >
                  {tAny("serviceAccountIssueToken")}
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  disabled={revokeAccount.isPending}
                  onClick={(event) => {
                    event.stopPropagation();
                    revokeAccount.mutate(
                      r.account_id,
                      getHandlers({ successTitle: tAny("serviceAccountRevoked") }),
                    );
                  }}
                >
                  {tAny("serviceAccountRevoke")}
                </Button>
              </>
            )}
          </div>
        </PermissionGate>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
    <div className="space-y-4" data-testid="service-accounts-page">
      <PageHeader
        title={t("nav.serviceAccounts")}
        description={tAny("serviceAccountsHelp")}
        icon={KeyRound}
        actions={
          <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              {tAny("addServiceAccount")}
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={data?.accounts ?? []}
        isLoading={isLoading}
        getRowKey={(r) => r.account_id}
        emptyTitle={tAny("noServiceAccounts")}
      />

      {/* Create drawer */}
      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setNewName("");
          setNewPerms("");
        }}
        title={tAny("addServiceAccount")}
        description={tAny("serviceAccountsHelp")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="sa-name">{tAny("serviceAccountName")}</Label>
            <Input
              id="sa-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="analytics-reader"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sa-perms">{tAny("serviceAccountPerms")}</Label>
            <Input
              id="sa-perms"
              value={newPerms}
              onChange={(e) => setNewPerms(e.target.value)}
              placeholder="analytics.read,students.read"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
            <Button
              disabled={!canCreate || createAccount.isPending}
              onClick={() =>
                createAccount.mutate(
                  {
                    name: newName.trim(),
                    permissions: newPerms
                      .split(",")
                      .map((p) => p.trim())
                      .filter(Boolean),
                  },
                  {
                    ...getHandlers({
                      successTitle: tAny("serviceAccountCreated"),
                    }),
                    onSuccess: () => {
                      getHandlers({
                        successTitle: tAny("serviceAccountCreated"),
                      }).onSuccess(undefined);
                      setCreateOpen(false);
                      setNewName("");
                      setNewPerms("");
                    },
                  },
                )
              }
            >
              {tAny("addServiceAccount")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>

      {/* Issue token drawer */}
      <DrawerPanel
        open={tokenOpen}
        onClose={() => {
          setTokenOpen(false);
          setIssuedToken("");
        }}
        title={tAny("serviceAccountIssueToken")}
        description={tokenAccountId}
      >
        <div className="space-y-4">
          {issuedToken ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-green-600">
                {tAny("serviceAccountTokenIssued")}
              </p>
              <code className="block rounded bg-muted p-3 text-xs break-all select-all">
                {issuedToken}
              </code>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigator.clipboard.writeText(issuedToken)}
              >
                Copy
              </Button>
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <Label htmlFor="token-secret">
                  {tAny("serviceAccountTokenSecret")}
                </Label>
                <Input
                  id="token-secret"
                  type="password"
                  value={tokenSecret}
                  onChange={(e) => setTokenSecret(e.target.value)}
                  placeholder="Min 8 characters"
                />
              </div>
              <PermissionGate permission={PERMISSIONS.INTEGRATIONS_MANAGE}>
                <Button
                  disabled={tokenSecret.length < 8 || issueToken.isPending}
                  onClick={() =>
                    issueToken.mutate(
                      { secret: tokenSecret },
                      {
                        onSuccess: (result) => {
                          setIssuedToken(result.token);
                        },
                        onError: () => {
                          getHandlers({
                            successTitle: "",
                          }).onError(new Error("Token issue failed"));
                        },
                      },
                    )
                  }
                >
                  {tAny("serviceAccountIssueToken")}
                </Button>
              </PermissionGate>
            </>
          )}
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
