'use client';

import { useQuery } from '@tanstack/react-query';

import { executiveGovernanceApi } from './api';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export function ExecutiveGovernanceRuntimeShellPage() {
  const overview = useQuery({ queryKey: ['executive-governance:overview'], queryFn: executiveGovernanceApi.getOverview, staleTime: 30000 });
  const summary = useQuery({ queryKey: ['executive-governance:summary'], queryFn: executiveGovernanceApi.getSummary, staleTime: 30000 });
  const signals = useQuery({ queryKey: ['executive-governance:signals'], queryFn: executiveGovernanceApi.getSignals, staleTime: 30000 });
  const dashboard = useQuery({ queryKey: ['executive-governance:dashboard'], queryFn: executiveGovernanceApi.getDashboard, staleTime: 30000 });
  const decisions = useQuery({ queryKey: ['executive-governance:decisions'], queryFn: executiveGovernanceApi.getDecisions, staleTime: 30000 });
  const decisionSummary = useQuery({ queryKey: ['executive-governance:decision-summary'], queryFn: executiveGovernanceApi.getDecisionSummary, staleTime: 30000 });
  const decisionExecution = useQuery({ queryKey: ['executive-governance:decision-execution'], queryFn: executiveGovernanceApi.getDecisionExecution, staleTime: 30000 });

  if (overview.isPending || summary.isPending || signals.isPending || dashboard.isPending || decisions.isPending || decisionSummary.isPending || decisionExecution.isPending) {
    return <LoadingState title="Loading Executive Governance runtime shell" />;
  }

  if (overview.error || summary.error || signals.error || dashboard.error || decisions.error || decisionSummary.error || decisionExecution.error) {
    return <ErrorState message="Failed to load Executive Governance runtime shell." error={overview.error ?? summary.error ?? signals.error ?? dashboard.error ?? decisions.error ?? decisionSummary.error ?? decisionExecution.error} />;
  }

  if (!overview.data || !summary.data || !signals.data || !dashboard.data || !decisions.data || !decisionSummary.data || !decisionExecution.data) {
    return <ErrorState message="Executive Governance runtime shell is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.EXECUTIVE_CONTROL_TOWER_SUMMARY_READ}>
      <div className="space-y-6" data-testid="executive-governance-runtime-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Executive Governance Runtime Shell</h1>
          <p className="text-sm text-muted-foreground">
            Canonical read-only runtime composed from executive_control_tower, rector_assignment_workflow, committee_decision_registry, order_decree_registry, analytics, and brain_core.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-label="Executive Overview">
          <SummaryCard label="Executive Assignments" value={overview.data.executive_assignments} />
          <SummaryCard label="Executive Decisions" value={overview.data.executive_decisions} />
          <SummaryCard label="Executive Protocols" value={overview.data.executive_protocols} />
          <SummaryCard label="Executive Meetings" value={overview.data.executive_meetings} />
        </section>

        <section className="rounded-lg border p-4" aria-label="Decision Summary">
          <h2 className="text-lg font-semibold">Decision Summary</h2>
          <p className="mt-2 text-sm">Total decisions: {decisionSummary.data.total_decisions}</p>
          <p className="text-sm text-muted-foreground">Owner modules: {summary.data.owner_modules.join(', ')}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Executive Decisions" data-testid="executive-decision-registry-view">
          <h2 className="text-lg font-semibold">Executive Decisions</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {decisions.data.map((entry) => (
              <div key={entry.decision_id} className="rounded-lg border p-3">
                <p className="font-medium">{entry.decision_title}</p>
                <p className="text-sm text-muted-foreground">{entry.decision_id} | {entry.decision_source}</p>
                <p className="text-sm">status={entry.decision_status} / execution={entry.execution_status}</p>
                <p className="text-sm">progress={entry.execution_progress}%</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" aria-label="Decision Sources">
          <h2 className="text-lg font-semibold">Decision Sources</h2>
          {Object.entries(decisionSummary.data.decision_sources).map(([source, count]) => (
            <p key={source} className="text-sm">{source}: {count}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Execution Status" data-testid="decision-execution-summary">
          <h2 className="text-lg font-semibold">Execution Status</h2>
          {Object.entries(decisionExecution.data.execution_status_counts).map(([status, count]) => (
            <p key={status} className="text-sm">{status}: {count}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Escalation Summary">
          <h2 className="text-lg font-semibold">Escalation Summary</h2>
          <p className="mt-2 text-sm">Overdue items: {decisionExecution.data.overdue_items}</p>
          <p className="text-sm">Escalated items: {decisionExecution.data.escalated_items}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Assignment Summary">
          <h2 className="text-lg font-semibold">Assignment Summary</h2>
          <p className="mt-2 text-sm">Assignments: {summary.data.executive_assignments}</p>
          <p className="text-sm">Overdue items: {summary.data.overdue_items}</p>
          <p className="text-sm">Escalated items: {summary.data.escalated_items}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Protocol Summary">
          <h2 className="text-lg font-semibold">Protocol Summary</h2>
          <p className="mt-2 text-sm">Protocols: {summary.data.executive_protocols}</p>
          <p className="text-sm">Strategic items: {summary.data.strategic_items}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Signal Summary" data-testid="executive-governance-signal-summary">
          <h2 className="text-lg font-semibold">Signal Summary</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {signals.data.map((signal) => (
              <div key={signal.signal_family} className="rounded-lg border p-3">
                <p className="font-medium">{signal.signal_family}</p>
                <p className="text-sm text-muted-foreground">owner={signal.owner_module}</p>
                <p className="text-sm">source={signal.source_module}</p>
                <p className="text-sm">observed={signal.observed_items}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" aria-label="Decision Signals" data-testid="decision-signal-summary">
          <h2 className="text-lg font-semibold">Decision Signals</h2>
          <p className="mt-2 text-sm">{decisionExecution.data.signal_families.join(', ')}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Dashboard Summary" data-testid="executive-governance-dashboard-summary">
          <h2 className="text-lg font-semibold">Dashboard Summary</h2>
          <p className="mt-2 text-sm">Dashboard owner: {dashboard.data.dashboard_owner_module}</p>
          <p className="text-sm">View: {dashboard.data.dashboard_view}</p>
          <p className="text-sm">Read-only: {String(dashboard.data.read_only)}</p>
          <p className="text-sm">Auditability preserved: {String(dashboard.data.auditability_preserved)}</p>
          <p className="text-sm">RBAC roles: {dashboard.data.rbac_roles.join(', ')}</p>
        </section>
      </div>
    </RequirePermission>
  );
}

export default ExecutiveGovernanceRuntimeShellPage;
