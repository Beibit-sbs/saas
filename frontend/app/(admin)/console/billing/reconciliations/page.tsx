"use client";

import { useState } from "react";
import { Link2, CheckCircle, XCircle, Wand2 } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";

// ---------- types ----------

export interface Reconciliation {
  id: string;
  tenant_id: number;
  payment_id: string;
  invoice_id: string;
  status: "active" | "cancelled";
  notes: string;
  created_at: string;
  cancelled_at: string | null;
  cancel_reason: string | null;
}

interface ReconciliationListResponse {
  reconciliations: Reconciliation[];
}

interface TenantRecord {
  id: number;
  slug: string;
  name: string;
}

interface TenantListResponse {
  tenants: TenantRecord[];
}

// ---------- hooks ----------

function useTenants() {
  return useQuery({
    queryKey: ["tenants"],
    queryFn: () => apiGet<TenantListResponse>("/api/admin/tenants"),
  });
}

function useReconciliations(tenantId: number, statusFilter?: string) {
  return useQuery({
    queryKey: ["reconciliations", tenantId, statusFilter],
    queryFn: () =>
      apiGet<ReconciliationListResponse>(
        `/api/reconciliations?tenant_id=${tenantId}${statusFilter ? `&status=${statusFilter}` : ""}`
      ),
    enabled: tenantId > 0,
  });
}

function useCancelReconciliation() {
  return useMutation({
    mutationFn: ({
      reconciliationId,
      tenantId,
      reason,
    }: {
      reconciliationId: string;
      tenantId: number;
      reason: string;
    }) =>
      apiPost(`/api/reconciliations/${reconciliationId}/cancel`, {
        tenant_id: tenantId,
        reason,
      }),
  });
}

function useAutoReconcile() {
  return useMutation({
    mutationFn: ({
      tenantId,
      invoiceId,
    }: {
      tenantId: number;
      invoiceId: string;
    }) =>
      apiPost("/api/reconciliations/auto", {
        tenant_id: tenantId,
        invoice_id: invoiceId,
      }),
  });
}

// ---------- status badge ----------

function StatusBadge({ status }: { status: string }) {
  if (status === "active") {
    return <Badge variant="success">Active</Badge>;
  }
  return <Badge variant="secondary">Cancelled</Badge>;
}

// ---------- page ----------

export default function ReconciliationsPage() {
  const qc = useQueryClient();
  const { getHandlers } = useMutationFeedback();

  const [tenantId, setTenantId] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");

  // cancel modal
  const [cancelTarget, setCancelTarget] = useState<Reconciliation | null>(null);
  const [cancelReason, setCancelReason] = useState("");

  // auto-reconcile modal
  const [autoModalOpen, setAutoModalOpen] = useState(false);
  const [autoInvoiceId, setAutoInvoiceId] = useState("");

  const { data: tenantsData } = useTenants();
  const tenants = tenantsData?.tenants ?? [];

  const { data: recsData, error } = useReconciliations(
    tenantId,
    statusFilter || undefined
  );
  const recs = recsData?.reconciliations ?? [];

  const cancelMutation = useCancelReconciliation();
  const autoMutation = useAutoReconcile();

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ["reconciliations", tenantId] });

  function handleCancel() {
    if (!cancelTarget) return;
    cancelMutation.mutate(
      {
        reconciliationId: cancelTarget.id,
        tenantId,
        reason: cancelReason,
      },
      {
        ...getHandlers({ successTitle: "Reconciliation cancelled" }),
        onSuccess: () => {
          invalidate();
          setCancelTarget(null);
          setCancelReason("");
        },
      }
    );
  }

  function handleAutoReconcile() {
    autoMutation.mutate(
      { tenantId, invoiceId: autoInvoiceId },
      {
        ...getHandlers({ successTitle: "Auto-reconciled successfully" }),
        onSuccess: () => {
          invalidate();
          setAutoModalOpen(false);
          setAutoInvoiceId("");
        },
      }
    );
  }

  // stats
  const total = recs.length;
  const active = recs.filter((r) => r.status === "active").length;
  const cancelled = recs.filter((r) => r.status === "cancelled").length;

  const columns: Column<Reconciliation>[] = [
    { key: "id", header: "ID", cell: (r) => r.id.slice(0, 8) + "…" },
    { key: "payment_id", header: "Payment ID", cell: (r) => r.payment_id },
    { key: "invoice_id", header: "Invoice ID", cell: (r) => r.invoice_id },
    {
      key: "status",
      header: "Status",
      cell: (r) => <StatusBadge status={r.status} />,
    },
    { key: "notes", header: "Notes", cell: (r) => r.notes || "—" },
    {
      key: "created_at",
      header: "Created",
      cell: (r) => new Date(r.created_at).toLocaleDateString(),
    },
    {
      key: "actions",
      header: "Actions",
      cell: (r) =>
        r.status === "active" ? (
          <Button
            size="sm"
            variant="destructive"
            onClick={() => {
              setCancelTarget(r);
              setCancelReason("");
            }}
          >
            <XCircle className="h-3 w-3 mr-1" />
            Cancel
          </Button>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Payment Reconciliations"
          description="Match online payments to invoices"
          icon={Link2}
        />

        {/* tenant selector */}
        <div className="flex items-center gap-4">
          <select
            aria-label="Select tenant"
            value={tenantId}
            onChange={(e) => setTenantId(Number(e.target.value))}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value={0}>— Select tenant —</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          {/* status filter */}
          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="cancelled">Cancelled</option>
          </select>

          {/* auto-reconcile button */}
          {tenantId > 0 && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setAutoModalOpen(true)}
            >
              <Wand2 className="h-3 w-3 mr-1" />
              Auto Reconcile
            </Button>
          )}
        </div>

        {/* stat cards */}
        {tenantId > 0 && (
          <div className="grid grid-cols-3 gap-4">
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Total</p>
              <p className="text-2xl font-bold">{total}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Active</p>
              <p className="text-2xl font-bold text-green-600">{active}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Cancelled</p>
              <p className="text-2xl font-bold text-gray-500">{cancelled}</p>
            </Card>
          </div>
        )}

        {error && <ErrorState message="Failed to load reconciliations" />}

        {tenantId > 0 && (
          <DataTable
            columns={columns}
            data={recs}
            getRowKey={(r) => r.id}
          />
        )}

        {/* cancel modal */}
        {cancelTarget && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Cancel reconciliation"
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            <div className="bg-white rounded-lg p-6 w-96 space-y-4">
              <h2 className="text-lg font-semibold">Cancel Reconciliation</h2>
              <p className="text-sm text-muted-foreground">
                Cancel reconciliation <strong>{cancelTarget.id.slice(0, 8)}…</strong>?
              </p>
              <div>
                <label className="text-sm font-medium">Reason (optional)</label>
                <textarea
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="Enter reason..."
                  className="mt-1 w-full border rounded px-3 py-2 text-sm"
                  rows={3}
                  aria-label="Cancel reason"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setCancelTarget(null);
                    setCancelReason("");
                  }}
                >
                  Back
                </Button>
                <Button variant="destructive" onClick={handleCancel}>
                  <XCircle className="h-4 w-4 mr-1" />
                  Confirm Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* auto-reconcile modal */}
        {autoModalOpen && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Auto reconcile"
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            <div className="bg-white rounded-lg p-6 w-96 space-y-4">
              <h2 className="text-lg font-semibold">Auto Reconcile</h2>
              <p className="text-sm text-muted-foreground">
                Automatically match a completed payment to this invoice.
              </p>
              <div>
                <label className="text-sm font-medium">Invoice ID</label>
                <input
                  type="text"
                  value={autoInvoiceId}
                  onChange={(e) => setAutoInvoiceId(e.target.value)}
                  placeholder="e.g. inv-1234"
                  className="mt-1 w-full border rounded px-3 py-2 text-sm"
                  aria-label="Invoice ID for auto reconcile"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setAutoModalOpen(false);
                    setAutoInvoiceId("");
                  }}
                >
                  Back
                </Button>
                <Button
                  onClick={handleAutoReconcile}
                  disabled={!autoInvoiceId.trim()}
                >
                  <Wand2 className="h-4 w-4 mr-1" />
                  Run Auto Reconcile
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
