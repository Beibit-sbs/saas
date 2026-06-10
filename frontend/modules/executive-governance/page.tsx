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
  const assignments = useQuery({ queryKey: ['executive-governance:assignments'], queryFn: executiveGovernanceApi.getAssignments, staleTime: 30000 });
  const assignmentSummary = useQuery({ queryKey: ['executive-governance:assignments-summary'], queryFn: executiveGovernanceApi.getAssignmentSummary, staleTime: 30000 });
  const assignmentExecution = useQuery({ queryKey: ['executive-governance:assignments-execution'], queryFn: executiveGovernanceApi.getAssignmentExecution, staleTime: 30000 });
  const assignmentRisks = useQuery({ queryKey: ['executive-governance:assignments-risks'], queryFn: executiveGovernanceApi.getAssignmentRisks, staleTime: 30000 });
  const controlTower = useQuery({ queryKey: ['executive-governance:control-tower'], queryFn: executiveGovernanceApi.getControlTower, staleTime: 30000 });
  const controlTowerSummary = useQuery({ queryKey: ['executive-governance:control-tower-summary'], queryFn: executiveGovernanceApi.getControlTowerSummary, staleTime: 30000 });
  const controlTowerRisks = useQuery({ queryKey: ['executive-governance:control-tower-risks'], queryFn: executiveGovernanceApi.getControlTowerRisks, staleTime: 30000 });
  const controlTowerKpis = useQuery({ queryKey: ['executive-governance:control-tower-kpis'], queryFn: executiveGovernanceApi.getControlTowerKpis, staleTime: 30000 });
  const controlTowerEscalations = useQuery({ queryKey: ['executive-governance:control-tower-escalations'], queryFn: executiveGovernanceApi.getControlTowerEscalations, staleTime: 30000 });
  const meetings = useQuery({ queryKey: ['executive-governance:meetings'], queryFn: executiveGovernanceApi.getMeetings, staleTime: 30000 });
  const meetingSummary = useQuery({ queryKey: ['executive-governance:meetings-summary'], queryFn: executiveGovernanceApi.getMeetingSummary, staleTime: 30000 });
  const protocols = useQuery({ queryKey: ['executive-governance:protocols'], queryFn: executiveGovernanceApi.getProtocols, staleTime: 30000 });
  const protocolSummary = useQuery({ queryKey: ['executive-governance:protocols-summary'], queryFn: executiveGovernanceApi.getProtocolSummary, staleTime: 30000 });
  const protocolExecution = useQuery({ queryKey: ['executive-governance:protocols-execution'], queryFn: executiveGovernanceApi.getProtocolExecution, staleTime: 30000 });

  if (
    overview.isPending ||
    summary.isPending ||
    signals.isPending ||
    dashboard.isPending ||
    decisions.isPending ||
    decisionSummary.isPending ||
    decisionExecution.isPending ||
    assignments.isPending ||
    assignmentSummary.isPending ||
    assignmentExecution.isPending ||
    assignmentRisks.isPending ||
    controlTower.isPending ||
    controlTowerSummary.isPending ||
    controlTowerRisks.isPending ||
    controlTowerKpis.isPending ||
    controlTowerEscalations.isPending ||
    meetings.isPending ||
    meetingSummary.isPending ||
    protocols.isPending ||
    protocolSummary.isPending ||
    protocolExecution.isPending
  ) {
    return <LoadingState title="Loading Executive Governance runtime shell" />;
  }

  if (
    overview.error ||
    summary.error ||
    signals.error ||
    dashboard.error ||
    decisions.error ||
    decisionSummary.error ||
    decisionExecution.error ||
    assignments.error ||
    assignmentSummary.error ||
    assignmentExecution.error ||
    assignmentRisks.error ||
    controlTower.error ||
    controlTowerSummary.error ||
    controlTowerRisks.error ||
    controlTowerKpis.error ||
    controlTowerEscalations.error ||
    meetings.error ||
    meetingSummary.error ||
    protocols.error ||
    protocolSummary.error ||
    protocolExecution.error
  ) {
    return (
      <ErrorState
        message="Failed to load Executive Governance runtime shell."
        error={
          overview.error ??
          summary.error ??
          signals.error ??
          dashboard.error ??
          decisions.error ??
          decisionSummary.error ??
          decisionExecution.error ??
          assignments.error ??
          assignmentSummary.error ??
          assignmentExecution.error ??
          assignmentRisks.error ??
          controlTower.error ??
          controlTowerSummary.error ??
          controlTowerRisks.error ??
          controlTowerKpis.error ??
          controlTowerEscalations.error ??
          meetings.error ??
          meetingSummary.error ??
          protocols.error ??
          protocolSummary.error ??
          protocolExecution.error
        }
      />
    );
  }

  if (
    !overview.data ||
    !summary.data ||
    !signals.data ||
    !dashboard.data ||
    !decisions.data ||
    !decisionSummary.data ||
    !decisionExecution.data ||
    !assignments.data ||
    !assignmentSummary.data ||
    !assignmentExecution.data ||
    !assignmentRisks.data ||
    !controlTower.data ||
    !controlTowerSummary.data ||
    !controlTowerRisks.data ||
    !controlTowerKpis.data ||
    !controlTowerEscalations.data ||
    !meetings.data ||
    !meetingSummary.data ||
    !protocols.data ||
    !protocolSummary.data ||
    !protocolExecution.data
  ) {
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

        <section className="rounded-lg border p-4" aria-label="Assignment Summary" data-testid="assignment-summary-runtime">
          <h2 className="text-lg font-semibold">Assignment Summary</h2>
          <p className="mt-2 text-sm">Assignments: {assignmentSummary.data.total_assignments}</p>
          <p className="text-sm">Active assignments: {assignmentSummary.data.active_assignments}</p>
          <p className="text-sm">Completed assignments: {assignmentSummary.data.completed_assignments}</p>
          <p className="text-sm">Overdue items: {assignmentSummary.data.overdue_assignments}</p>
          <p className="text-sm">Escalated items: {assignmentSummary.data.escalated_assignments}</p>
          <p className="text-sm">Execution trend: {assignmentSummary.data.execution_trend}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Assignment Registry" data-testid="assignment-registry-runtime">
          <h2 className="text-lg font-semibold">Assignment Registry</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {assignments.data.map((entry) => (
              <div key={entry.assignment_id} className="rounded-lg border p-3">
                <p className="font-medium">{entry.assignment_title}</p>
                <p className="text-sm text-muted-foreground">{entry.assignment_id} | {entry.assignment_source}</p>
                <p className="text-sm">type={entry.assignment_type} / owner={entry.assigned_unit}</p>
                <p className="text-sm">assignee={entry.assigned_person}</p>
                <p className="text-sm">status={entry.execution_status} / risk={entry.risk_level}</p>
                <p className="text-sm">completion={entry.completion_percent}%</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" aria-label="Assignment Execution" data-testid="assignment-execution-runtime">
          <h2 className="text-lg font-semibold">Assignment Execution</h2>
          <p className="mt-2 text-sm">Execution performance: {assignmentExecution.data.execution_performance}%</p>
          <p className="text-sm">Execution trend: {assignmentExecution.data.execution_trend}</p>
          <p className="text-sm">Overdue assignments: {assignmentExecution.data.overdue_assignments}</p>
          <p className="text-sm">Escalated assignments: {assignmentExecution.data.escalated_assignments}</p>
          {Object.entries(assignmentExecution.data.execution_status_counts).map(([status, count]) => (
            <p key={status} className="text-sm">{status}: {count}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Execution Analytics" data-testid="execution-analytics-runtime">
          <h2 className="text-lg font-semibold">Execution Analytics</h2>
          {Object.entries(assignmentExecution.data.escalation_inventory).map(([key, value]) => (
            <p key={key} className="text-sm">{key}: {value}</p>
          ))}
          {Object.entries(assignmentExecution.data.escalation_summary).map(([key, value]) => (
            <p key={key} className="text-sm">{key}: {value}</p>
          ))}
          <p className="mt-2 text-sm">Escalation trends: {assignmentExecution.data.escalation_trends.join(', ')}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Escalation Center" data-testid="escalation-center-runtime">
          <h2 className="text-lg font-semibold">Escalation Center</h2>
          <p className="mt-2 text-sm">High risk assignment count: {assignmentRisks.data.high_risk_assignments.length}</p>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {assignmentRisks.data.high_risk_assignments.map((entry) => (
              <div key={entry.assignment_id} className="rounded-lg border p-3">
                <p className="font-medium">{entry.assignment_title}</p>
                <p className="text-sm text-muted-foreground">{entry.assignment_id} | {entry.assignment_source}</p>
                <p className="text-sm">status={entry.execution_status} / risk={entry.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" aria-label="Executive Signals" data-testid="executive-signals-runtime">
          <h2 className="text-lg font-semibold">Executive Signals</h2>
          <p className="mt-2 text-sm">{assignmentExecution.data.signal_families.join(', ')}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Executive Control Tower" data-testid="executive-control-tower-runtime">
          <h2 className="text-lg font-semibold">Executive Control Tower</h2>
          <p className="mt-2 text-sm">Total decisions: {controlTower.data.total_decisions}</p>
          <p className="text-sm">Total protocols: {controlTower.data.total_protocols}</p>
          <p className="text-sm">Total assignments: {controlTower.data.total_assignments}</p>
          <p className="text-sm">Execution rate: {controlTower.data.execution_rate}%</p>
          <p className="text-sm">Risk score: {controlTower.data.risk_score}</p>
          <p className="text-sm">KPI score: {controlTower.data.kpi_score}</p>
          <p className="text-sm">Executive workload: {controlTower.data.executive_workload}</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Rector Dashboard" data-testid="rector-dashboard-runtime">
          <h2 className="text-lg font-semibold">Rector Dashboard</h2>
          <p className="mt-2 text-sm">Rector overview owner: {controlTowerSummary.data.rector_overview.dashboard_owner_module}</p>
          <p className="text-sm">University execution rate: {controlTowerSummary.data.university_execution_status.execution_rate}%</p>
          <p className="text-sm">Completion rate: {controlTowerSummary.data.university_execution_status.completion_rate}%</p>
          <p className="text-sm">Escalation rate: {controlTowerSummary.data.university_execution_status.escalation_rate}%</p>
        </section>

        <section className="rounded-lg border p-4" aria-label="Executive KPI Center" data-testid="executive-kpi-center-runtime">
          <h2 className="text-lg font-semibold">Executive KPI Center</h2>
          <p className="mt-2 text-sm">KPI score: {controlTowerKpis.data.kpi_score}</p>
          <p className="text-sm">Execution rate: {controlTowerKpis.data.execution_rate}%</p>
          <p className="text-sm">Completion rate: {controlTowerKpis.data.completion_rate}%</p>
          <p className="text-sm">Escalation rate: {controlTowerKpis.data.escalation_rate}%</p>
          {Object.entries(controlTowerKpis.data.kpi_distribution).map(([key, value]) => (
            <p key={key} className="text-sm">{key}: {value}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Executive Risk Center" data-testid="executive-risk-center-runtime">
          <h2 className="text-lg font-semibold">Executive Risk Center</h2>
          <p className="mt-2 text-sm">Risk score: {controlTowerRisks.data.risk_score}</p>
          <p className="text-sm">High-risk assignments: {controlTowerRisks.data.high_risk_assignments.length}</p>
          {Object.entries(controlTowerRisks.data.high_risk_units).map(([key, value]) => (
            <p key={key} className="text-sm">unit {key}: {value}</p>
          ))}
          {Object.entries(controlTowerRisks.data.escalation_hotspots).map(([key, value]) => (
            <p key={key} className="text-sm">escalation hotspot {key}: {value}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Strategic Initiatives" data-testid="strategic-initiatives-runtime">
          <h2 className="text-lg font-semibold">Strategic Initiatives</h2>
          {Object.entries(controlTowerSummary.data.strategic_initiatives).map(([key, value]) => (
            <p key={key} className="text-sm">{key}: {value}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Escalation Center" data-testid="control-tower-escalation-runtime">
          <h2 className="text-lg font-semibold">Escalation Center</h2>
          <p className="mt-2 text-sm">Escalation rate: {controlTowerEscalations.data.escalation_rate}%</p>
          {Object.entries(controlTowerEscalations.data.workload_distribution).map(([key, value]) => (
            <p key={key} className="text-sm">workload {key}: {value}</p>
          ))}
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

        <section className="rounded-lg border p-4" aria-label="Meeting Registry" data-testid="meeting-registry-runtime">
          <h2 className="text-lg font-semibold">Meeting Registry</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {meetings.data.map((meeting) => (
              <div key={meeting.meeting_id} className="rounded-lg border p-3">
                <p className="font-medium">{meeting.meeting_title}</p>
                <p className="text-sm text-muted-foreground">{meeting.meeting_id} | {meeting.meeting_type}</p>
                <p className="text-sm">status={meeting.meeting_status} / execution={meeting.execution_status}</p>
                <p className="text-sm">protocols={meeting.protocol_count}, decisions={meeting.decision_count}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" aria-label="Meeting Analytics" data-testid="meeting-analytics-runtime">
          <h2 className="text-lg font-semibold">Meeting Analytics</h2>
          <p className="mt-2 text-sm">Total meetings: {meetingSummary.data.total_meetings}</p>
          <p className="text-sm">Protocols linked: {meetingSummary.data.total_protocols}</p>
          <p className="text-sm">Decisions linked: {meetingSummary.data.total_decisions}</p>
          {Object.entries(meetingSummary.data.meeting_status_counts).map(([status, count]) => (
            <p key={status} className="text-sm">{status}: {count}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Protocol Registry" data-testid="protocol-registry-runtime">
          <h2 className="text-lg font-semibold">Protocol Registry</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {protocols.data.map((protocol) => (
              <div key={protocol.protocol_id} className="rounded-lg border p-3">
                <p className="font-medium">{protocol.protocol_title}</p>
                <p className="text-sm text-muted-foreground">{protocol.protocol_number} | {protocol.protocol_status}</p>
                <p className="text-sm">decisions={protocol.decision_count}, assignments={protocol.assignment_count}</p>
                <p className="text-sm">progress={protocol.execution_progress}%</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" aria-label="Protocol Execution" data-testid="protocol-execution-runtime">
          <h2 className="text-lg font-semibold">Protocol Execution</h2>
          <p className="mt-2 text-sm">Average execution progress: {protocolExecution.data.average_execution_progress}%</p>
          <p className="text-sm">Overdue items: {protocolExecution.data.overdue_items}</p>
          <p className="text-sm">Escalated items: {protocolExecution.data.escalated_items}</p>
          {Object.entries(protocolExecution.data.linkage_inventory).map(([key, value]) => (
            <p key={key} className="text-sm">{key}: {value}</p>
          ))}
        </section>

        <section className="rounded-lg border p-4" aria-label="Protocol Signals" data-testid="protocol-signals-runtime">
          <h2 className="text-lg font-semibold">Protocol Signals</h2>
          <p className="mt-2 text-sm">{protocolExecution.data.signal_families.join(', ')}</p>
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
