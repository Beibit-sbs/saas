"use client";

import { useState } from "react";
import { CreditCard, RefreshCw, ArrowLeftRight } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useBillingPlans,
  useTenantBillingState,
  useAssignBillingSubscription,
  useChangeBillingPlan,
  useTransitionBillingSubscription,
} from "@/modules/billing/hooks";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";

interface TenantRecord {
  id: number;
  slug: string;
  name: string;
  status: string;
}

interface TenantListResponse {
  tenants: TenantRecord[];
}

function useTenants() {
  return useQuery({
    queryKey: ["tenants"],
    queryFn: () => apiGet<TenantListResponse>("/api/admin/tenants"),
  });
}

const STATUS_COLORS: Record<string, "default" | "success" | "warning" | "destructive"> = {
  active: "success",
  trialing: "warning",
  suspended: "destructive",
  cancelled: "destructive",
  past_due: "warning",
};

export default function BillingSubscriptionsPage() {
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [planCode, setPlanCode] = useState("");
  const [transitionStatus, setTransitionStatus] = useState("");

  const { data: tenantsData, isLoading: tenantsLoading, error: tenantsError } = useTenants();
  const { data: plansData } = useBillingPlans();
  const {
    data: billingState,
    isLoading: stateLoading,
    error: stateError,
    refetch,
  } = useTenantBillingState(selectedTenantId ?? 0);

  const assignPlan = useAssignBillingSubscription(selectedTenantId ?? 0);
  const changePlan = useChangeBillingPlan(selectedTenantId ?? 0);
  const transitionSub = useTransitionBillingSubscription(selectedTenantId ?? 0);
  const { getHandlers } = useMutationFeedback();

  if (tenantsError) {
    return (
      <ErrorState
        title="Failed to load tenants"
        message={
          tenantsError instanceof Error
            ? tenantsError.message
            : "An unexpected error occurred while loading tenants."
        }
      />
    );
  }

  const tenants = tenantsData?.tenants ?? [];
  const plans = plansData ?? [];

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Subscriptions"
          description="View and manage tenant billing subscriptions and plan assignments"
          icon={CreditCard}
        />

        {/* Tenant Selector */}
        <Card className="p-6">
          <Label className="text-sm font-medium mb-2 block">Select Tenant</Label>
          <div className="flex gap-3 flex-wrap">
            {tenantsLoading ? (
              <span className="text-sm text-muted-foreground">Loading tenants…</span>
            ) : (
              tenants.map((t) => (
                <Button
                  key={t.id}
                  variant={selectedTenantId === t.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedTenantId(t.id)}
                >
                  {t.name}
                </Button>
              ))
            )}
          </div>
        </Card>

        {/* Billing State */}
        {selectedTenantId && (
          <>
            {stateLoading && (
              <Card className="p-6">
                <span className="text-sm text-muted-foreground">Loading billing state…</span>
              </Card>
            )}
            {stateError && (
              <ErrorState
                title="Failed to load billing state"
                message={
                  stateError instanceof Error
                    ? stateError.message
                    : "An unexpected error occurred while loading billing state."
                }
              />
            )}
            {billingState && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Current State */}
                <Card className="p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Current Subscription</h3>
                    <Button variant="ghost" size="sm" onClick={() => refetch()}>
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Plan</span>
                      <span className="font-medium">{billingState.plan_code}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant={STATUS_COLORS[billingState.subscription_status] ?? "default"}>
                        {billingState.subscription_status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Billing State</span>
                      <span>{billingState.billing_state}</span>
                    </div>
                    {billingState.period_start && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Period</span>
                        <span>
                          {new Date(billingState.period_start).toLocaleDateString()} –{" "}
                          {billingState.period_end
                            ? new Date(billingState.period_end).toLocaleDateString()
                            : "—"}
                        </span>
                      </div>
                    )}
                    {billingState.next_plan_code && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Next Plan</span>
                        <span>{billingState.next_plan_code}</span>
                      </div>
                    )}
                  </div>
                </Card>

                {/* Usage vs Limits */}
                <Card className="p-6 space-y-3">
                  <h3 className="font-semibold">Usage / Limits</h3>
                  {Object.keys(billingState.limits).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No limits configured</p>
                  ) : (
                    <div className="space-y-2 text-sm">
                      {Object.entries(billingState.limits).map(([metric, limit]) => {
                        const used = billingState.usage[metric] ?? 0;
                        const pct = limit > 0 ? Math.round((used / limit) * 100) : 0;
                        return (
                          <div key={metric}>
                            <div className="flex justify-between mb-1">
                              <span className="text-muted-foreground">{metric}</span>
                              <span>
                                {used} / {limit}
                                <span className="text-muted-foreground ml-1">({pct}%)</span>
                              </span>
                            </div>
                            <div className="h-1.5 bg-muted rounded-full">
                              <div
                                className={`h-full rounded-full ${pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-yellow-500" : "bg-green-500"}`}
                                style={{ width: `${Math.min(pct, 100)}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Card>
              </div>
            )}

            {/* Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Assign / Change Plan */}
              <Card className="p-6 space-y-3">
                <h3 className="font-semibold flex items-center gap-2">
                  <ArrowLeftRight className="w-4 h-4" />
                  Change Plan
                </h3>
                <div className="space-y-2">
                  <Label>New Plan</Label>
                  <select
                    className="w-full border rounded px-3 py-2 text-sm bg-background"
                    value={planCode}
                    onChange={(e) => setPlanCode(e.target.value)}
                  >
                    <option value="">— select plan —</option>
                    {plans
                      .filter((p) => p.active)
                      .map((p) => (
                        <option key={p.code} value={p.code}>
                          {p.name} ({p.code})
                        </option>
                      ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    disabled={!planCode || assignPlan.isPending}
                    onClick={() =>
                      assignPlan.mutate(
                        { plan_code: planCode },
                        getHandlers({ successTitle: "Subscription assigned" }),
                      )
                    }
                  >
                    Assign
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!planCode || changePlan.isPending}
                    onClick={() =>
                      changePlan.mutate(
                        { plan_code: planCode },
                        getHandlers({ successTitle: "Plan changed" }),
                      )
                    }
                  >
                    Schedule Change
                  </Button>
                </div>
              </Card>

              {/* Transition Status */}
              <Card className="p-6 space-y-3">
                <h3 className="font-semibold">Transition Status</h3>
                <div className="space-y-2">
                  <Label>Target Status</Label>
                  <select
                    className="w-full border rounded px-3 py-2 text-sm bg-background"
                    value={transitionStatus}
                    onChange={(e) => setTransitionStatus(e.target.value)}
                  >
                    <option value="">— select status —</option>
                    {["active", "trialing", "suspended", "cancelled", "past_due"].map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  size="sm"
                  disabled={!transitionStatus || transitionSub.isPending}
                  onClick={() =>
                    transitionSub.mutate(
                      { status: transitionStatus },
                      getHandlers({ successTitle: "Status updated" }),
                    )
                  }
                >
                  Apply
                </Button>
              </Card>
            </div>
          </>
        )}

        {!selectedTenantId && !tenantsLoading && (
          <Card className="p-6">
            <p className="text-sm text-muted-foreground text-center">
              Select a tenant above to view and manage their subscription.
            </p>
          </Card>
        )}
      </div>
    </RequirePermission>
  );
}
