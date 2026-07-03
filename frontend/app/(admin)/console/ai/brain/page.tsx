"use client";

import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, RefreshCw } from "lucide-react";

import { useAdminAuth } from "@/shared/auth/context";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { ErrorState, LoadingState } from "@/shared/ui/page-states";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { useToast } from "@/shared/ui/use-toast";
import { formatDate, formatRelative } from "@/shared/utils/format";
import {
  useApplyBrainPolicyTuning,
  useBrainDecisions,
  useBrainExplanation,
  useBrainOutcomes,
  useBrainPolicyProfile,
  useBrainPolicyTuning,
} from "@/modules/brain-core/hooks";

function statusVariant(status: string): "success" | "secondary" | "warning" | "destructive" | "outline" {
  if (status === "dispatched" || status === "completed") return "success";
  if (status === "approval_pending") return "warning";
  if (status === "cancelled") return "secondary";
  if (status === "failed") return "destructive";
  return "outline";
}

function pct(value: number | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${Math.round(value * 100)}%`;
}

export default function BrainCorePage() {
  const { user } = useAdminAuth();
  const { toast } = useToast();

  const tenantId = user?.tenantId ?? 0;
  const actor = user?.sub ?? "ops@brain";

  const decisionsQuery = useBrainDecisions(tenantId);
  const outcomesQuery = useBrainOutcomes();
  const policyProfileQuery = useBrainPolicyProfile(tenantId);
  const policyTuningQuery = useBrainPolicyTuning(tenantId);

  const decisionItems = decisionsQuery.data?.items;
  const outcomeItems = outcomesQuery.data?.items;
  const decisions = useMemo(() => decisionItems ?? [], [decisionItems]);
  const outcomes = useMemo(() => outcomeItems ?? [], [outcomeItems]);

  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedDecisionId && decisions.length > 0) {
      setSelectedDecisionId(decisions[0].decision_id);
    }
  }, [decisions, selectedDecisionId]);

  const explanationQuery = useBrainExplanation(selectedDecisionId);
  const applyPolicyTuning = useApplyBrainPolicyTuning(tenantId);

  const pendingApprovals = useMemo(
    () => decisions.filter((item) => item.status === "approval_pending").length,
    [decisions],
  );

  const highPriority = useMemo(
    () => decisions.filter((item) => item.priority === "critical" || item.priority === "high").length,
    [decisions],
  );

  const anyLoading = decisionsQuery.isLoading || outcomesQuery.isLoading;
  const hasLoadError = decisionsQuery.isError || outcomesQuery.isError;

  async function handleApplyPolicyTuning() {
    try {
      const result = await applyPolicyTuning.mutateAsync({ actor });
      toast({
        variant: "success",
        title: result.changed ? "Policy profile updated" : "No profile changes applied",
        description: `Reason: ${result.reason}`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to apply policy tuning";
      toast({ variant: "destructive", title: message });
      throw error;
    }
  }

  return (
    <RequirePermission
      permission={PERMISSIONS.DASHBOARD_READ}
      message="You do not have permission to access Brain Core dashboard."
    >
      <div className="space-y-6" data-testid="brain-core-page">
        <PageHeader
          title="Brain Core Decision Center"
          description="Operational dashboard for decisions, explanations, outcomes, and tenant policy tuning."
          icon={BrainCircuit}
          actions={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void decisionsQuery.refetch();
                void outcomesQuery.refetch();
                void policyProfileQuery.refetch();
                void policyTuningQuery.refetch();
                if (selectedDecisionId) {
                  void explanationQuery.refetch();
                }
              }}
              disabled={anyLoading}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          }
        />

        {anyLoading && !decisionsQuery.data && !outcomesQuery.data && (
          <LoadingState title="Loading Brain Core dashboard" message="Fetching decisions and outcomes." />
        )}

        {hasLoadError && !anyLoading && (
          <ErrorState
            title="Unable to load Brain Core data"
            onRetry={() => {
              void decisionsQuery.refetch();
              void outcomesQuery.refetch();
            }}
          />
        )}

        {!anyLoading && !hasLoadError && (
          <>
            <section className="grid gap-4 grid-cols-1 md:grid-cols-4" data-testid="brain-core-summary">
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Total decisions</p>
                <p className="mt-1 text-2xl font-semibold">{decisions.length}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Pending approval</p>
                <p className="mt-1 text-2xl font-semibold">{pendingApprovals}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">High/Critical priority</p>
                <p className="mt-1 text-2xl font-semibold">{highPriority}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Recorded outcomes</p>
                <p className="mt-1 text-2xl font-semibold">{outcomes.length}</p>
              </div>
            </section>

            <section className="grid gap-6 grid-cols-1 xl:grid-cols-2">
              <div className="rounded-lg border bg-card">
                <div className="border-b px-4 py-3">
                  <h2 className="text-base font-semibold">Decisions</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/30 text-left">
                        <th className="px-4 py-2 font-medium">Decision</th>
                        <th className="px-4 py-2 font-medium">Type</th>
                        <th className="px-4 py-2 font-medium">Priority</th>
                        <th className="px-4 py-2 font-medium">Status</th>
                        <th className="px-4 py-2 font-medium">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {decisions.length === 0 && (
                        <tr>
                          <td className="px-4 py-4 text-muted-foreground" colSpan={5}>No decisions yet.</td>
                        </tr>
                      )}
                      {decisions.map((decision) => {
                        const active = selectedDecisionId === decision.decision_id;
                        return (
                          <tr
                            key={decision.decision_id}
                            className={`border-b cursor-pointer hover:bg-muted/30 ${active ? "bg-primary/5" : ""}`}
                            onClick={() => setSelectedDecisionId(decision.decision_id)}
                            data-testid={`brain-decision-row-${decision.decision_id}`}
                          >
                            <td className="px-4 py-2 font-mono text-xs">{decision.decision_id.slice(0, 8)}</td>
                            <td className="px-4 py-2">{decision.decision_type}</td>
                            <td className="px-4 py-2">{decision.priority}</td>
                            <td className="px-4 py-2">
                              <Badge variant={statusVariant(decision.status)}>{decision.status}</Badge>
                            </td>
                            <td className="px-4 py-2 text-muted-foreground">
                              {decision.created_at ? formatRelative(decision.created_at) : "-"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="rounded-lg border bg-card">
                <div className="border-b px-4 py-3">
                  <h2 className="text-base font-semibold">Explanation</h2>
                </div>
                <div className="p-4 space-y-4" data-testid="brain-explanation-panel">
                  {!selectedDecisionId && <p className="text-sm text-muted-foreground">Select a decision to view details.</p>}

                  {selectedDecisionId && explanationQuery.isLoading && (
                    <p className="text-sm text-muted-foreground">Loading explanation...</p>
                  )}

                  {selectedDecisionId && explanationQuery.isError && (
                    <p className="text-sm text-destructive">Failed to load explanation.</p>
                  )}

                  {selectedDecisionId && explanationQuery.data && (
                    <>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">Summary</p>
                        <p className="mt-1 text-sm">{explanationQuery.data.summary}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">Factors</p>
                        <ul className="mt-1 space-y-1 text-sm list-disc pl-5">
                          {(explanationQuery.data.factors ?? []).map((factor, idx) => (
                            <li key={`${factor}-${idx}`}>{factor}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">Policy notes</p>
                        <ul className="mt-1 space-y-1 text-sm list-disc pl-5">
                          {(explanationQuery.data.policy_notes ?? []).map((note, idx) => (
                            <li key={`${note}-${idx}`}>{note}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">Expected outcome</p>
                        <p className="mt-1 text-sm">{explanationQuery.data.expected_outcome}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </section>

            <section className="grid gap-6 grid-cols-1 xl:grid-cols-2">
              <div className="rounded-lg border bg-card">
                <div className="border-b px-4 py-3">
                  <h2 className="text-base font-semibold">Outcomes</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/30 text-left">
                        <th className="px-4 py-2 font-medium">Decision</th>
                        <th className="px-4 py-2 font-medium">Type</th>
                        <th className="px-4 py-2 font-medium">Effectiveness</th>
                        <th className="px-4 py-2 font-medium">Recorded</th>
                      </tr>
                    </thead>
                    <tbody>
                      {outcomes.length === 0 && (
                        <tr>
                          <td className="px-4 py-4 text-muted-foreground" colSpan={4}>No outcomes recorded yet.</td>
                        </tr>
                      )}
                      {outcomes.slice(0, 20).map((outcome) => (
                        <tr key={outcome.outcome_id} className="border-b">
                          <td className="px-4 py-2 font-mono text-xs">{outcome.decision_id.slice(0, 8)}</td>
                          <td className="px-4 py-2">{outcome.outcome_type}</td>
                          <td className="px-4 py-2">
                            <Badge variant={outcome.effectiveness === "negative" ? "destructive" : outcome.effectiveness === "positive" ? "success" : "outline"}>
                              {outcome.effectiveness}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-muted-foreground">
                            {outcome.created_at ? formatDate(outcome.created_at) : "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="rounded-lg border bg-card p-4 space-y-4" data-testid="brain-policy-panel">
                <div>
                  <h2 className="text-base font-semibold">Policy tuning</h2>
                  <p className="text-sm text-muted-foreground">Tenant profile and conservative tuning suggestion based on outcomes.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="rounded-md border p-3">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Current profile</p>
                    <p className="mt-1 text-sm">Autonomy level: {policyProfileQuery.data?.autonomy_level ?? "-"}</p>
                    <p className="text-sm">
                      Critical approval: {policyProfileQuery.data?.require_approval_for_critical ? "required" : "not required"}
                    </p>
                    <p className="text-sm text-muted-foreground">Role: {policyProfileQuery.data?.default_approval_role ?? "-"}</p>
                  </div>

                  <div className="rounded-md border p-3">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Suggested profile</p>
                    <p className="mt-1 text-sm">Autonomy level: {policyTuningQuery.data?.suggested_profile?.autonomy_level ?? "-"}</p>
                    <p className="text-sm">
                      Critical approval: {policyTuningQuery.data?.suggested_profile?.require_approval_for_critical ? "required" : "not required"}
                    </p>
                    <p className="text-sm text-muted-foreground">Reason: {policyTuningQuery.data?.reason ?? "-"}</p>
                  </div>
                </div>

                <div className="rounded-md border p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Outcome metrics</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                    <p>Total: {policyTuningQuery.data?.metrics?.total_outcomes ?? 0}</p>
                    <p>Positive rate: {pct(policyTuningQuery.data?.metrics?.positive_rate)}</p>
                    <p>Negative: {policyTuningQuery.data?.metrics?.negative ?? 0}</p>
                    <p>Negative rate: {pct(policyTuningQuery.data?.metrics?.negative_rate)}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <Badge variant={policyTuningQuery.data?.changed ? "warning" : "outline"}>
                    {policyTuningQuery.data?.changed ? "Change suggested" : "No tuning required"}
                  </Badge>
                  <ConfirmActionDialog
                    title="Apply policy tuning"
                    description="This will update tenant policy profile to the suggested values from outcome metrics."
                    confirmLabel="Apply tuning"
                    onConfirm={handleApplyPolicyTuning}
                    loading={applyPolicyTuning.isPending}
                    trigger={
                      <Button
                        size="sm"
                        disabled={!policyTuningQuery.data?.changed || applyPolicyTuning.isPending || tenantId <= 0}
                      >
                        Apply suggestion
                      </Button>
                    }
                  />
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </RequirePermission>
  );
}
