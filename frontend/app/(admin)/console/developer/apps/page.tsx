"use client";

import { useState } from "react";
import { Code2, KeyRound, PlugZap, Activity } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/ui/empty-state";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Skeleton } from "@/shared/ui/skeleton";
import {
  useCreateDeveloperApp,
  useDeveloperAppInstallations,
  useDeveloperAppLogs,
  useDeveloperApps,
} from "@/modules/platform/developer/use-developer";

export default function DeveloperAppsPage() {
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [description, setDescription] = useState("");
  const [scopes, setScopes] = useState("students.read,enrollments.read,analytics.read");
  const [latestSecret, setLatestSecret] = useState<string | null>(null);

  const apps = useDeveloperApps();
  const installations = useDeveloperAppInstallations(selectedAppId);
  const logs = useDeveloperAppLogs(selectedAppId);
  const createApp = useCreateDeveloperApp();

  const selectedApp = (apps.data ?? []).find((item) => item.id === selectedAppId) ?? null;

  return (
    <RequirePermission
      permission={PERMISSIONS.DEVELOPER_PLATFORM_READ}
      message="You need developer platform read permission to access this panel."
    >
      <div className="space-y-6" data-testid="developer-apps-page">
        <PageHeader
          title="Developer Apps"
          description="Manage public API clients, installations, and usage visibility for external integrations."
          icon={Code2}
        />

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-lg border bg-card p-4 space-y-3 lg:col-span-1" data-testid="developer-app-create-panel">
            <p className="text-sm font-medium">Create Developer App</p>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="App name" />
            <Input value={ownerEmail} onChange={(e) => setOwnerEmail(e.target.value)} placeholder="owner@example.com" />
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
            <Input value={scopes} onChange={(e) => setScopes(e.target.value)} placeholder="students.read,analytics.read" />
            <Button
              data-testid="developer-app-create-btn"
              disabled={!name.trim() || !ownerEmail.trim() || createApp.isPending}
              onClick={async () => {
                const created = await createApp.mutateAsync({
                  name: name.trim(),
                  owner_email: ownerEmail.trim(),
                  description: description.trim(),
                  scopes: scopes.split(",").map((item) => item.trim()).filter(Boolean),
                });
                setLatestSecret(created.app_secret);
                setSelectedAppId(created.id);
                setName("");
                setOwnerEmail("");
                setDescription("");
              }}
            >
              <KeyRound className="mr-2 h-4 w-4" />
              Create App
            </Button>
            {latestSecret && (
              <div className="rounded border p-3 text-xs" data-testid="developer-app-secret-box">
                <p className="font-medium">Latest secret</p>
                <p className="font-mono break-all mt-1">{latestSecret}</p>
              </div>
            )}
          </div>

          <div className="rounded-lg border bg-card p-4 space-y-3 lg:col-span-2">
            <p className="text-sm font-medium">Registered Apps</p>

            <div className="space-y-2" data-testid="developer-app-list">
              {apps.isLoading ? (
                <div className="space-y-2" aria-label="Loading apps">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : apps.isError ? (
                <ErrorState title="Failed to load developer apps" onRetry={() => void apps.refetch()} />
              ) : (apps.data ?? []).length === 0 ? (
                <EmptyState
                  title="No developer apps yet"
                  description="Create the first developer app to start external integrations."
                />
              ) : (
                (apps.data ?? []).map((app) => (
                  <button
                    key={app.id}
                    type="button"
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      selectedAppId === app.id ? "border-primary bg-primary/5" : "hover:bg-muted/50"
                    }`}
                    onClick={() => setSelectedAppId(app.id)}
                    data-testid={`developer-app-row-${app.id}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="space-y-1">
                        <p className="font-medium text-sm">{app.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">{app.app_key}</p>
                      </div>
                      <Badge variant={app.status === "active" ? "default" : "secondary"}>{app.status}</Badge>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {selectedApp && (
          <div className="grid gap-6 lg:grid-cols-2" data-testid={`developer-app-detail-${selectedApp.id}`}>
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <div className="flex items-center gap-2">
                <PlugZap className="h-4 w-4 text-muted-foreground" />
                <p className="font-medium">Installations</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedApp.scopes.map((scope) => (
                  <Badge key={scope} variant="outline">{scope}</Badge>
                ))}
              </div>
              {installations.isLoading ? (
                <div className="space-y-2" aria-label="Loading installations">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : installations.isError ? (
                <ErrorState title="Failed to load installations" onRetry={() => void installations.refetch()} />
              ) : (
                <div className="space-y-2" data-testid="developer-app-installations">
                  {(installations.data ?? []).length === 0 ? (
                    <EmptyState
                      title="No installations"
                      description="This app has not been installed into any tenant yet."
                    />
                  ) : (
                    (installations.data ?? []).map((item) => (
                      <div key={item.id} className="rounded border p-3 text-sm">
                        <p>Tenant #{item.tenant_id}</p>
                        <p className="text-xs text-muted-foreground">Installed by {item.installed_by}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            <div className="rounded-lg border bg-card p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <p className="font-medium">API Usage Logs</p>
              </div>
              {logs.isLoading ? (
                <div className="space-y-2" aria-label="Loading logs">
                  <Skeleton className="h-14 w-full" />
                  <Skeleton className="h-14 w-full" />
                </div>
              ) : logs.isError ? (
                <ErrorState title="Failed to load API logs" onRetry={() => void logs.refetch()} />
              ) : (
                <div className="space-y-2" data-testid="developer-app-logs">
                  {(logs.data ?? []).length === 0 ? (
                    <EmptyState
                      title="No API usage logs"
                      description="Usage records will appear after the first API calls from this app."
                    />
                  ) : (
                    (logs.data ?? []).map((item) => (
                      <div key={item.id} className="rounded border p-3 text-sm">
                        <p className="font-mono text-xs">{item.endpoint}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {item.status_code} • {item.latency_ms}ms • tenant {item.tenant_id}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </RequirePermission>
  );
}