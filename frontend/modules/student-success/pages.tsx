'use client';

import { useQuery } from '@tanstack/react-query';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { studentSuccessApi } from './api';
import type {
  StudentRetentionRuntime,
  StudentRegistryRuntimeSection,
  StudentSuccessRuntimeShellSection,
} from './types';

function RuntimeSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentSuccessRuntimeShellSection;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 grid gap-2 text-sm">
        <p>
          <span className="font-medium">Owner:</span> {section.owner_module}
        </p>
        <p>
          <span className="font-medium">Records:</span> {section.records}
        </p>
        <p>
          <span className="font-medium">Read-only:</span> {String(section.read_only)}
        </p>
        <p>
          <span className="font-medium">Aggregator-only:</span> {String(section.aggregator_only)}
        </p>
        <p>
          <span className="font-medium">Sources:</span> {section.source_modules.join(', ')}
        </p>
      </div>
    </section>
  );
}

function RegistrySectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentRegistryRuntimeSection;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 grid gap-2 text-sm">
        <p>
          <span className="font-medium">Owner:</span> {section.owner_module}
        </p>
        <p>
          <span className="font-medium">Records:</span> {section.records}
        </p>
        <p>
          <span className="font-medium">Read-only:</span> {String(section.read_only)}
        </p>
        <p>
          <span className="font-medium">Aggregator-only:</span> {String(section.aggregator_only)}
        </p>
        <p>
          <span className="font-medium">Sources:</span> {section.source_modules.join(', ')}
        </p>
      </div>
    </section>
  );
}

function RetentionSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentRetentionRuntime['retention_summary'];
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 grid gap-2 text-sm">
        <p>
          <span className="font-medium">Owner:</span> {section.owner_module}
        </p>
        <p>
          <span className="font-medium">Records:</span> {section.records}
        </p>
        <p>
          <span className="font-medium">Read-only:</span> {String(section.read_only)}
        </p>
        <p>
          <span className="font-medium">Aggregator-only:</span> {String(section.aggregator_only)}
        </p>
        <p>
          <span className="font-medium">Sources:</span> {section.source_modules.join(', ')}
        </p>
      </div>
    </section>
  );
}

export function StudentSuccessRuntimeShellPage() {
  const runtimeShell = useQuery({
    queryKey: ['student-success:runtime-shell'],
    queryFn: studentSuccessApi.getRuntimeShell,
    staleTime: 30000,
  });

  if (runtimeShell.isPending) {
    return <LoadingState title="Loading Student Success runtime shell" />;
  }

  if (runtimeShell.error) {
    return <ErrorState message="Failed to load Student Success runtime shell." error={runtimeShell.error} />;
  }

  if (!runtimeShell.data) {
    return <ErrorState message="Student Success runtime shell is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="student-success-runtime-shell">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Success Runtime Shell</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated shell for lifecycle, retention, risk, interventions, advisors, signals, and dashboard visibility.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <RuntimeSectionCard title="Student Success Overview" section={runtimeShell.data.student_success_overview} testId="student-success-overview" />
        <RuntimeSectionCard title="Lifecycle Summary" section={runtimeShell.data.lifecycle_summary} testId="student-success-lifecycle-summary" />
        <RuntimeSectionCard title="Retention Summary" section={runtimeShell.data.retention_summary} testId="student-success-retention-summary" />
        <RuntimeSectionCard title="Risk Summary" section={runtimeShell.data.risk_summary} testId="student-success-risk-summary" />
        <RuntimeSectionCard title="Intervention Summary" section={runtimeShell.data.intervention_summary} testId="student-success-intervention-summary" />
        <RuntimeSectionCard title="Advisor Summary" section={runtimeShell.data.advisor_summary} testId="student-success-advisor-summary" />
        <RuntimeSectionCard title="Signal Summary" section={runtimeShell.data.signal_summary} testId="student-success-signal-summary" />
        <RuntimeSectionCard title="Dashboard Summary" section={runtimeShell.data.dashboard_summary} testId="student-success-dashboard-summary" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-success-runtime-safety">
        <h2 className="text-lg font-semibold">Runtime safety</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Read-only: {String(runtimeShell.data.safety.read_only)}</p>
          <p>Aggregator-only: {String(runtimeShell.data.safety.aggregator_only)}</p>
          <p>Tenant-aware: {String(runtimeShell.data.safety.tenant_aware)}</p>
          <p>SUMMARY_READ required: {String(runtimeShell.data.safety.summary_read_required)}</p>
          <p>Workflow execution enabled: {String(runtimeShell.data.safety.workflow_execution_enabled)}</p>
          <p>Provider mutation enabled: {String(runtimeShell.data.safety.provider_mutation_enabled)}</p>
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
          {runtimeShell.data.safety.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function StudentRegistryRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-registry-runtime'],
    queryFn: studentSuccessApi.getStudentRegistryRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Registry runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Registry runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Registry runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="student-registry-runtime">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Registry Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated Student Registry runtime for enrollment, academic standing, lifecycle status, and advisor/risk/retention linkage surfaces.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard title="Student Registry Summary" section={runtime.data.student_registry_summary} testId="student-registry-summary" />
        <RegistrySectionCard title="Enrollment Summary" section={runtime.data.enrollment_summary} testId="student-registry-enrollment-summary" />
        <RegistrySectionCard title="Academic Standing Summary" section={runtime.data.academic_standing_summary} testId="student-registry-academic-standing-summary" />
        <RegistrySectionCard title="Retention Link Summary" section={runtime.data.retention_link_summary} testId="student-registry-retention-link-summary" />
        <RegistrySectionCard title="Advisor Link Summary" section={runtime.data.advisor_link_summary} testId="student-registry-advisor-link-summary" />
        <RegistrySectionCard title="Risk Link Summary" section={runtime.data.risk_link_summary} testId="student-registry-risk-link-summary" />
        <RegistrySectionCard title="Lifecycle Status Summary" section={runtime.data.lifecycle_status_summary} testId="student-registry-lifecycle-status-summary" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-registry-runtime-safety">
        <h2 className="text-lg font-semibold">Runtime safety</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Read-only: {String(runtime.data.safety.read_only)}</p>
          <p>Aggregator-only: {String(runtime.data.safety.aggregator_only)}</p>
          <p>Tenant-aware: {String(runtime.data.safety.tenant_aware)}</p>
          <p>SUMMARY_READ required: {String(runtime.data.safety.summary_read_required)}</p>
          <p>Write operations enabled: {String(runtime.data.safety.write_operations_enabled)}</p>
          <p>Workflow execution enabled: {String(runtime.data.safety.workflow_execution_enabled)}</p>
          <p>Approvals enabled: {String(runtime.data.safety.approval_execution_enabled)}</p>
          <p>Background jobs enabled: {String(runtime.data.safety.background_jobs_enabled)}</p>
          <p>Provider mutation enabled: {String(runtime.data.safety.provider_mutation_enabled)}</p>
          <p>Outbound calls enabled: {String(runtime.data.safety.outbound_calls_enabled)}</p>
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.safety.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function StudentRetentionRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-retention-runtime'],
    queryFn: studentSuccessApi.getStudentRetentionRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Retention runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Retention runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Retention runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="retention-runtime-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Retention Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated Student Retention runtime for retention scoring, risk and dropout visibility, persistence, trend, cohort, and retention signal surfaces.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <RetentionSectionCard title="Retention Score Distribution" section={runtime.data.retention_score_distribution} testId="retention-score-panel" />
        <RetentionSectionCard title="Retention Risk Distribution" section={runtime.data.retention_risk_distribution} testId="retention-risk-panel" />
        <RetentionSectionCard title="Dropout Risk Summary" section={runtime.data.dropout_risk_summary} testId="dropout-risk-panel" />
        <RetentionSectionCard title="Persistence Summary" section={runtime.data.persistence_summary} testId="persistence-panel" />
        <RetentionSectionCard title="Retention Trend Summary" section={runtime.data.retention_trend_summary} testId="retention-trend-panel" />
        <RetentionSectionCard title="Cohort Retention Summary" section={runtime.data.cohort_retention_summary} testId="cohort-retention-panel" />
        <RetentionSectionCard title="Retention Summary" section={runtime.data.retention_summary} testId="retention-summary-panel" />
        <RetentionSectionCard title="Retention Signal Summary" section={runtime.data.retention_signal_summary} testId="retention-signal-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-retention-runtime-safety">
        <h2 className="text-lg font-semibold">Runtime safety</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Read-only: {String(runtime.data.safety.read_only)}</p>
          <p>Aggregator-only: {String(runtime.data.safety.aggregator_only)}</p>
          <p>Tenant-aware: {String(runtime.data.safety.tenant_aware)}</p>
          <p>SUMMARY_READ required: {String(runtime.data.safety.summary_read_required)}</p>
          <p>Write operations enabled: {String(runtime.data.safety.write_operations_enabled)}</p>
          <p>Workflow execution enabled: {String(runtime.data.safety.workflow_execution_enabled)}</p>
          <p>Approvals enabled: {String(runtime.data.safety.approval_execution_enabled)}</p>
          <p>Background jobs enabled: {String(runtime.data.safety.background_jobs_enabled)}</p>
          <p>Outbound providers enabled: {String(runtime.data.safety.outbound_providers_enabled)}</p>
          <p>External integrations enabled: {String(runtime.data.safety.external_integrations_enabled)}</p>
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.safety.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}
