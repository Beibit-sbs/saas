"use client";

import { useState } from "react";
import { Network, Plus, Trash2, ToggleLeft, ToggleRight } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { LoadingState } from "@/shared/ui/page-states";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import {
  useAIRoutingPolicies,
  useCreateAIRoutingPolicy,
  useDeleteAIRoutingPolicy,
  useUpdateAIRoutingPolicy,
  useAIRoutingSelectionLog,
} from "@/modules/ai-routing/hooks";
import type { AIRoutingPolicyCreatePayload } from "@/modules/ai-routing/types";

export default function AIRoutingPage() {
  const { data: policies, isLoading, isError, refetch } = useAIRoutingPolicies();
  const { data: selectionLog } = useAIRoutingSelectionLog(20);
  const createPolicy = useCreateAIRoutingPolicy();
  const updatePolicy = useUpdateAIRoutingPolicy();
  const deletePolicy = useDeleteAIRoutingPolicy();

  const [showForm, setShowForm] = useState(false);
  const [formName, setFormName] = useState("");

  function handleCreate() {
    if (!formName.trim()) return;
    const payload: AIRoutingPolicyCreatePayload = {
      name: formName.trim(),
      strategy: "priority",
      enabled: true,
      rules: [],
      fallback_chain: [],
    };
    createPolicy.mutate(payload, {
      onSuccess: () => {
        setFormName("");
        setShowForm(false);
      },
    });
  }

  function handleToggle(policyId: number, enabled: boolean) {
    const policy = (policies ?? []).find((p) => p.id === policyId);
    if (!policy) return;
    updatePolicy.mutate({
      policyId,
      payload: {
        name: policy.name,
        strategy: policy.strategy,
        enabled: !enabled,
        rules: policy.rules,
        fallback_chain: policy.fallback_chain,
      },
    });
  }

  return (
    <RequirePermission
      permission={PERMISSIONS.AI_MODELS_MANAGE}
      message="You do not have permission to manage AI routing."
    >
      <div className="space-y-6" data-testid="ai-routing-page">
        <PageHeader
          title="AI Routing Policies"
          description="Manage model routing rules and observe recent routing decisions."
          icon={Network}
        />

        {/* Policies section */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Routing Policies</h2>
            <Button
              size="sm"
              onClick={() => setShowForm((v) => !v)}
              data-testid="add-policy-btn"
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Policy
            </Button>
          </div>

          {showForm && (
            <div
              className="rounded-lg border bg-card p-4 space-y-3"
              data-testid="create-policy-form"
            >
              <label className="text-sm font-medium" htmlFor="policy-name">
                Policy Name
              </label>
              <input
                id="policy-name"
                className="w-full rounded-md border bg-background p-2 text-sm"
                placeholder="e.g. Default Priority Policy"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                data-testid="policy-name-input"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleCreate}
                  disabled={createPolicy.isPending || !formName.trim()}
                  data-testid="save-policy-btn"
                >
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setShowForm(false);
                    setFormName("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {isLoading && <LoadingState />}
          {isError && (
            <ErrorState
              message="Failed to load routing policies."
              onRetry={refetch}
            />
          )}

          {!isLoading && !isError && (
            <div data-testid="policies-list">
              {(policies ?? []).length === 0 ? (
                <p className="text-sm text-muted-foreground py-4" data-testid="no-policies">
                  No routing policies configured.
                </p>
              ) : (
                <table className="w-full text-sm border rounded-lg overflow-hidden">
                  <thead>
                    <tr className="border-b bg-muted/50 text-left">
                      <th className="px-4 py-2 font-medium">Name</th>
                      <th className="px-4 py-2 font-medium">Strategy</th>
                      <th className="px-4 py-2 font-medium">Rules</th>
                      <th className="px-4 py-2 font-medium">Fallback chain</th>
                      <th className="px-4 py-2 font-medium">Status</th>
                      <th className="px-4 py-2 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(policies ?? []).map((policy) => (
                      <tr key={policy.id} className="border-b last:border-0" data-testid={`policy-row-${policy.id}`}>
                        <td className="px-4 py-2 font-medium">{policy.name}</td>
                        <td className="px-4 py-2">
                          <Badge variant="outline">{policy.strategy}</Badge>
                        </td>
                        <td className="px-4 py-2">{policy.rules.length}</td>
                        <td className="px-4 py-2">
                          {policy.fallback_chain.length > 0
                            ? policy.fallback_chain.join(" → ")
                            : <span className="text-muted-foreground">—</span>}
                        </td>
                        <td className="px-4 py-2">
                          <Badge variant={policy.enabled ? "success" : "secondary"} data-testid={`policy-status-${policy.id}`}>
                            {policy.enabled ? "enabled" : "disabled"}
                          </Badge>
                        </td>
                        <td className="px-4 py-2 flex gap-2">
                          <button
                            onClick={() => handleToggle(policy.id, policy.enabled)}
                            className="text-muted-foreground hover:text-foreground"
                            aria-label={policy.enabled ? "Disable policy" : "Enable policy"}
                            data-testid={`toggle-policy-${policy.id}`}
                          >
                            {policy.enabled ? (
                              <ToggleRight className="h-5 w-5 text-green-600" />
                            ) : (
                              <ToggleLeft className="h-5 w-5" />
                            )}
                          </button>
                          <button
                            onClick={() => deletePolicy.mutate(policy.id)}
                            className="text-muted-foreground hover:text-destructive"
                            aria-label="Delete policy"
                            data-testid={`delete-policy-${policy.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </section>

        {/* Selection log section */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Recent Routing Decisions</h2>
          <div data-testid="selection-log">
            {(selectionLog ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground py-4" data-testid="no-log-entries">
                No routing decisions recorded yet.
              </p>
            ) : (
              <table className="w-full text-sm border rounded-lg overflow-hidden">
                <thead>
                  <tr className="border-b bg-muted/50 text-left">
                    <th className="px-4 py-2 font-medium">Timestamp</th>
                    <th className="px-4 py-2 font-medium">Model</th>
                    <th className="px-4 py-2 font-medium">Selection</th>
                    <th className="px-4 py-2 font-medium">Task type</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectionLog ?? []).map((entry, i) => (
                    <tr key={i} className="border-b last:border-0" data-testid={`log-entry-${i}`}>
                      <td className="px-4 py-2 text-muted-foreground">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">{entry.model_key}</td>
                      <td className="px-4 py-2">
                        <Badge variant="outline">{entry.selection}</Badge>
                      </td>
                      <td className="px-4 py-2">{entry.task_type ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}
