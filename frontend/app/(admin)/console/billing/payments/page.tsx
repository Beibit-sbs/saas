"use client";

import { useState } from "react";
import { CreditCard, CheckCircle, XCircle, RotateCcw } from "lucide-react";
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

export interface Payment {
  payment_id: string;
  tenant_id: number;
  student_id: string;
  amount: number;
  currency: string;
  method: string;
  description: string;
  status: string;
  created_at: string;
  transaction_ref?: string | null;
  reason?: string | null;
}

interface PaymentListResponse {
  payments: Payment[];
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

function usePayments(tenantId: number, status?: string) {
  return useQuery({
    queryKey: ["payments", tenantId, status],
    queryFn: () => {
      const params = new URLSearchParams({ tenant_id: String(tenantId) });
      if (status) params.set("status", status);
      return apiGet<PaymentListResponse>(`/api/payments?${params}`);
    },
    enabled: tenantId > 0,
  });
}

function useProcessPayment(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (paymentId: string) =>
      apiPost(`/api/payments/${paymentId}/process`, { tenant_id: tenantId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payments", tenantId] }),
  });
}

function useCompletePayment(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ paymentId, transactionRef }: { paymentId: string; transactionRef: string }) =>
      apiPost(`/api/payments/${paymentId}/complete`, {
        tenant_id: tenantId,
        transaction_ref: transactionRef,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payments", tenantId] }),
  });
}

function useFailPayment(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ paymentId, reason }: { paymentId: string; reason: string }) =>
      apiPost(`/api/payments/${paymentId}/fail`, { tenant_id: tenantId, reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payments", tenantId] }),
  });
}

function useRefundPayment(tenantId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ paymentId, reason }: { paymentId: string; reason: string }) =>
      apiPost(`/api/payments/${paymentId}/refund`, { tenant_id: tenantId, reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payments", tenantId] }),
  });
}

// ---------- constants ----------

const STATUS_COLORS: Record<string, "default" | "warning" | "destructive" | "success"> = {
  PENDING: "warning",
  PROCESSING: "warning",
  COMPLETED: "success",
  FAILED: "destructive",
  REFUNDED: "default",
};

const STATUSES = ["", "PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED"];

// ---------- page ----------

export default function PaymentsPage() {
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [transactionRef, setTransactionRef] = useState("");
  const [failingId, setFailingId] = useState<string | null>(null);
  const [failReason, setFailReason] = useState("");
  const [refundingId, setRefundingId] = useState<string | null>(null);
  const [refundReason, setRefundReason] = useState("");

  const { data: tenantsData, isLoading: tenantsLoading } = useTenants();
  const { data: paymentsData, isLoading: paymentsLoading, error: paymentsError } =
    usePayments(selectedTenantId ?? 0, statusFilter || undefined);

  const localeQuery = useTenantLocale(selectedTenantId ?? 0);
  const localeProfile = localeQuery.data;

  const processPayment = useProcessPayment(selectedTenantId ?? 0);
  const completePayment = useCompletePayment(selectedTenantId ?? 0);
  const failPayment = useFailPayment(selectedTenantId ?? 0);
  const refundPayment = useRefundPayment(selectedTenantId ?? 0);
  const { getHandlers } = useMutationFeedback();

  const tenants = tenantsData?.tenants ?? [];
  const payments = paymentsData?.payments ?? [];

  function fmtAmount(amount: number, currency: string) {
    return formatCurrencyAmount(amount, {
      currencyCode: localeProfile?.currency_code ?? currency,
      languageCode: localeProfile?.language_code ?? "en",
    });
  }

  const columns: Column<Payment>[] = [
    { key: "student_id", header: "Student", cell: (r) => r.student_id },
    { key: "method", header: "Method", cell: (r) => r.method },
    {
      key: "amount",
      header: "Amount",
      cell: (r) => fmtAmount(r.amount, r.currency),
    },
    {
      key: "status",
      header: "Status",
      cell: (r) => (
        <Badge variant={STATUS_COLORS[r.status] ?? "default"}>{r.status}</Badge>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      cell: (r) => (
        <div className="flex gap-2 flex-wrap">
          {r.status === "PENDING" && (
            <Button
              size="sm"
              variant="outline"
              aria-label={`Process ${r.payment_id}`}
              onClick={() =>
                processPayment.mutate(r.payment_id, getHandlers({ successTitle: "Payment processed" }))
              }
            >
              Process
            </Button>
          )}
          {r.status === "PROCESSING" && (
            <>
              <Button
                size="sm"
                variant="outline"
                aria-label={`Complete ${r.payment_id}`}
                onClick={() => {
                  setCompletingId(r.payment_id);
                  setTransactionRef("");
                }}
              >
                <CheckCircle className="w-3 h-3 mr-1" /> Complete
              </Button>
              <Button
                size="sm"
                variant="destructive"
                aria-label={`Fail ${r.payment_id}`}
                onClick={() => {
                  setFailingId(r.payment_id);
                  setFailReason("");
                }}
              >
                <XCircle className="w-3 h-3 mr-1" /> Fail
              </Button>
            </>
          )}
          {r.status === "COMPLETED" && (
            <Button
              size="sm"
              variant="outline"
              aria-label={`Refund ${r.payment_id}`}
              onClick={() => {
                setRefundingId(r.payment_id);
                setRefundReason("");
              }}
            >
              <RotateCcw className="w-3 h-3 mr-1" /> Refund
            </Button>
          )}
        </div>
      ),
    },
  ];

  // summary stats
  const totalPayments = payments.length;
  const completedCount = payments.filter((p) => p.status === "COMPLETED").length;
  const pendingCount = payments.filter((p) => p.status === "PENDING" || p.status === "PROCESSING").length;
  const failedCount = payments.filter((p) => p.status === "FAILED").length;

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          icon={CreditCard}
          title="Online Payments"
          description="View and manage tenant payment transactions"
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
                <p className="text-sm text-muted-foreground">Total Payments</p>
                <p className="text-2xl font-bold">{totalPayments}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold text-green-600">{completedCount}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">In Progress</p>
                <p className="text-2xl font-bold">{pendingCount}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold text-red-600">{failedCount}</p>
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
            {paymentsError ? (
              <ErrorState message="Failed to load payments" />
            ) : paymentsLoading ? (
              <p className="text-sm text-muted-foreground">Loading payments…</p>
            ) : payments.length === 0 ? (
              <Card className="p-6 text-center text-muted-foreground text-sm">
                No payments found.
              </Card>
            ) : (
              <DataTable
                columns={columns}
                data={payments}
                getRowKey={(p) => p.payment_id}
              />
            )}

            {/* Complete dialog */}
            {completingId && (
              <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <Card className="p-6 w-full max-w-md space-y-4">
                  <h2 className="font-semibold text-lg">Complete Payment</h2>
                  <p className="text-sm text-muted-foreground">
                    Enter the transaction reference from the payment gateway.
                  </p>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    placeholder="Transaction reference"
                    value={transactionRef}
                    onChange={(e) => setTransactionRef(e.target.value)}
                    aria-label="Transaction reference"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setCompletingId(null)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={() => {
                        completePayment.mutate(
                          { paymentId: completingId, transactionRef },
                          {
                            ...getHandlers({ successTitle: "Payment completed" }),
                            onSuccess: () => {
                              setCompletingId(null);
                            },
                          }
                        );
                      }}
                    >
                      Confirm Complete
                    </Button>
                  </div>
                </Card>
              </div>
            )}

            {/* Fail dialog */}
            {failingId && (
              <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <Card className="p-6 w-full max-w-md space-y-4">
                  <h2 className="font-semibold text-lg">Fail Payment</h2>
                  <p className="text-sm text-muted-foreground">
                    Provide a reason for failing this payment.
                  </p>
                  <textarea
                    className="w-full border rounded px-3 py-2 text-sm"
                    rows={3}
                    placeholder="Reason"
                    value={failReason}
                    onChange={(e) => setFailReason(e.target.value)}
                    aria-label="Fail reason"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setFailingId(null)}>
                      Cancel
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => {
                        failPayment.mutate(
                          { paymentId: failingId, reason: failReason },
                          {
                            ...getHandlers({ successTitle: "Payment failed" }),
                            onSuccess: () => {
                              setFailingId(null);
                            },
                          }
                        );
                      }}
                    >
                      Confirm Fail
                    </Button>
                  </div>
                </Card>
              </div>
            )}

            {/* Refund dialog */}
            {refundingId && (
              <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <Card className="p-6 w-full max-w-md space-y-4">
                  <h2 className="font-semibold text-lg">Refund Payment</h2>
                  <p className="text-sm text-muted-foreground">
                    Provide a reason for refunding this payment.
                  </p>
                  <textarea
                    className="w-full border rounded px-3 py-2 text-sm"
                    rows={3}
                    placeholder="Reason"
                    value={refundReason}
                    onChange={(e) => setRefundReason(e.target.value)}
                    aria-label="Refund reason"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setRefundingId(null)}>
                      Cancel
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        refundPayment.mutate(
                          { paymentId: refundingId, reason: refundReason },
                          {
                            ...getHandlers({ successTitle: "Payment refunded" }),
                            onSuccess: () => {
                              setRefundingId(null);
                            },
                          }
                        );
                      }}
                    >
                      <RotateCcw className="w-3 h-3 mr-1" /> Confirm Refund
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
