"use client";

import { useState } from "react";
import { CreditCard } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPatch, apiDelete } from "@/shared/api/client";

// ---------- types ----------

export interface PlanRow {
  id: number;
  code: string;
  name: string;
  description: string;
  active: boolean;
}

interface PlanListResponse {
  plans: PlanRow[];
}

interface PlanItemResponse {
  plan: PlanRow;
}

interface PlanStats {
  total: number;
  active: number;
  inactive: number;
}

// ---------- hooks ----------

function usePlans(includeInactive: boolean) {
  return useQuery({
    queryKey: ["billing-plans", includeInactive],
    queryFn: () =>
      apiGet<PlanListResponse>(
        `/api/billing/plans${includeInactive ? "?include_inactive=true" : ""}`
      ),
  });
}

function usePlanStats() {
  return useQuery({
    queryKey: ["billing-plans-stats"],
    queryFn: () => apiGet<PlanStats>("/api/billing/plans/stats"),
  });
}

function useCreatePlan() {
  return useMutation({
    mutationFn: (payload: { code: string; name: string; description: string }) =>
      apiPost<PlanItemResponse>("/api/billing/plans", payload),
  });
}

function useUpdatePlan() {
  return useMutation({
    mutationFn: ({
      planId,
      payload,
    }: {
      planId: number;
      payload: { name?: string; description?: string; active?: boolean };
    }) => apiPatch<PlanItemResponse>(`/api/billing/plans/${planId}`, payload),
  });
}

function useDeactivatePlan() {
  return useMutation({
    mutationFn: (planId: number) => apiDelete(`/api/billing/plans/${planId}`),
  });
}

// ---------- component ----------

export default function BillingPlansPage() {
  const queryClient = useQueryClient();
  const [includeInactive, setIncludeInactive] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PlanRow | null>(null);

  // form state — create
  const [newCode, setNewCode] = useState("");
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  // form state — edit
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const { data: plansData, error } = usePlans(includeInactive);
  const { data: statsData } = usePlanStats();
  const plans = plansData?.plans ?? [];

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["billing-plans"] });
    queryClient.invalidateQueries({ queryKey: ["billing-plans-stats"] });
  };

  const createMutation = useCreatePlan();
  const updateMutation = useUpdatePlan();
  const deactivateMutation = useDeactivatePlan();

  const { getHandlers } = useMutationFeedback();

  function openEditModal(plan: PlanRow) {
    setSelectedPlan(plan);
    setEditName(plan.name);
    setEditDescription(plan.description);
    setEditModalOpen(true);
  }

  function handleCreate() {
    createMutation.mutate(
      { code: newCode, name: newName, description: newDescription },
      {
        ...getHandlers({ successTitle: "Plan created" }),
        onSuccess: () => {
          invalidate();
          setCreateModalOpen(false);
          setNewCode("");
          setNewName("");
          setNewDescription("");
        },
      }
    );
  }

  function handleUpdate() {
    if (!selectedPlan) return;
    updateMutation.mutate(
      { planId: selectedPlan.id, payload: { name: editName, description: editDescription } },
      {
        ...getHandlers({ successTitle: "Plan updated" }),
        onSuccess: () => {
          invalidate();
          setEditModalOpen(false);
          setSelectedPlan(null);
        },
      }
    );
  }

  function handleDeactivate(plan: PlanRow) {
    deactivateMutation.mutate(plan.id, {
      ...getHandlers({ successTitle: "Plan deactivated" }),
      onSuccess: () => invalidate(),
    });
  }

  const columns: Column<PlanRow>[] = [
    { key: "code", header: "Code", cell: (p) => <code className="text-xs">{p.code}</code> },
    { key: "name", header: "Name", cell: (p) => p.name },
    {
      key: "description",
      header: "Description",
      cell: (p) => p.description || <span className="text-muted-foreground text-xs">—</span>,
    },
    {
      key: "active",
      header: "Status",
      cell: (p) => (
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            p.active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
          }`}
        >
          {p.active ? "Active" : "Inactive"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      cell: (p) => (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => openEditModal(p)}>
            Edit
          </Button>
          {p.active && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleDeactivate(p)}
              disabled={deactivateMutation.isPending}
            >
              Deactivate
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Billing Plans"
          description="Manage subscription plans and their availability"
          icon={CreditCard}
        />

        {/* Controls */}
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              aria-label="Show inactive plans"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            Show inactive plans
          </label>
          <RequirePermission permission={PERMISSIONS.BILLING_WRITE}>
            <Button size="sm" onClick={() => setCreateModalOpen(true)}>
              + New Plan
            </Button>
          </RequirePermission>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Total Plans</p>
            <p className="text-2xl font-bold">{statsData?.total ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Active Plans</p>
            <p className="text-2xl font-bold text-green-600">{statsData?.active ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Inactive Plans</p>
            <p className="text-2xl font-bold text-gray-500">{statsData?.inactive ?? 0}</p>
          </Card>
        </div>

        {/* Error */}
        {error && <ErrorState message="Failed to load billing plans" />}

        {/* Table */}
        <DataTable
          columns={columns}
          data={plans}
          getRowKey={(p) => String(p.id)}
        />

        {/* Create Modal */}
        {createModalOpen && (
          <div
            role="dialog"
            aria-label="Create Plan"
            className="fixed inset-0 flex items-center justify-center bg-black/40"
          >
            <div className="bg-background rounded-lg p-6 w-96 space-y-4">
              <h2 className="text-lg font-semibold">New Billing Plan</h2>
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Code</label>
                  <input
                    aria-label="Plan code"
                    className="w-full border rounded px-3 py-2 text-sm"
                    placeholder="e.g. pro"
                    value={newCode}
                    onChange={(e) => setNewCode(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Name</label>
                  <input
                    aria-label="Plan name"
                    className="w-full border rounded px-3 py-2 text-sm"
                    placeholder="e.g. Professional"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Description</label>
                  <input
                    aria-label="Plan description"
                    className="w-full border rounded px-3 py-2 text-sm"
                    placeholder="Optional description"
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setCreateModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleCreate}
                  disabled={!newCode || !newName || createMutation.isPending}
                >
                  Create
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {editModalOpen && selectedPlan && (
          <div
            role="dialog"
            aria-label="Edit Plan"
            className="fixed inset-0 flex items-center justify-center bg-black/40"
          >
            <div className="bg-background rounded-lg p-6 w-96 space-y-4">
              <h2 className="text-lg font-semibold">Edit Plan</h2>
              <p className="text-sm text-muted-foreground">
                Code: <strong>{selectedPlan.code}</strong>
              </p>
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Name</label>
                  <input
                    aria-label="Edit plan name"
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Description</label>
                  <input
                    aria-label="Edit plan description"
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditModalOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleUpdate} disabled={!editName || updateMutation.isPending}>
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

