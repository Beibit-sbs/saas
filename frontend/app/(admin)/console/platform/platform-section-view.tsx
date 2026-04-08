"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMutation } from "@tanstack/react-query";
import { RequireAdminRole } from "@/shared/ui/require-admin-role";
import { PageHeader } from "@/shared/ui/page-header";
import { Button } from "@/shared/ui/button";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { StatusBadge } from "@/shared/ui/status-badge";
import { apiDelete, apiGet, apiPost, apiPut } from "@/shared/api/client";
import { TAB_TO_PLATFORM_SECTION, type PlatformConsoleTab } from "./platform-sections";

interface TenantRecord {
  id: number;
  slug: string;
  name: string;
  status: string;
  plan_id: number;
}

interface PlanRecord {
  id: number;
  code: string;
  name: string;
  active: boolean;
}

interface BillingState {
  tenant_id: number;
  plan_code: string;
  next_plan_code?: string | null;
  subscription_status: string;
  billing_state: string;
  period_start?: string | null;
  period_end?: string | null;
  limits: Record<string, number>;
  usage: Record<string, number>;
}

interface FeatureFlagRecord {
  key: string;
  enabled: boolean;
  description?: string | null;
  scope: string;
}

interface ServiceAccountRecord {
  account_id: string;
  name: string;
  permissions: string[];
  platform_global: boolean;
  active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

interface WebhookSubscriptionRecord {
  id: number;
  event_type: string;
  target_url: string;
  is_active: boolean;
}

interface WebhookDeliveryRecord {
  id: number;
  delivery_status: "pending" | "delivered" | "failed";
  event_type: string;
  retry_count: number;
  outbox_event_id: number;
  response_status_code: number | null;
  next_retry_at: string | null;
  last_error: string | null;
}

interface AutomationRuleRecord {
  id: number;
  name: string;
  event_type: string;
  is_active: boolean;
}

interface AutomationExecutionRecord {
  id: number;
  status: string;
  rule_id: number;
  event_id: number;
  result_json: Record<string, unknown>;
  error_message: string | null;
}

interface OpsSummaryResponse {
  queues: {
    retry_backlog: number | null;
    dead_webhooks: number | null;
    failed_webhooks: number | null;
    failed_automation_executions: number | null;
  };
}

interface AuditEventRecord {
  timestamp?: string;
  metadata?: {
    account_id?: string;
  };
}

function toDeliveryUiStatus(delivery: WebhookDeliveryRecord): "success" | "failed" | "retrying" {
  if (delivery.delivery_status === "delivered") return "success";
  if (delivery.delivery_status === "failed" && delivery.next_retry_at) return "retrying";
  return "failed";
}

function summarizeExecutionSideEffects(result: Record<string, unknown> | null | undefined): string {
  if (!result || typeof result !== "object") return "-";
  const keys = Object.keys(result);
  if (keys.length === 0) return "-";
  if ("actions_executed" in result) return `actions: ${String(result.actions_executed)}`;
  if ("notifications_sent" in result) return `notifications: ${String(result.notifications_sent)}`;
  if ("jobs_created" in result) return `jobs: ${String(result.jobs_created)}`;
  return keys.slice(0, 3).join(", ");
}

interface PlatformSectionViewProps {
  section: PlatformConsoleTab;
}

const EXECUTIVE_MODE_STORAGE_KEY = "admin.executiveMode";

const PLATFORM_TABS: Array<{ tab: PlatformConsoleTab; title: string }> = [
  { tab: "overview", title: "Overview" },
  { tab: "tenants", title: "Tenants" },
  { tab: "billing-plans", title: "Billing / Plans" },
  { tab: "usage-quotas", title: "Usage / Quotas" },
  { tab: "feature-flags", title: "Feature Flags" },
  { tab: "integrations", title: "Integrations / Webhooks" },
  { tab: "automation", title: "Automation" },
  { tab: "service-accounts", title: "Service Accounts" },
];

export function PlatformSectionView({ section }: PlatformSectionViewProps) {
  const router = useRouter();
  const [executiveMode, setExecutiveMode] = useState(false);
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [newServiceAccountName, setNewServiceAccountName] = useState("");
  const [newServiceAccountPermissions, setNewServiceAccountPermissions] = useState("admin.integrations.manage");
  const [newServiceAccountPlatformGlobal, setNewServiceAccountPlatformGlobal] = useState(false);
  const qc = useQueryClient();

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(EXECUTIVE_MODE_STORAGE_KEY);
    if (stored === "1") {
      setExecutiveMode(true);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(EXECUTIVE_MODE_STORAGE_KEY, executiveMode ? "1" : "0");
  }, [executiveMode]);

  const tenantsQuery = useQuery<{ tenants: TenantRecord[] }>({
    queryKey: ["platform-console", "tenants"],
    queryFn: () => apiGet<{ tenants: TenantRecord[] }>("/api/admin/tenants"),
    refetchInterval: 30_000,
  });

  const plansQuery = useQuery<{ plans: PlanRecord[] }>({
    queryKey: ["platform-console", "plans"],
    queryFn: () => apiGet<{ plans: PlanRecord[] }>("/platform/plans"),
    refetchInterval: 30_000,
  });

  const quotasQuery = useQuery<{ quotas: Array<{ plan_id: number; key: string; limit_value: number }> }>({
    queryKey: ["platform-console", "quotas"],
    queryFn: () => apiGet<{ quotas: Array<{ plan_id: number; key: string; limit_value: number }> }>("/platform/quotas"),
    refetchInterval: 30_000,
  });

  const featureFlagsQuery = useQuery<{ flags: FeatureFlagRecord[] }>({
    queryKey: ["platform-console", "feature-flags"],
    queryFn: () => apiGet<{ flags: FeatureFlagRecord[] }>("/api/admin/feature-flags"),
    refetchInterval: 30_000,
  });

  const integrationsQuery = useQuery<{ ldap: { enabled: boolean; configured: boolean }; ai_providers: Array<{ provider: string; configured: boolean }> }>({
    queryKey: ["platform-console", "integrations"],
    queryFn: () => apiGet<{ ldap: { enabled: boolean; configured: boolean }; ai_providers: Array<{ provider: string; configured: boolean }> }>("/api/admin/integrations/settings"),
    refetchInterval: 30_000,
  });

  const billingStateQuery = useQuery<BillingState>({
    queryKey: ["platform-console", "billing-state", selectedTenantId],
    queryFn: () => apiGet<BillingState>(`/platform/tenants/${selectedTenantId}/billing`),
    enabled: selectedTenantId !== null,
    refetchInterval: 30_000,
  });

  const webhookSubsQuery = useQuery<WebhookSubscriptionRecord[]>({
    queryKey: ["platform-console", "webhooks", "subs", selectedTenantId],
    queryFn: async () => {
      const data = await apiGet<WebhookSubscriptionRecord[]>(`/api/v1/admin/tenants/${selectedTenantId}/webhooks/subscriptions`);
      return Array.isArray(data) ? data : [];
    },
    enabled: selectedTenantId !== null,
    refetchInterval: 30_000,
  });

  const webhookDeliveriesQuery = useQuery<{ items: WebhookDeliveryRecord[] }>({
    queryKey: ["platform-console", "webhooks", "deliveries", selectedTenantId],
    queryFn: () => apiGet<{ items: WebhookDeliveryRecord[] }>(`/api/v1/admin/tenants/${selectedTenantId}/webhooks/deliveries`),
    enabled: selectedTenantId !== null,
    refetchInterval: 30_000,
  });

  const automationRulesQuery = useQuery<AutomationRuleRecord[]>({
    queryKey: ["platform-console", "automation", "rules", selectedTenantId],
    queryFn: () => apiGet<AutomationRuleRecord[]>("/api/bff/admin/platform/automation/rules", { tenant_id: selectedTenantId ?? undefined }),
    enabled: selectedTenantId !== null,
    refetchInterval: 30_000,
  });

  const automationExecutionsQuery = useQuery<AutomationExecutionRecord[]>({
    queryKey: ["platform-console", "automation", "executions", selectedTenantId],
    queryFn: () => apiGet<AutomationExecutionRecord[]>("/api/bff/admin/platform/automation/executions", { tenant_id: selectedTenantId ?? undefined }),
    enabled: selectedTenantId !== null,
    refetchInterval: 30_000,
  });

  const serviceAccountsQuery = useQuery<{ accounts: ServiceAccountRecord[] }>({
    queryKey: ["platform-console", "service-accounts"],
    queryFn: () => apiGet<{ accounts: ServiceAccountRecord[] }>("/api/admin/service-accounts"),
    refetchInterval: 30_000,
  });

  const opsSummaryQuery = useQuery<OpsSummaryResponse>({
    queryKey: ["platform-console", "ops-summary"],
    queryFn: () => apiGet<OpsSummaryResponse>("/api/v1/platform/ops/summary"),
    refetchInterval: 30_000,
  });

  const serviceAccountUsageQuery = useQuery<{ events: AuditEventRecord[] }>({
    queryKey: ["platform-console", "service-account-usage", selectedTenantId],
    queryFn: () =>
      apiGet<{ events: AuditEventRecord[] }>("/api/admin/audit/events", {
        action: "service_accounts.token.issue",
        tenant_id: selectedTenantId ?? undefined,
        limit: 500,
      }),
    enabled: selectedTenantId !== null,
    refetchInterval: 60_000,
  });

  const transitionSubscription = useMutation({
    mutationFn: (status: string) => apiPost(`/platform/tenants/${selectedTenantId}/billing/subscription/transition`, { status }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["platform-console", "billing-state", selectedTenantId] }),
  });

  const changePlan = useMutation({
    mutationFn: (planCode: string) => apiPost(`/platform/tenants/${selectedTenantId}/billing/subscription/plan-change`, { plan_code: planCode, effective: "next_period" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["platform-console", "billing-state", selectedTenantId] }),
  });

  const updateTenantStatus = useMutation({
    mutationFn: ({ tenantId, status }: { tenantId: number; status: string }) => apiPut(`/api/admin/tenants/${tenantId}`, { status }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["platform-console", "tenants"] }),
  });

  const deactivateTenant = useMutation({
    mutationFn: (tenantId: number) => apiDelete(`/api/admin/tenants/${tenantId}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["platform-console", "tenants"] });
      void qc.invalidateQueries({ queryKey: ["platform-console", "billing-state", selectedTenantId] });
    },
  });

  const toggleFeatureFlag = useMutation({
    mutationFn: (flag: FeatureFlagRecord) =>
      apiPost("/api/admin/feature-flags", {
        key: flag.key,
        enabled: !flag.enabled,
        description: flag.description ?? "",
        scope: flag.scope,
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["platform-console", "feature-flags"] }),
  });

  const deactivateWebhook = useMutation({
    mutationFn: (subscriptionId: number) => apiPost(`/api/v1/admin/webhooks/subscriptions/${subscriptionId}/deactivate`),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["platform-console", "webhooks", "subs", selectedTenantId] }),
  });

  const revokeServiceAccount = useMutation({
    mutationFn: (accountId: string) => apiPost(`/api/admin/service-accounts/${accountId}/revoke`),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["platform-console", "service-accounts"] }),
  });

  const createServiceAccount = useMutation({
    mutationFn: (payload: { name: string; permissions: string[]; platform_global: boolean }) =>
      apiPost<{ account: ServiceAccountRecord }>("/api/admin/service-accounts", payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["platform-console", "service-accounts"] });
      setNewServiceAccountName("");
    },
  });

  const retryFailedWebhookDeliveries = useMutation({
    mutationFn: async (limit: number) => {
      const response = await fetch("/api/admin/platform/internal/webhooks/retry-failed", {
        method: "POST",
        headers: { "content-type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ limit }),
      });
      if (!response.ok) throw new Error("webhook retry failed");
      return response.json();
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["platform-console", "webhooks", "deliveries", selectedTenantId] });
      void qc.invalidateQueries({ queryKey: ["platform-console", "ops-summary"] });
    },
  });

  const manualAutomationTrigger = useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/admin/platform/internal/automation/trigger", {
        method: "POST",
        headers: { "content-type": "application/json" },
        credentials: "include",
      });
      if (!response.ok) throw new Error("manual automation trigger failed");
      return response.json();
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["platform-console", "automation", "executions", selectedTenantId] });
      void qc.invalidateQueries({ queryKey: ["platform-console", "webhooks", "deliveries", selectedTenantId] });
      void qc.invalidateQueries({ queryKey: ["platform-console", "ops-summary"] });
    },
  });

  const tenants = useMemo(() => tenantsQuery.data?.tenants ?? [], [tenantsQuery.data?.tenants]);
  const plans = useMemo(() => plansQuery.data?.plans ?? [], [plansQuery.data?.plans]);
  const quotas = useMemo(() => quotasQuery.data?.quotas ?? [], [quotasQuery.data?.quotas]);
  const featureFlags = useMemo(() => featureFlagsQuery.data?.flags ?? [], [featureFlagsQuery.data?.flags]);
  const serviceAccounts = useMemo(() => serviceAccountsQuery.data?.accounts ?? [], [serviceAccountsQuery.data?.accounts]);
  const webhookSubscriptions = useMemo(() => webhookSubsQuery.data ?? [], [webhookSubsQuery.data]);
  const webhookDeliveries = useMemo(() => webhookDeliveriesQuery.data?.items ?? [], [webhookDeliveriesQuery.data?.items]);
  const automationRules = useMemo(() => automationRulesQuery.data ?? [], [automationRulesQuery.data]);
  const automationExecutions = useMemo(() => automationExecutionsQuery.data ?? [], [automationExecutionsQuery.data]);
  const serviceAccountUsageById = useMemo(() => {
    const usage = new Map<string, { issues: number; lastIssuedAt: string | null }>();
    const events = serviceAccountUsageQuery.data?.events ?? [];
    for (const event of events) {
      const accountId = String(event.metadata?.account_id ?? "").trim();
      if (!accountId) continue;
      const prev = usage.get(accountId) ?? { issues: 0, lastIssuedAt: null };
      const ts = typeof event.timestamp === "string" ? event.timestamp : null;
      usage.set(accountId, {
        issues: prev.issues + 1,
        lastIssuedAt: !prev.lastIssuedAt || (ts && ts > prev.lastIssuedAt) ? ts : prev.lastIssuedAt,
      });
    }
    return usage;
  }, [serviceAccountUsageQuery.data?.events]);

  useEffect(() => {
    if (selectedTenantId !== null) return;
    if (tenants.length === 0) return;
    setSelectedTenantId(Number(tenants[0].id));
  }, [selectedTenantId, tenants]);

  const selectedTenant = useMemo(
    () => tenants.find((item) => Number(item.id) === Number(selectedTenantId)) ?? null,
    [tenants, selectedTenantId],
  );

  const handleTabChange = useCallback((nextTab: PlatformConsoleTab) => {
    router.push(`/console/platform/${TAB_TO_PLATFORM_SECTION[nextTab]}`);
  }, [router]);

  const renderSection = () => {
    if (section === "overview") {
      return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4" data-testid="platform-console-overview">
          <Card><CardHeader><CardTitle>Tenants</CardTitle></CardHeader><CardContent>{tenants.length}</CardContent></Card>
          <Card><CardHeader><CardTitle>Plans</CardTitle></CardHeader><CardContent>{plans.length}</CardContent></Card>
          <Card><CardHeader><CardTitle>Feature Flags</CardTitle></CardHeader><CardContent>{featureFlags.length}</CardContent></Card>
          <Card><CardHeader><CardTitle>Service Accounts</CardTitle></CardHeader><CardContent>{serviceAccounts.length}</CardContent></Card>
        </div>
      );
    }

    if (section === "tenants") {
      return (
        <Card data-testid="platform-console-tenants">
          <CardHeader>
            <CardTitle>Tenant List</CardTitle>
            <CardDescription>List view, status, plan and key actions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {tenants.map((tenant) => (
              <div key={tenant.id} className="rounded border p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{tenant.name}</div>
                    <div className="text-xs text-muted-foreground">{tenant.slug}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={tenant.status} />
                    <span className="text-xs text-muted-foreground">plan #{tenant.plan_id}</span>
                    <Button size="sm" variant="outline" onClick={() => setSelectedTenantId(tenant.id)}>Details</Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => updateTenantStatus.mutate({ tenantId: tenant.id, status: tenant.status === "active" ? "suspended" : "active" })}
                    >
                      {tenant.status === "active" ? "Suspend" : "Activate"}
                    </Button>
                    {tenant.id !== 1 && tenant.status !== "inactive" ? (
                      <ConfirmActionDialog
                        title="Deactivate tenant?"
                        description={`${tenant.name} will be moved to inactive status.`}
                        variant="destructive"
                        loading={deactivateTenant.isPending}
                        onConfirm={async () => {
                          await deactivateTenant.mutateAsync(tenant.id);
                        }}
                        trigger={<Button size="sm" variant="destructive">Deactivate</Button>}
                      />
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      );
    }

    if (section === "billing-plans") {
      const currentPlanCode = String(billingStateQuery.data?.plan_code || "");
      const nextPlan = plans.find((plan) => plan.code !== currentPlanCode);
      return (
        <div className="grid gap-4 lg:grid-cols-2" data-testid="platform-console-billing">
          <Card>
            <CardHeader>
              <CardTitle>Current Subscription</CardTitle>
              <CardDescription>Status and transitions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-sm">Tenant: <span className="font-medium">{selectedTenant?.name ?? "Unknown"}</span></div>
              <div className="text-sm">Plan: <span className="font-medium">{currentPlanCode || "Unknown"}</span></div>
              <div className="text-sm">Subscription status: <span className="font-medium">{billingStateQuery.data?.subscription_status ?? "Unknown"}</span></div>
              <div className="flex gap-2 pt-2">
                <Button size="sm" variant="outline" onClick={() => transitionSubscription.mutate("active")}>Set Active</Button>
                <Button size="sm" variant="outline" onClick={() => transitionSubscription.mutate("suspended")}>Set Suspended</Button>
                <Button size="sm" variant="outline" onClick={() => transitionSubscription.mutate("cancelled")}>Set Cancelled</Button>
              </div>
              {nextPlan ? (
                <Button size="sm" onClick={() => changePlan.mutate(nextPlan.code)}>Transition to {nextPlan.code}</Button>
              ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Plan Catalog</CardTitle>
              <CardDescription>List view and status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {plans.map((plan) => (
                <div key={plan.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <span>{plan.code} ({plan.name})</span>
                  <StatusBadge status={plan.active ? "active" : "inactive"} />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      );
    }

    if (section === "usage-quotas") {
      const limits = billingStateQuery.data?.limits ?? {};
      const usage = billingStateQuery.data?.usage ?? {};
      const keys = Array.from(new Set([...Object.keys(limits), ...Object.keys(usage)]));
      return (
        <Card data-testid="platform-console-usage-quotas">
          <CardHeader>
            <CardTitle>Usage / Quotas</CardTitle>
            <CardDescription>Usage counters, limits and enforcement-visible state</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-sm">Billing mode: <span className="font-medium">{billingStateQuery.data?.billing_state ?? "unknown"}</span></div>
            {keys.map((key) => (
              <div key={key} className="flex items-center justify-between rounded border p-2 text-sm">
                <span>{key}</span>
                <span>{usage[key] ?? 0} / {limits[key] ?? 0}</span>
              </div>
            ))}
            <div className="pt-2 text-xs text-muted-foreground">Quota rows loaded: {quotas.length}</div>
          </CardContent>
        </Card>
      );
    }

    if (section === "feature-flags") {
      return (
        <Card data-testid="platform-console-feature-flags">
          <CardHeader>
            <CardTitle>Feature Flags</CardTitle>
            <CardDescription>Flag list, status and scope</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {featureFlags.map((flag) => (
              <div key={flag.key} className="flex items-center justify-between rounded border p-2">
                <div>
                  <div className="text-sm font-medium">{flag.key}</div>
                  <div className="text-xs text-muted-foreground">scope: {flag.scope}</div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={flag.enabled ? "active" : "inactive"} />
                  <Button size="sm" variant="outline" onClick={() => toggleFeatureFlag.mutate(flag)}>
                    {flag.enabled ? "Turn Off" : "Turn On"}
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      );
    }

    if (section === "integrations") {
      return (
        <div className="grid gap-4 lg:grid-cols-2" data-testid="platform-console-integrations">
          <Card>
            <CardHeader>
              <CardTitle>Integrations</CardTitle>
              <CardDescription>Settings status and key visibility</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>LDAP: {integrationsQuery.data?.ldap?.enabled ? "enabled" : "disabled"} ({integrationsQuery.data?.ldap?.configured ? "configured" : "not configured"})</div>
              <div>AI providers: {(integrationsQuery.data?.ai_providers ?? []).length}</div>
              {(integrationsQuery.data?.ai_providers ?? []).map((provider) => (
                <div key={provider.provider} className="flex items-center justify-between rounded border p-2">
                  <span>{provider.provider}</span>
                  <StatusBadge status={provider.configured ? "active" : "inactive"} />
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Webhooks</CardTitle>
              <CardDescription>Subscriptions, deliveries, retry/dead visibility and manual controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="rounded border p-2 text-xs">
                <div>retry backlog: <span className="font-medium">{opsSummaryQuery.data?.queues.retry_backlog ?? 0}</span></div>
                <div>failed: <span className="font-medium">{opsSummaryQuery.data?.queues.failed_webhooks ?? 0}</span></div>
                <div>dead: <span className="font-medium">{opsSummaryQuery.data?.queues.dead_webhooks ?? 0}</span></div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => retryFailedWebhookDeliveries.mutate(20)}
                  disabled={retryFailedWebhookDeliveries.isPending}
                >
                  Retry Failed Deliveries
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => manualAutomationTrigger.mutate()}
                  disabled={manualAutomationTrigger.isPending}
                >
                  Manual Trigger
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">Subscriptions</div>
              {webhookSubscriptions.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <span>{item.event_type}</span>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={item.is_active ? "active" : "inactive"} />
                    {item.is_active ? (
                      <Button size="sm" variant="outline" onClick={() => deactivateWebhook.mutate(item.id)}>Deactivate</Button>
                    ) : null}
                  </div>
                </div>
              ))}
              <div className="pt-2 text-xs text-muted-foreground">Deliveries</div>
              {webhookDeliveries.slice(0, 10).map((delivery) => (
                <div key={delivery.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <div>
                    <div className="font-medium">{delivery.event_type}</div>
                    <div className="text-xs text-muted-foreground">
                      outbox #{delivery.outbox_event_id} | retries: {delivery.retry_count}
                      {delivery.next_retry_at ? ` | next retry: ${delivery.next_retry_at}` : ""}
                    </div>
                    {delivery.last_error ? <div className="text-xs text-red-700">{delivery.last_error}</div> : null}
                  </div>
                  <div className="text-right">
                    <div>{toDeliveryUiStatus(delivery)}</div>
                    <div className="text-xs text-muted-foreground">HTTP: {delivery.response_status_code ?? "-"}</div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      );
    }

    if (section === "automation") {
      return (
        <div className="grid gap-4 lg:grid-cols-2" data-testid="platform-console-automation">
          <Card>
            <CardHeader>
              <CardTitle>Rules</CardTitle>
              <CardDescription>List view and status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="rounded border p-2 text-xs">
                failed executions: <span className="font-medium">{opsSummaryQuery.data?.queues.failed_automation_executions ?? 0}</span>
              </div>
              {automationRules.map((rule) => (
                <div key={rule.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <span>{rule.name} ({rule.event_type})</span>
                  <StatusBadge status={rule.is_active ? "active" : "inactive"} />
                </div>
              ))}
              <Button
                size="sm"
                onClick={() => manualAutomationTrigger.mutate()}
                disabled={manualAutomationTrigger.isPending}
              >
                Manual Evaluate / Trigger
              </Button>
              <Button size="sm" variant="outline" onClick={() => router.push("/console/automation")}>Open Rules</Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Executions</CardTitle>
              <CardDescription>Execution status and details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {automationExecutions.slice(0, 10).map((execution) => (
                <div key={execution.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <div>
                    <div>rule #{execution.rule_id}</div>
                    <div className="text-xs text-muted-foreground">side effects: {summarizeExecutionSideEffects(execution.result_json)}</div>
                    {execution.error_message ? <div className="text-xs text-red-700">{execution.error_message}</div> : null}
                  </div>
                  <span>{execution.status === "completed" ? "success" : execution.status === "failed" ? "failed" : execution.status}</span>
                </div>
              ))}
              <Button size="sm" variant="outline" onClick={() => router.push("/console/automation/executions")}>Open Executions</Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return (
      <Card data-testid="platform-console-service-accounts">
        <CardHeader>
          <CardTitle>Service Accounts</CardTitle>
          <CardDescription>List, scope, active/revoked status, create/revoke and token usage</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid gap-2 rounded border p-3 md:grid-cols-4">
            <input
              value={newServiceAccountName}
              onChange={(event) => setNewServiceAccountName(event.target.value)}
              placeholder="Account name"
              className="rounded border px-2 py-1 text-sm"
            />
            <input
              value={newServiceAccountPermissions}
              onChange={(event) => setNewServiceAccountPermissions(event.target.value)}
              placeholder="permissions (comma separated)"
              className="rounded border px-2 py-1 text-sm md:col-span-2"
            />
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={newServiceAccountPlatformGlobal}
                onChange={(event) => setNewServiceAccountPlatformGlobal(event.target.checked)}
              />
              platform-global
            </label>
            <Button
              size="sm"
              className="md:col-span-4"
              onClick={() => {
                const permissions = newServiceAccountPermissions
                  .split(",")
                  .map((item) => item.trim())
                  .filter((item) => item.length > 0);
                if (!newServiceAccountName.trim() || permissions.length === 0) return;
                createServiceAccount.mutate({
                  name: newServiceAccountName.trim(),
                  permissions,
                  platform_global: newServiceAccountPlatformGlobal,
                });
              }}
              disabled={createServiceAccount.isPending}
            >
              Create Service Account
            </Button>
          </div>
          {serviceAccounts.map((account) => (
            <div key={account.account_id} className="flex items-center justify-between rounded border p-2 text-sm">
              <div>
                <div className="font-medium">{account.name}</div>
                <div className="text-xs text-muted-foreground">scope: {account.platform_global ? "platform" : "tenant"}</div>
                <div className="text-xs text-muted-foreground">permissions: {account.permissions.join(", ")}</div>
                <div className="text-xs text-muted-foreground">
                  token issues: {serviceAccountUsageById.get(account.account_id)?.issues ?? 0}
                  {serviceAccountUsageById.get(account.account_id)?.lastIssuedAt
                    ? ` | last: ${serviceAccountUsageById.get(account.account_id)?.lastIssuedAt}`
                    : ""}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={account.active ? "active" : "inactive"} />
                {account.active ? (
                  <Button size="sm" variant="outline" onClick={() => revokeServiceAccount.mutate(account.account_id)}>Revoke</Button>
                ) : null}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  };

  return (
    <RequireAdminRole>
      <div className="space-y-4" data-testid="platform-console-unified">
        <div className="flex justify-end">
          <button
            type="button"
            className="admin-presentation-toggle"
            onClick={() => setExecutiveMode((prev) => !prev)}
            aria-pressed={executiveMode}
            data-testid="canonical-executive-mode-toggle"
          >
            {executiveMode ? "Disable Executive Mode" : "Enable Executive Mode"}
          </button>
        </div>

        <PageHeader
          title="Unified Platform Console"
          description="Single control plane for tenants, billing, quotas, flags, integrations, automation and service accounts"
        />

        <div className="flex flex-wrap gap-2">
          {PLATFORM_TABS.map((item) => (
            <Button
              key={item.tab}
              size="sm"
              variant={item.tab === section ? "default" : "outline"}
              onClick={() => handleTabChange(item.tab)}
            >
              {item.title}
            </Button>
          ))}
        </div>

        <div className="rounded-md border p-3 text-sm">
          <span className="text-muted-foreground">Selected tenant: </span>
          <select
            value={selectedTenantId ?? ""}
            onChange={(event) => setSelectedTenantId(Number(event.target.value))}
            className="rounded border px-2 py-1"
          >
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
            ))}
          </select>
        </div>

        {renderSection()}
      </div>
    </RequireAdminRole>
  );
}
