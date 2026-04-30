"use client";

import { useState } from "react";
import { AlertCircle, Bell, CheckCircle, ChevronUp } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useTenantDelinquencyRecords,
  useTenantDelinquencyDashboard,
  useTenantDunningPolicy,
  useEscalateDelinquency,
  useResolveDelinquency,
  useSendDelinquencyReminder,
} from "@/modules/billing/hooks";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { BillingDelinquencyRecord } from "@/modules/billing/types";

interface TenantRecord {
  id: number;
  slug: string;
  name: string;
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

const STATUS_COLORS: Record<string, "default" | "warning" | "destructive" | "success"> = {
  open: "warning",
  escalated: "destructive",
  resolved: "success",
  closed: "default",
};

function formatCents(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

export default function BillingDelinquencyPage() {
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [resolving, setResolving] = useState<number | null>(null);
  const [resolution, setResolution] = useState("");

  const { data: tenantsData, isLoading: tenantsLoading } = useTenants();

  const { data: dashboardData } = useTenantDelinquencyDashboard(selectedTenantId ?? 0);
  const { data: policyData } = useTenantDunningPolicy(selectedTenantId ?? 0);
  const {
    data: recordsData,
    isLoading: recordsLoading,
    error: recordsError,
  } = useTenantDelinquencyRecords(selectedTenantId ?? 0, statusFilter || undefined);

  const escalate = useEscalateDelinquency(selectedTenantId ?? 0);
  const resolve = useResolveDelinquency(selectedTenantId ?? 0);
  const remind = useSendDelinquencyReminder(selectedTenantId ?? 0);
  const { getHandlers } = useMutationFeedback();

  const tenants = tenantsData?.tenants ?? [];
  const records = recordsData?.items ?? [];
  const dashboard = dashboardData;
  const policy = policyData;

  const columns: Column<BillingDelinquencyRecord>[] = [
    { key: "invoice_id", header: "Invoice", cell: (r) => r.invoice_id },
    {
      key: "status",
      header: "Status",
      cell: (r) => (
        <Badge variant={STATUS_COLORS[r.status] ?? "default"}>{r.status}</Badge>
      ),
    },
    {
      key: "amount_cents",
      header: "Amount",
      cell: (r) => formatCents(r.amount_cents),
    },
    {
      key: "opened_at",
      header: "Opened",
      cell: (r) => new Date(r.opened_at).toLocaleDateString(),
    },
    {
      key: "reminder_count",
      header: "Reminders",
      cell: (r) => r.reminder_count,
    },
    {
      key: "id",
      header: "Actions",
      cell: (r) => (
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="ghost"
            disabled={remind.isPending}
            onClick={() =>
              remind.mutate(
                { recordId: r.id },
                getHandlers({ successTitle: "Reminder sent" }),
              )
            }
            title="Send reminder"
          >
            <Bell className="w-3 h-3" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={escalate.isPending || r.status === "escalated" || r.status === "resolved"}
            onClick={() =>
              escalate.mutate(
                { recordId: r.id },
                getHandlers({ successTitle: "Record escalated" }),
              )
            }
            title="Escalate"
          >
            <ChevronUp className="w-3 h-3" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={r.status === "resolved"}
            onClick={() => {
              setResolving(r.id);
              setResolution("");
            }}
            title="Resolve"
          >
            <CheckCircle className="w-3 h-3" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Delinquency"
          description="Manage overdue invoices, dunning policies, and payment reminders"
          icon={AlertCircle}
        />

        {/* Tenant Selector */}
        <Card className="p-6">
          <Label className="text-sm font-medium mb-2 block">Select Tenant</Label>
          <div className="flex gap-3 flex-wrap">
            {tenantsLoading ? (
              <span className="text-sm text-muted-foreground">Loading…</span>
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

        {selectedTenantId && (
          <>
            {/* Dashboard Summary */}
            {dashboard && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="p-4">
                  <p className="text-xs text-muted-foreground">Total Records</p>
                  <p className="text-2xl font-bold">{dashboard.total}</p>
                </Card>
                <Card className="p-4">
                  <p className="text-xs text-muted-foreground">Open</p>
                  <p className="text-2xl font-bold text-yellow-600">{dashboard.open_total}</p>
                </Card>
                <Card className="p-4">
                  <p className="text-xs text-muted-foreground">Total Overdue</p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatCents(dashboard.total_overdue_cents)}
                  </p>
                </Card>
                <Card className="p-4">
                  <p className="text-xs text-muted-foreground">By Status</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {Object.entries(dashboard.by_status).map(([s, n]) => (
                      <span key={s} className="text-xs">
                        {s}: {n}
                      </span>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {/* Filter */}
            <div className="flex items-center gap-3">
              <Label className="text-sm">Filter by status:</Label>
              {["", "open", "escalated", "resolved", "closed"].map((s) => (
                <Button
                  key={s}
                  size="sm"
                  variant={statusFilter === s ? "default" : "outline"}
                  onClick={() => setStatusFilter(s)}
                >
                  {s === "" ? "All" : s}
                </Button>
              ))}
            </div>

            {/* Records Table */}
            {recordsError ? (
              <ErrorState
                title="Failed to load delinquency records"
                message={
                  recordsError instanceof Error
                    ? recordsError.message
                    : "An unexpected error occurred while loading data."
                }
              />
            ) : (
              <DataTable
                columns={columns}
                data={records}
                isLoading={recordsLoading}
                getRowKey={(record) => String(record.id)}
                emptyDescription="No delinquency records found"
              />
            )}

            {/* Dunning Policy */}
            {policy && (
              <Card className="p-6">
                <h3 className="font-semibold mb-3">Dunning Policy</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Grace period</span>
                    <p className="font-medium">{policy.grace_period_days} days</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Overdue after</span>
                    <p className="font-medium">{policy.overdue_period_days} days</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Suspension after</span>
                    <p className="font-medium">{policy.suspension_period_days} days</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Auto-cancel after</span>
                    <p className="font-medium">{policy.auto_cancel_after_days} days</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Reminder schedule</span>
                    <p className="font-medium">days {policy.reminder_schedule.join(", ")}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Require approval for reactivation</span>
                    <p className="font-medium">
                      {policy.require_approval_for_reactivation ? "Yes" : "No"}
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </>
        )}

        {/* Resolve Dialog */}
        {resolving !== null && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="p-6 w-96 space-y-4">
              <h3 className="font-semibold">Resolve Record #{resolving}</h3>
              <div>
                <Label>Resolution</Label>
                <select
                  className="w-full border rounded px-3 py-2 text-sm bg-background mt-1"
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                >
                  <option value="">— select —</option>
                  {["paid", "waived", "written_off", "plan_change", "other"].map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setResolving(null)}>
                  Cancel
                </Button>
                <Button
                  disabled={!resolution || resolve.isPending}
                  onClick={() => {
                    resolve.mutate(
                      { recordId: resolving, resolution },
                      {
                        ...getHandlers({ successTitle: "Record resolved" }),
                        onSuccess: (result) => {
                          getHandlers({ successTitle: "Record resolved" }).onSuccess(result);
                          setResolving(null);
                        },
                      },
                    );
                  }}
                >
                  Resolve
                </Button>
              </div>
            </Card>
          </div>
        )}

        {!selectedTenantId && !tenantsLoading && (
          <Card className="p-6">
            <p className="text-sm text-muted-foreground text-center">
              Select a tenant to view delinquency records.
            </p>
          </Card>
        )}
      </div>
    </RequirePermission>
  );
}
