"use client";

import { useState } from "react";
import { FileText, Send, CheckCircle, XCircle, Plus } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { formatCurrencyAmount } from "@/shared/utils/format";
import { useTenantLocale } from "@/modules/currency-localization/hooks";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";

// ---------- types ----------

export interface InvoiceItem {
  item_id: string;
  description: string;
  quantity: number;
  unit_price_cents: number;
  total_cents: number;
}

export interface Invoice {
  invoice_id: string;
  tenant_id: number;
  invoice_number: string;
  status: string;
  currency_code: string;
  items: InvoiceItem[];
  total_cents: number;
  due_date: string;
  notes: string;
  issued_at: string | null;
  sent_at: string | null;
  payments: unknown[];
  voided_at: string | null;
}

interface InvoiceListResponse {
  invoices: Invoice[];
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

function useInvoices(tenantId: number, status?: string) {
  return useQuery({
    queryKey: ["invoices", tenantId, status],
    queryFn: () => {
      const params = new URLSearchParams({ tenant_id: String(tenantId) });
      if (status) params.set("status", status);
      return apiGet<InvoiceListResponse>(`/api/invoices?${params}`);
    },
    enabled: tenantId > 0,
  });
}

function useFinalizeInvoice(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost(`/api/invoices/${invoiceId}/finalize`, { tenant_id: tenantId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices", tenantId] }),
  });
}

function useSendInvoice(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost(`/api/invoices/${invoiceId}/send`, { tenant_id: tenantId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices", tenantId] }),
  });
}

function useVoidInvoice(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ invoiceId, reason }: { invoiceId: string; reason: string }) =>
      apiPost(`/api/invoices/${invoiceId}/void`, { tenant_id: tenantId, reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices", tenantId] }),
  });
}

// ---------- constants ----------

const STATUS_COLORS: Record<string, "default" | "warning" | "destructive" | "success"> = {
  draft: "default",
  finalized: "warning",
  sent: "warning",
  paid: "success",
  overdue: "destructive",
  void: "destructive",
};

const STATUSES = ["", "draft", "finalized", "sent", "paid", "overdue", "void"];

// ---------- page ----------

export default function InvoicesPage() {
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [voidingId, setVoidingId] = useState<string | null>(null);
  const [voidReason, setVoidReason] = useState("");

  const { data: tenantsData, isLoading: tenantsLoading } = useTenants();
  const { data: invoicesData, isLoading: invoicesLoading, error: invoicesError } =
    useInvoices(selectedTenantId ?? 0, statusFilter || undefined);

  const localeQuery = useTenantLocale(selectedTenantId ?? 0);
  const localeProfile = localeQuery.data;

  const finalize = useFinalizeInvoice(selectedTenantId ?? 0);
  const send = useSendInvoice(selectedTenantId ?? 0);
  const voidInv = useVoidInvoice(selectedTenantId ?? 0);
  const { getHandlers } = useMutationFeedback();

  const tenants = tenantsData?.tenants ?? [];
  const invoices = invoicesData?.invoices ?? [];

  function fmtAmount(cents: number, currency: string) {
    return formatCurrencyAmount(cents / 100, {
      currencyCode: localeProfile?.currency_code ?? currency,
      languageCode: localeProfile?.language_code ?? "en",
    });
  }

  const columns: Column<Invoice>[] = [
    { key: "invoice_number", header: "Number", cell: (r) => r.invoice_number },
    {
      key: "status",
      header: "Status",
      cell: (r) => (
        <Badge variant={STATUS_COLORS[r.status] ?? "default"}>{r.status}</Badge>
      ),
    },
    {
      key: "total_cents",
      header: "Total",
      cell: (r) => fmtAmount(r.total_cents, r.currency_code),
    },
    { key: "due_date", header: "Due Date", cell: (r) => r.due_date },
    {
      key: "actions",
      header: "Actions",
      cell: (r) => (
        <div className="flex gap-2">
          {r.status === "draft" && (
            <Button
              size="sm"
              variant="outline"
              aria-label={`Finalize ${r.invoice_number}`}
              onClick={() =>
                finalize.mutate(r.invoice_id, getHandlers({ successTitle: "Invoice finalized" }))
              }
            >
              <FileText className="w-3 h-3 mr-1" /> Finalize
            </Button>
          )}
          {r.status === "finalized" && (
            <Button
              size="sm"
              variant="outline"
              aria-label={`Send ${r.invoice_number}`}
              onClick={() =>
                send.mutate(r.invoice_id, getHandlers({ successTitle: "Invoice sent" }))
              }
            >
              <Send className="w-3 h-3 mr-1" /> Send
            </Button>
          )}
          {["draft", "finalized", "sent", "overdue"].includes(r.status) && (
            <Button
              size="sm"
              variant="destructive"
              aria-label={`Void ${r.invoice_number}`}
              onClick={() => {
                setVoidingId(r.invoice_id);
                setVoidReason("");
              }}
            >
              <XCircle className="w-3 h-3 mr-1" /> Void
            </Button>
          )}
        </div>
      ),
    },
  ];

  // summary stats
  const totalInvoices = invoices.length;
  const paidCount = invoices.filter((i) => i.status === "paid").length;
  const overdueCount = invoices.filter((i) => i.status === "overdue").length;
  const draftCount = invoices.filter((i) => i.status === "draft").length;

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          icon={FileText}
          title="Invoices"
          description="View and manage tenant invoices"
        />

        {/* Tenant selector */}
        <Card className="p-4">
          <label className="block text-sm font-medium mb-1">Tenant</label>
          {tenantsLoading ? (
            <p className="text-sm text-muted-foreground">Loading tenants…</p>
          ) : (
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={selectedTenantId ?? ""}
              onChange={(e) =>
                setSelectedTenantId(e.target.value ? Number(e.target.value) : null)
              }
              aria-label="Select tenant"
            >
              <option value="">— select a tenant —</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          )}
        </Card>

        {selectedTenantId && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">Total Invoices</p>
                <p className="text-2xl font-bold">{totalInvoices}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">Paid</p>
                <p className="text-2xl font-bold text-green-600">{paidCount}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">Overdue</p>
                <p className="text-2xl font-bold text-red-600">{overdueCount}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">Drafts</p>
                <p className="text-2xl font-bold">{draftCount}</p>
              </Card>
            </div>

            {/* Filter */}
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium">Filter by status:</label>
              <select
                className="border rounded px-3 py-1 text-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Filter by status"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s || "All"}
                  </option>
                ))}
              </select>
            </div>

            {/* Table */}
            {invoicesError ? (
              <ErrorState message="Failed to load invoices" />
            ) : invoicesLoading ? (
              <p className="text-sm text-muted-foreground">Loading invoices…</p>
            ) : invoices.length === 0 ? (
              <Card className="p-6 text-center text-muted-foreground text-sm">
                No invoices found.
              </Card>
            ) : (
              <DataTable columns={columns} data={invoices} getRowKey={(inv) => inv.invoice_id} />
            )}

            {/* Void dialog */}
            {voidingId && (
              <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <Card className="p-6 w-full max-w-md space-y-4">
                  <h2 className="font-semibold text-lg">Void Invoice</h2>
                  <p className="text-sm text-muted-foreground">
                    Provide an optional reason for voiding this invoice.
                  </p>
                  <textarea
                    className="w-full border rounded px-3 py-2 text-sm"
                    rows={3}
                    placeholder="Reason (optional)"
                    value={voidReason}
                    onChange={(e) => setVoidReason(e.target.value)}
                    aria-label="Void reason"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setVoidingId(null)}>
                      Cancel
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => {
                        voidInv.mutate(
                          { invoiceId: voidingId, reason: voidReason },
                          {
                            ...getHandlers({ successTitle: "Invoice voided" }),
                            onSuccess: () => {
                              setVoidingId(null);
                            },
                          }
                        );
                      }}
                    >
                      Confirm Void
                    </Button>
                  </div>
                </Card>
              </div>
            )}
          </>
        )}
      </div>
    </RequirePermission>
  );
}
