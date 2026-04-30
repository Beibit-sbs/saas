"use client";

import { useMemo } from "react";
import { BrainCircuit, RefreshCw, Lightbulb, TrendingUp, AlertTriangle } from "lucide-react";

import { useAdminAuth } from "@/shared/auth/context";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState, LoadingState } from "@/shared/ui/page-states";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import {
  useBrainExecutiveKPI,
  useBrainRecommendations,
} from "@/modules/brain-core/hooks";

function severityVariant(severity: string): "destructive" | "warning" | "secondary" | "outline" {
  if (severity === "critical") return "destructive";
  if (severity === "high") return "warning";
  if (severity === "medium") return "secondary";
  return "outline";
}

function healthVariant(status: string): "success" | "warning" | "destructive" | "outline" {
  if (status === "healthy") return "success";
  if (status === "degraded") return "warning";
  if (status === "critical") return "destructive";
  return "outline";
}

function pct(value: number | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${Math.round(value * 100)}%`;
}

export default function BrainIntelligencePage() {
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;

  const kpiQuery = useBrainExecutiveKPI(tenantId);
  const recommendationsQuery = useBrainRecommendations(tenantId);

  const recommendations = useMemo(
    () => recommendationsQuery.data?.recommendations ?? [],
    [recommendationsQuery.data],
  );

  const kpi = kpiQuery.data;

  const anyLoading = kpiQuery.isLoading || recommendationsQuery.isLoading;
  const hasError = kpiQuery.isError && recommendationsQuery.isError;

  return (
    <RequirePermission
      permission={PERMISSIONS.DASHBOARD_READ}
      message="You do not have permission to access Brain Intelligence."
    >
      <div className="space-y-6" data-testid="brain-intelligence-page">
        <PageHeader
          title="Brain Intelligence Dashboard"
          description="Predictive KPIs, proactive recommendations, and signal intelligence for your tenant."
          icon={BrainCircuit}
          actions={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void kpiQuery.refetch();
                void recommendationsQuery.refetch();
              }}
              disabled={anyLoading}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          }
        />

        {anyLoading && !kpi && recommendations.length === 0 && (
          <LoadingState title="Loading intelligence data" message="Fetching KPIs and recommendations." />
        )}

        {hasError && !anyLoading && (
          <ErrorState
            title="Unable to load intelligence data"
            onRetry={() => {
              void kpiQuery.refetch();
              void recommendationsQuery.refetch();
            }}
          />
        )}

        {kpi && (
          <>
            {/* KPI Summary Cards */}
            <section
              className="grid gap-4 grid-cols-2 md:grid-cols-4"
              data-testid="brain-kpi-summary"
            >
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Signal Volume
                </p>
                <p className="mt-1 text-2xl font-semibold">{kpi.signal_volume.total}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {kpi.signal_volume.high_severity} high-severity
                </p>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Decision Quality</p>
                <p className="mt-1 text-2xl font-semibold">{kpi.decision_quality.total_decisions}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Dispatch rate: {pct(kpi.decision_quality.dispatch_rate)}
                </p>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Effectiveness Score</p>
                <p className="mt-1 text-2xl font-semibold">
                  {pct(kpi.outcome_effectiveness.effectiveness_score)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {kpi.outcome_effectiveness.positive} positive / {kpi.outcome_effectiveness.negative} negative
                </p>
              </div>

              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">Brain Health</p>
                <div className="mt-1">
                  <Badge variant={healthVariant(kpi.brain_health.health_status)}>
                    {kpi.brain_health.health_status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Autonomy level: {kpi.brain_health.policy_autonomy_level}
                </p>
              </div>
            </section>

            {/* Top Risk Signals */}
            {kpi.top_risk_signals.length > 0 && (
              <section className="rounded-lg border bg-card" data-testid="brain-top-risks">
                <div className="border-b px-4 py-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-warning" />
                  <h2 className="text-base font-semibold">Top Risk Signals</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/30 text-left">
                        <th className="px-4 py-2 font-medium">Event Type</th>
                        <th className="px-4 py-2 font-medium text-right">Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kpi.top_risk_signals.map((signal) => (
                        <tr key={signal.event_type} className="border-b last:border-0">
                          <td className="px-4 py-2 font-mono text-xs">{signal.event_type}</td>
                          <td className="px-4 py-2 text-right font-semibold">{signal.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        )}

        {/* Proactive Recommendations */}
        <section className="rounded-lg border bg-card" data-testid="brain-recommendations">
          <div className="border-b px-4 py-3 flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-primary" />
            <h2 className="text-base font-semibold">Proactive Recommendations</h2>
            {recommendations.length > 0 && (
              <Badge variant="secondary" className="ml-auto">
                {recommendations.length}
              </Badge>
            )}
          </div>

          {recommendationsQuery.isLoading && (
            <div className="p-4 text-sm text-muted-foreground">Loading recommendations…</div>
          )}

          {!recommendationsQuery.isLoading && recommendations.length === 0 && (
            <div className="p-8 text-center text-sm text-muted-foreground" data-testid="no-recommendations">
              No active recommendations for this tenant.
            </div>
          )}

          {recommendations.length > 0 && (
            <div className="divide-y">
              {recommendations.map((rec) => (
                <div key={rec.recommendation_id} className="p-4 space-y-1">
                  <div className="flex items-start gap-3">
                    <Badge variant={severityVariant(rec.severity)}>{rec.severity}</Badge>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{rec.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{rec.description}</p>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {Math.round(rec.confidence * 100)}% confidence
                    </span>
                  </div>
                  {rec.suggested_action && (
                    <p className="text-xs text-muted-foreground pl-[5.5rem]">
                      → {rec.suggested_action}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </RequirePermission>
  );
}
