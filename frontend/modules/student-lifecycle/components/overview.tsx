import { EXPECTED_DATA_SOURCE } from '../constants';
import type { StudentLifecycleDashboardResponse, StudentLifecycleHealthResponse } from '../types';
import {
  IncompleteDataNotice,
  MetadataOnlyNotice,
  NoAutomatedDecisionBadge,
  NoHiddenScoreBadge,
  ProviderNotEnabledBadge,
  StudentLifecycleBoundaryBanner,
  StudentLifecycleLimitationsPanel,
} from './boundaries';

function humanize(value: string) {
  return value.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function StudentLifecycleMetricCard({ label, value, testId }: { label: string; value: number; testId?: string }) {
  return (
    <div className="rounded-lg border p-4" data-testid={testId}>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export function StudentLifecycleStatusBreakdown({ title, counts }: { title: string; counts: Record<string, number> }) {
  const entries = Object.entries(counts);
  return (
    <section className="rounded-lg border p-4" data-testid={`student-lifecycle-breakdown-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <h3 className="text-sm font-semibold">{title}</h3>
      {entries.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {entries.map(([status, count]) => (
            <li key={status} className="flex items-center justify-between">
              <span>{humanize(status)}</span>
              <span className="font-medium">{count}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No records yet.</p>
      )}
    </section>
  );
}

export function StudentLifecycleHumanReviewQueue({ count }: { count: number }) {
  return (
    <section className="rounded-lg border p-4" data-testid="student-lifecycle-human-review-queue">
      <h3 className="text-sm font-semibold">Human review queue</h3>
      <p className="mt-2 text-2xl font-semibold">{count}</p>
      <p className="mt-1 text-sm text-muted-foreground">Items currently require an explicit human step.</p>
    </section>
  );
}

export function StudentLifecycleRiskBoundaryPanel({ health }: { health: StudentLifecycleHealthResponse }) {
  return (
    <section className="rounded-lg border p-4" data-testid="student-lifecycle-risk-boundary-panel">
      <h3 className="text-sm font-semibold">Boundary status</h3>
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="rounded-full border px-2.5 py-1 text-xs" data-testid="fake-metrics-label">
          fake_metrics={String(health.fake_metrics)}
        </span>
        <span className="rounded-full border px-2.5 py-1 text-xs" data-testid="data-source-label">
          data_source={health.data_source}
        </span>
        <span className="rounded-full border px-2.5 py-1 text-xs" data-testid="provider-integration-label">
          provider_integration_enabled={String(health.provider_integration_enabled)}
        </span>
        <span className="rounded-full border px-2.5 py-1 text-xs" data-testid="hidden-score-label">
          hidden_score_present={String(health.hidden_score_present)}
        </span>
      </div>
      <p className="mt-3 text-sm text-muted-foreground">
        Route count {health.route_count} · Table count {health.table_count} · Data source {EXPECTED_DATA_SOURCE}
      </p>
    </section>
  );
}

export function StudentLifecycleOverviewDashboard({
  dashboard,
  health,
}: {
  dashboard: StudentLifecycleDashboardResponse;
  health: StudentLifecycleHealthResponse;
}) {
  return (
    <div className="space-y-6" data-testid="student-lifecycle-overview-dashboard">
      <StudentLifecycleBoundaryBanner
        title="Student Lifecycle overview boundaries"
        labels={[
          'Human review required',
          'No automated decision is made',
          'Provider integration not enabled',
        ]}
      >
        <div className="mt-2 flex flex-wrap gap-2">
          <NoAutomatedDecisionBadge />
          <ProviderNotEnabledBadge />
          <NoHiddenScoreBadge />
          {dashboard.incomplete_data ? <IncompleteDataNotice /> : null}
          <MetadataOnlyNotice />
        </div>
      </StudentLifecycleBoundaryBanner>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StudentLifecycleMetricCard label="Applicants tracked" value={Object.values(dashboard.applicant_counts_by_status).reduce((sum, count) => sum + count, 0)} testId="student-lifecycle-applicant-metric" />
        <StudentLifecycleMetricCard label="Students tracked" value={Object.values(dashboard.student_counts_by_status).reduce((sum, count) => sum + count, 0)} />
        <StudentLifecycleMetricCard label="Human review required" value={dashboard.human_review_required_count} />
        <StudentLifecycleMetricCard label="Automated decisions" value={dashboard.automated_decision_count} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <StudentLifecycleStatusBreakdown title="Applicants" counts={dashboard.applicant_counts_by_status} />
        <StudentLifecycleStatusBreakdown title="Students" counts={dashboard.student_counts_by_status} />
        <StudentLifecycleStatusBreakdown title="Enrollment" counts={dashboard.enrollment_counts_by_status} />
        <StudentLifecycleStatusBreakdown title="Transcript previews" counts={dashboard.transcript_preview_counts} />
        <StudentLifecycleStatusBreakdown title="Degree progress" counts={dashboard.degree_progress_counts} />
        <StudentLifecycleStatusBreakdown title="Requests" counts={dashboard.request_counts_by_status} />
        <StudentLifecycleStatusBreakdown title="Appeals" counts={dashboard.appeal_counts_by_status} />
        <StudentLifecycleStatusBreakdown title="Interventions" counts={dashboard.intervention_counts_by_status} />
        <StudentLifecycleHumanReviewQueue count={dashboard.human_review_required_count} />
      </div>

      <StudentLifecycleRiskBoundaryPanel health={health} />
      <StudentLifecycleLimitationsPanel limitations={dashboard.limitations} />
    </div>
  );
}