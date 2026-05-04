"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPut } from "@/shared/api/client";

// ---------- types ----------

export interface QuotaRow {
  id: number;
  plan_id: number;
  key: string;
  limit_value: number;
}

interface QuotaListResponse {
  quotas: QuotaRow[];
}

interface QuotaCheckResult {
  tenant_id: number;
  quota_key: string;
  limit_value: number;
  current_value: number;
  within_limit: boolean;
  soft_warning: boolean;
  message: string;
}

interface ConsistencyReport {
  total_plan_count: number;
  configured_plan_quota_count: number;
  issue_count: number;
  issues: Array<{
    issue_type: string;
    plan_id: number | null;
    plan_code: string | null;
    quota_key: string | null;
    detail: string;
  }>;
}

interface PlanRecord {
  id: number;
  code: string;
  name: string;
}

interface PlanListResponse {
  plans: PlanRecord[];
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

function usePlans() {
  return useQuery({
    queryKey: ["plans"],
    queryFn: () => apiGet<PlanListResponse>("/api/billing/plans"),
  });
}

function useTenants() {
  return useQuery({
    queryKey: ["tenants"],
    queryFn: () => apiGet<TenantListResponse>("/api/admin/tenants"),
  });
}

function useQuotas(planId: number | null) {
  return useQuery({
    queryKey: ["quotas", planId],
    queryFn: () => {
      const params = planId ? `?plan_id=${planId}` : "";
      return apiGet<QuotaListResponse>(`/api/quotas${params}`);
    },
  });
}

function useConsistencyReport() {
  return useQuery({
    queryKey: ["quotas-consistency"],
    queryFn: () => apiGet<ConsistencyReport>("/api/quotas/consistency"),
  });
}

function useCheckQuota(tenantId: number, quotaKey: string) {
  return useQuery({
    queryKey: ["quota-check", tenantId, quotaKey],
    queryFn: () =>
      apiGet<QuotaCheckResult>(
        `/api/quotas/check?tenant_id=${tenantId}&quota_key=${encodeURIComponent(quotaKey)}`
      ),
    enabled: tenantId > 0 && quotaKey.length > 0,
  });
}

function useUpdatePlanQuotas() {
  return useMutation({
    mutationFn: ({
      planId,
      quotas,
    }: {
      planId: number;
      quotas: Record<string, number>;
    }) => apiPut(`/api/quotas/plans/${planId}`, { quotas }),
  });
}

// ---------- page ----------

export default function QuotasPage() {
  const qc = useQueryClient();
  const { getHandlers } = useMutationFeedback();

  const [planFilter, setPlanFilter] = useState<number | null>(null);
  const [checkTenantId, setCheckTenantId] = useState(0);
  const [checkKey, setCheckKey] = useState("");
  const [checkTriggered, setCheckTriggered] = useState(false);

  // edit quota modal
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editPlanId, setEditPlanId] = useState(0);
  const [editKey, setEditKey] = useState("");
  const [editValue, setEditValue] = useState(0);

  const { data: plansData } = usePlans();
  const plans = plansData?.plans ?? [];

  const { data: tenantsData } = useTenants();
  const tenants = tenantsData?.tenants ?? [];

  const { data: quotasData, error } = useQuotas(planFilter);
  const quotas = quotasData?.quotas ?? [];

  const { data: consistencyData } = useConsistencyReport();

  const checkQuery = useCheckQuota(
    checkTriggered ? checkTenantId : 0,
    checkTriggered ? checkKey : ""
  );

  const updateMutation = useUpdatePlanQuotas();

  const invalidate = () => qc.invalidateQueries({ queryKey: ["quotas"] });

  function openEditModal(row: QuotaRow) {
    setEditPlanId(row.plan_id);
    setEditKey(row.key);
    setEditValue(row.limit_value);
    setEditModalOpen(true);
  }

  function handleSave() {
    updateMutation.mutate(
      { planId: editPlanId, quotas: { [editKey]: editValue } },
      {
        ...getHandlers({ successTitle: "Quota updated" }),
        onSuccess: () => {
          invalidate();
          setEditModalOpen(false);
        },
      }
    );
  }

  const totalQuotas = quotas.length;
  const planCount = Array.from(new Set(quotas.map((q) => q.plan_id))).length;
  const issueCount = consistencyData?.issue_count ?? 0;

  const columns: Column<QuotaRow>[] = [
    { key: "plan_id", header: "Plan ID", cell: (q) => String(q.plan_id) },
    { key: "key", header: "Quota Key", cell: (q) => q.key },
    {
      key: "limit_value",
      header: "Limit",
      cell: (q) => q.limit_value.toLocaleString(),
    },
    {
      key: "actions",
      header: "Actions",
      cell: (q) => (
        <Button size="sm" variant="outline" onClick={() => openEditModal(q)}>
          Edit
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Quota Management"
          description="Configure plan quotas and check tenant limits"
          icon={ShieldCheck}
        />

        {/* Controls */}
        <div className="flex items-center gap-4">
          <select
            aria-label="Filter by plan"
            className="border rounded px-3 py-2 text-sm"
            value={planFilter ?? ""}
            onChange={(e) =>
              setPlanFilter(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">— All plans —</option>
            {plans.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name || p.code}
              </option>
            ))}
          </select>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Total Quotas</p>
            <p className="text-2xl font-bold">{totalQuotas}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Plans Configured</p>
            <p className="text-2xl font-bold text-blue-600">{planCount}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Consistency Issues</p>
            <p
              className={`text-2xl font-bold ${issueCount > 0 ? "text-red-600" : "text-green-600"}`}
            >
              {issueCount}
            </p>
          </Card>
        </div>

        {/* Quota Check */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Check Tenant Quota</h3>
          <div className="flex items-center gap-3">
            <select
              aria-label="Select tenant for check"
              className="border rounded px-3 py-2 text-sm"
              value={checkTenantId}
              onChange={(e) => {
                setCheckTenantId(Number(e.target.value));
                setCheckTriggered(false);
              }}
            >
              <option value={0}>— Select tenant —</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <input
              aria-label="Quota key to check"
              className="border rounded px-3 py-2 text-sm"
              placeholder="Quota key (e.g. users)"
              value={checkKey}
              onChange={(e) => {
                setCheckKey(e.target.value);
                setCheckTriggered(false);
              }}
            />
            <Button
              size="sm"
              disabled={checkTenantId <= 0 || checkKey.length === 0}
              onClick={() => setCheckTriggered(true)}
            >
              Check
            </Button>
          </div>
          {checkTriggered && checkQuery.data && (
            <Card className="p-4 space-y-1">
              <p className="text-sm">
                Key: <strong>{checkQuery.data.quota_key}</strong>
              </p>
              <p className="text-sm">
                Limit:{" "}
                <strong>{checkQuery.data.limit_value.toLocaleString()}</strong>
              </p>
              <p className="text-sm">
                Current:{" "}
                <strong>
                  {checkQuery.data.current_value.toLocaleString()}
                </strong>
              </p>
              <p className="text-sm">
                Status:{" "}
                <span
                  className={
                    checkQuery.data.within_limit
                      ? "text-green-600 font-semibold"
                      : "text-red-600 font-semibold"
                  }
                >
                  {checkQuery.data.message}
                </span>
              </p>
            </Card>
          )}
        </div>

        {/* Error */}
        {error && <ErrorState message="Failed to load quotas" />}

        {/* Table */}
        <div className="space-y-3">
          <DataTable
            columns={columns}
            data={quotas}
            getRowKey={(q) => `${q.plan_id}-${q.key}`}
          />
        </div>

        {/* Edit Quota Modal */}
        {editModalOpen && (
          <div
            role="dialog"
            aria-label="Edit Quota"
            className="fixed inset-0 flex items-center justify-center bg-black/40"
          >
            <div className="bg-background rounded-lg p-6 w-96 space-y-4">
              <h2 className="text-lg font-semibold">Edit Quota</h2>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  Plan ID: <strong>{editPlanId}</strong>
                </p>
                <p className="text-sm text-muted-foreground">
                  Key: <strong>{editKey}</strong>
                </p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Limit Value</label>
                <input
                  aria-label="Limit value"
                  type="number"
                  min={0}
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={editValue}
                  onChange={(e) => setEditValue(Number(e.target.value))}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setEditModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={updateMutation.isPending}>
                  Save
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
