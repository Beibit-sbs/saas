"use client";

import { DollarSign, TrendingUp, AlertCircle } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatCurrencyAmount } from "@/shared/utils/format";
import {
  useBillingPlans,
  useTenantBillingState,
  useTenantDelinquencyDashboard,
} from "@/modules/billing/hooks";
import { useTenantLocale } from "@/modules/currency-localization/hooks";
import Link from "next/link";

export default function BillingIndexPage() {
  const { hasPermission } = usePermissions();
  const tenantId = 1;

  const plansQuery = useBillingPlans();
  const stateQuery = useTenantBillingState(tenantId);
  const delinquencyQuery = useTenantDelinquencyDashboard(tenantId);
  const localeQuery = useTenantLocale(tenantId);

  if (!hasPermission(PERMISSIONS.BILLING_READ)) {
    return <AccessDenied />;
  }

  const hasError = Boolean(plansQuery.error || stateQuery.error || delinquencyQuery.error);
  const isLoading = plansQuery.isLoading || stateQuery.isLoading || delinquencyQuery.isLoading;

  if (hasError) {
    return (
      <ErrorState
        title="Billing data unavailable"
        message="Could not load billing summary."
        onRetry={() => {
          void plansQuery.refetch();
          void stateQuery.refetch();
          void delinquencyQuery.refetch();
        }}
      />
    );
  }

  const plans = plansQuery.data ?? [];
  const activePlans = plans.filter((plan) => plan.active).length;
  const billingState = stateQuery.data;
  const dashboard = delinquencyQuery.data;
  const localeProfile = localeQuery.data;

  const currentPlanLabel = billingState?.plan_code
    ? billingState.plan_code.toUpperCase()
    : "No plan";
  const totalOverdueLabel = formatCurrencyAmount(
    dashboard ? dashboard.total_overdue_cents / 100 : 0,
    {
      currencyCode: localeProfile?.currency_code ?? "USD",
      languageCode: localeProfile?.language_code ?? "en",
    },
  );
  const openDelinquency = dashboard?.open_total ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Billing"
        description="Manage plans, subscriptions, usage, and payment status"
        icon={DollarSign}
      />

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Plans</p>
              <p className="text-2xl font-bold">{isLoading ? "Loading..." : activePlans}</p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Current Plan</p>
              <p className="text-2xl font-bold">{isLoading ? "Loading..." : currentPlanLabel}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Overdue</p>
              <p className="text-2xl font-bold">{isLoading ? "Loading..." : totalOverdueLabel}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Tenant currency: {localeProfile?.currency_code ?? "USD"}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Open Delinquency</p>
              <p className="text-2xl font-bold">{isLoading ? "Loading..." : openDelinquency}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </Card>
      </div>

      {/* Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link href="/console/billing/plans">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">Plans</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Create and manage billing plans with custom features and pricing
                </p>
              </div>
              <Button variant="ghost" size="sm">→</Button>
            </div>
          </Card>
        </Link>

        <Link href="/console/billing/subscriptions">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">Subscriptions</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Monitor tenant subscriptions, plan changes, and account status
                </p>
              </div>
              <Button variant="ghost" size="sm">→</Button>
            </div>
          </Card>
        </Link>

        <Link href="/console/billing/usage">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">Usage</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Track quotas, consumption, and billing metrics across tenants
                </p>
              </div>
              <Button variant="ghost" size="sm">→</Button>
            </div>
          </Card>
        </Link>

        <Link href="/console/billing/delinquency">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">Delinquency</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Manage overdue invoices, dunning policies, and payment reminders
                </p>
              </div>
              <Button variant="ghost" size="sm">→</Button>
            </div>
          </Card>
        </Link>
      </div>

      {/* Recent Activity Placeholder */}
      <Card className="p-6">
        <h3 className="font-semibold mb-4">Recent Billing Activity</h3>
        <p className="text-sm text-muted-foreground">
          Detailed activity logs and audit trail available in activity section
        </p>
      </Card>
    </div>
  );
}
