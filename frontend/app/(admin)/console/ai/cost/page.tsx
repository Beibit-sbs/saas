"use client";

import { DollarSign, AlertTriangle, TrendingUp, ShieldCheck } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { ErrorState } from "@/shared/ui/error-state";
import { LoadingState } from "@/shared/ui/page-states";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import {
  useAICostSummary,
  useAICostProjection,
  useAICostAnomalies,
  useAICostBudgetStatus,
  useAISLOCompliance,
  useAISLOViolations,
} from "@/modules/ai-cost/hooks";

export default function AICostPage() {
  const { data: summary, isLoading, isError, refetch } = useAICostSummary();
  const { data: projection } = useAICostProjection();
  const { data: anomalies } = useAICostAnomalies();
  const { data: budgetStatus } = useAICostBudgetStatus();
  const { data: compliance } = useAISLOCompliance();
  const { data: violations } = useAISLOViolations();

  return (
    <RequirePermission
      permission={PERMISSIONS.AI_MODELS_MANAGE}
      message="You do not have permission to view AI cost governance."
    >
      <div className="space-y-6" data-testid="ai-cost-page">
        <PageHeader
          title="AI Cost & Performance Governance"
          description="Monitor usage, budget utilization, anomalies, cost projection, and SLO compliance."
          icon={DollarSign}
        />

        {isLoading && <LoadingState />}
        {isError && (
          <ErrorState message="Failed to load cost summary." onRetry={refetch} />
        )}

        {/* Summary section */}
        {summary && (
          <section className="space-y-3" data-testid="cost-summary-section">
            <h2 className="text-lg font-semibold">Usage Summary</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Total Requests</p>
                <p className="mt-1 text-2xl font-bold" data-testid="requests-total">
                  {summary.requests_total}
                </p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Estimated Cost</p>
                <p className="mt-1 text-2xl font-bold" data-testid="estimated-cost">
                  ${summary.estimated_cost_usd.toFixed(2)}
                </p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Budget Used</p>
                <p className="mt-1 text-2xl font-bold" data-testid="budget-utilization">
                  {summary.budget_utilization_pct.toFixed(1)}%
                </p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Budget Limit</p>
                <p className="mt-1 text-2xl font-bold" data-testid="budget-limit">
                  ${summary.budget_limit_usd.toFixed(2)}
                </p>
              </div>
            </div>

            {summary.budget_alert && (
              <div
                className="flex items-center gap-2 rounded-md border border-yellow-400 bg-yellow-50 p-3 text-sm text-yellow-800"
                data-testid="budget-alert-banner"
              >
                <AlertTriangle className="h-4 w-4" />
                Budget alert: utilization has exceeded the alert threshold.
              </div>
            )}

            {summary.anomaly_detected && (
              <div
                className="flex items-center gap-2 rounded-md border border-red-400 bg-red-50 p-3 text-sm text-red-800"
                data-testid="anomaly-alert-banner"
              >
                <AlertTriangle className="h-4 w-4" />
                Anomaly detected: {summary.anomaly_reason ?? "unusual cost spike observed."}
              </div>
            )}

            {/* Per-model table */}
            {summary.models.length > 0 && (
              <table className="w-full text-sm" data-testid="models-table">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 font-medium">Model</th>
                    <th className="pb-2 font-medium">Provider</th>
                    <th className="pb-2 font-medium">Requests</th>
                    <th className="pb-2 font-medium">Tokens</th>
                    <th className="pb-2 font-medium">Cost (USD)</th>
                    <th className="pb-2 font-medium">Avg Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.models.map((m) => (
                    <tr key={m.model_key} className="border-b last:border-0">
                      <td className="py-2 font-mono text-xs">{m.model_key}</td>
                      <td className="py-2">{m.provider}</td>
                      <td className="py-2">{m.requests_total}</td>
                      <td className="py-2">{m.total_tokens}</td>
                      <td className="py-2">${m.estimated_cost_usd.toFixed(4)}</td>
                      <td className="py-2">{m.avg_latency_ms.toFixed(0)}ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}

        {/* Projection section */}
        {projection && (
          <section className="space-y-3" data-testid="projection-section">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Cost Projection
            </h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Current Cost</p>
                <p className="mt-1 text-xl font-bold" data-testid="current-cost">
                  ${projection.current_cost_usd.toFixed(2)}
                </p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Projected Cost</p>
                <p className="mt-1 text-xl font-bold" data-testid="projected-cost">
                  ${projection.projected_cost_usd.toFixed(2)}
                </p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Basis</p>
                <p className="mt-1 text-sm font-medium" data-testid="projection-basis">
                  {projection.projection_basis}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Budget status section */}
        {budgetStatus && budgetStatus.length > 0 && (
          <section className="space-y-3" data-testid="budget-status-section">
            <h2 className="text-lg font-semibold">Budget Status</h2>
            <table className="w-full text-sm" data-testid="budget-status-table">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Scope</th>
                  <th className="pb-2 font-medium">Scope ID</th>
                  <th className="pb-2 font-medium">Limit</th>
                  <th className="pb-2 font-medium">Current</th>
                  <th className="pb-2 font-medium">Used %</th>
                  <th className="pb-2 font-medium">Alert</th>
                </tr>
              </thead>
              <tbody>
                {budgetStatus.map((b, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2">{b.scope}</td>
                    <td className="py-2">{b.scope_id ?? "—"}</td>
                    <td className="py-2">${b.budget_limit_usd.toFixed(2)}</td>
                    <td className="py-2">${b.current_cost_usd.toFixed(2)}</td>
                    <td className="py-2">{b.utilization_pct.toFixed(1)}%</td>
                    <td className="py-2">
                      {b.budget_alert ? (
                        <Badge variant="destructive" data-testid="budget-alert-badge">Alert</Badge>
                      ) : (
                        <Badge variant="secondary">OK</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* Anomalies section */}
        {anomalies && anomalies.length > 0 && (
          <section className="space-y-3" data-testid="anomalies-section">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Cost Anomalies
            </h2>
            <table className="w-full text-sm" data-testid="anomalies-table">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Timestamp</th>
                  <th className="pb-2 font-medium">Model</th>
                  <th className="pb-2 font-medium">Cost (USD)</th>
                  <th className="pb-2 font-medium">Z-Score</th>
                  <th className="pb-2 font-medium">Reason</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.map((a, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2 font-mono text-xs">{a.timestamp}</td>
                    <td className="py-2 font-mono text-xs">{a.model_key}</td>
                    <td className="py-2">${a.estimated_cost_usd.toFixed(4)}</td>
                    <td className="py-2">{a.anomaly_score_z.toFixed(2)}</td>
                    <td className="py-2">{a.anomaly_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* SLO compliance section */}
        {compliance && (
          <section className="space-y-3" data-testid="slo-section">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <ShieldCheck className="h-4 w-4" />
              SLO Compliance
            </h2>
            {violations && violations.length > 0 && (
              <div
                className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800"
                data-testid="slo-violations-banner"
              >
                {violations.length} SLO violation{violations.length !== 1 ? "s" : ""} detected.
              </div>
            )}
            {compliance.length === 0 ? (
              <p className="text-sm text-muted-foreground" data-testid="no-slo-policies">
                No SLO policies configured.
              </p>
            ) : (
              <table className="w-full text-sm" data-testid="slo-compliance-table">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 font-medium">Model</th>
                    <th className="pb-2 font-medium">P95 Latency</th>
                    <th className="pb-2 font-medium">Error Rate</th>
                    <th className="pb-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {compliance.map((c) => (
                    <tr key={c.model_key} className="border-b last:border-0">
                      <td className="py-2 font-mono text-xs">{c.model_key}</td>
                      <td className="py-2">
                        {c.p95_latency_ms_observed}ms / {c.p95_latency_ms_target}ms
                      </td>
                      <td className="py-2">
                        {c.error_rate_pct_observed.toFixed(1)}% / {c.max_error_rate_pct_target}%
                      </td>
                      <td className="py-2">
                        {c.compliant ? (
                          <Badge variant="secondary" data-testid="slo-ok-badge">OK</Badge>
                        ) : (
                          <Badge variant="destructive" data-testid="slo-violation-badge">Violation</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}
      </div>
    </RequirePermission>
  );
}
