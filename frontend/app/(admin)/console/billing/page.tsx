"use client";

import { DollarSign, TrendingUp, AlertCircle } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import Link from "next/link";

export default function BillingIndexPage() {
  const { hasPermission } = usePermissions();

  if (!hasPermission(PERMISSIONS.BILLING_READ)) {
    return <AccessDenied />;
  }

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
              <p className="text-2xl font-bold">3</p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Monthly Revenue</p>
              <p className="text-2xl font-bold">$12.5K</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Subscriptions</p>
              <p className="text-2xl font-bold">47</p>
            </div>
            <DollarSign className="w-8 h-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Delinquent</p>
              <p className="text-2xl font-bold">2</p>
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
