'use client';

import { useQuery } from '@tanstack/react-query';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { studentSuccessApi } from './api';
import type {
  StudentAdvisorRuntime,
  StudentAcademicRiskRuntime,
  StudentAttendanceRiskRuntime,
  StudentInterventionRuntime,
  StudentRetentionRuntime,
  StudentRegistryRuntimeSection,
  StudentSuccessSignalsRuntime,
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

function AcademicRiskSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentAcademicRiskRuntime['academic_risk_summary'];
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

function AttendanceRiskSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentAttendanceRiskRuntime['attendance_risk_summary'];
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

function InterventionSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentInterventionRuntime['intervention_summary'];
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

function AdvisorSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentAdvisorRuntime['advisor_summary'];
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

function SuccessSignalsSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: StudentSuccessSignalsRuntime['success_signal_summary'];
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

export function StudentAcademicRiskRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-academic-risk-runtime'],
    queryFn: studentSuccessApi.getStudentAcademicRiskRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Academic Risk runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Academic Risk runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Academic Risk runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="academic-risk-runtime-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Academic Risk Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated Student Academic Risk runtime for GPA, failed course, low performance, probation, progression risk, and academic alerts.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <AcademicRiskSectionCard title="Academic Risk Summary" section={runtime.data.academic_risk_summary} testId="academic-risk-summary-panel" />
        <AcademicRiskSectionCard title="GPA Risk Distribution" section={runtime.data.gpa_risk_distribution} testId="gpa-risk-panel" />
        <AcademicRiskSectionCard title="Failed Course Risk Summary" section={runtime.data.failed_course_risk_summary} testId="failed-course-risk-panel" />
        <AcademicRiskSectionCard title="Probation Summary" section={runtime.data.probation_summary} testId="probation-panel" />
        <AcademicRiskSectionCard title="Progression Risk Summary" section={runtime.data.progression_risk_summary} testId="progression-risk-panel" />
        <AcademicRiskSectionCard title="Academic Alert Summary" section={runtime.data.academic_alert_summary} testId="academic-alert-panel" />
        <AcademicRiskSectionCard title="Low Performance Summary" section={runtime.data.low_performance_summary} testId="low-performance-panel" />
        <AcademicRiskSectionCard title="Academic Signal Summary" section={runtime.data.academic_signal_summary} testId="academic-signal-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-academic-risk-runtime-safety">
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
          <p>Outbound integrations enabled: {String(runtime.data.safety.outbound_integrations_enabled)}</p>
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

export function StudentAttendanceRiskRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-attendance-risk-runtime'],
    queryFn: studentSuccessApi.getStudentAttendanceRiskRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Attendance Risk runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Attendance Risk runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Attendance Risk runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="attendance-risk-runtime-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Attendance Risk Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated Student Attendance Risk runtime for absence, chronic absence, missed class, trend, punctuality, engagement, and attendance signals.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <AttendanceRiskSectionCard title="Attendance Risk Summary" section={runtime.data.attendance_risk_summary} testId="attendance-risk-summary-panel" />
        <AttendanceRiskSectionCard title="Absence Distribution" section={runtime.data.absence_distribution} testId="absence-distribution-panel" />
        <AttendanceRiskSectionCard title="Chronic Absence Summary" section={runtime.data.chronic_absence_summary} testId="chronic-absence-panel" />
        <AttendanceRiskSectionCard title="Missed Class Summary" section={runtime.data.missed_class_summary} testId="missed-class-panel" />
        <AttendanceRiskSectionCard title="Attendance Trend Summary" section={runtime.data.attendance_trend_summary} testId="attendance-trend-panel" />
        <AttendanceRiskSectionCard title="Punctuality Summary" section={runtime.data.punctuality_summary} testId="punctuality-panel" />
        <AttendanceRiskSectionCard title="Engagement Attendance Summary" section={runtime.data.engagement_attendance_summary} testId="engagement-attendance-panel" />
        <AttendanceRiskSectionCard title="Attendance Signal Summary" section={runtime.data.attendance_signal_summary} testId="attendance-signal-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-attendance-risk-runtime-safety">
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
          <p>Outbound integrations enabled: {String(runtime.data.safety.outbound_integrations_enabled)}</p>
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

export function StudentInterventionRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-intervention-runtime'],
    queryFn: studentSuccessApi.getStudentInterventionRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Intervention runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Intervention runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Intervention runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="intervention-runtime-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Intervention Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated intervention intelligence for advisors, curators, deans, and student success teams.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <InterventionSectionCard title="Intervention Summary" section={runtime.data.intervention_summary} testId="intervention-summary-panel" />
        <InterventionSectionCard title="Intervention Priority Groups" section={runtime.data.intervention_priority_groups} testId="intervention-priority-panel" />
        <InterventionSectionCard title="Intervention Recommendations" section={runtime.data.intervention_recommendations} testId="intervention-recommendations-panel" />
        <InterventionSectionCard title="Advisor Interventions" section={runtime.data.advisor_interventions} testId="advisor-interventions-panel" />
        <InterventionSectionCard title="Dean Interventions" section={runtime.data.dean_interventions} testId="dean-interventions-panel" />
        <InterventionSectionCard title="Support Programs" section={runtime.data.support_programs} testId="support-programs-panel" />
        <InterventionSectionCard title="Intervention Effectiveness Signals" section={runtime.data.intervention_effectiveness_signals} testId="intervention-effectiveness-panel" />
        <InterventionSectionCard title="Intervention Signal Summary" section={runtime.data.intervention_signal_summary} testId="intervention-signal-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-intervention-runtime-safety">
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
          <p>Notifications enabled: {String(runtime.data.safety.notification_execution_enabled)}</p>
          <p>Provider mutation enabled: {String(runtime.data.safety.provider_mutation_enabled)}</p>
          <p>Outbound integrations enabled: {String(runtime.data.safety.outbound_integrations_enabled)}</p>
          <p>Intervention execution enabled: {String(runtime.data.safety.intervention_execution_enabled)}</p>
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

export function StudentAdvisorRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-advisor-runtime'],
    queryFn: studentSuccessApi.getStudentAdvisorRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Advisor runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Advisor runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Advisor runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="advisor-runtime-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Advisor Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated advisor intelligence for workload balancing, student assignments, follow-up sequencing, and risk coverage.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <AdvisorSectionCard title="Advisor Summary" section={runtime.data.advisor_summary} testId="advisor-summary-panel" />
        <AdvisorSectionCard title="Advisor Workload Distribution" section={runtime.data.advisor_workload_distribution} testId="advisor-workload-panel" />
        <AdvisorSectionCard title="Advisor Student Assignments" section={runtime.data.advisor_student_assignments} testId="advisor-assignment-panel" />
        <AdvisorSectionCard title="Advisor Intervention Queue" section={runtime.data.advisor_intervention_queue} testId="advisor-queue-panel" />
        <AdvisorSectionCard title="Advisor Follow-up Summary" section={runtime.data.advisor_follow_up_summary} testId="advisor-followup-panel" />
        <AdvisorSectionCard title="Advisor Risk Coverage" section={runtime.data.advisor_risk_coverage} testId="advisor-risk-coverage-panel" />
        <AdvisorSectionCard title="Advisor Effectiveness Summary" section={runtime.data.advisor_effectiveness_summary} testId="advisor-effectiveness-panel" />
        <AdvisorSectionCard title="Advisor Signal Summary" section={runtime.data.advisor_signal_summary} testId="advisor-signal-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-advisor-runtime-safety">
        <h2 className="text-lg font-semibold">Runtime safety</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Read-only: {String(runtime.data.safety.read_only)}</p>
          <p>Aggregator-only: {String(runtime.data.safety.aggregator_only)}</p>
          <p>Tenant-aware: {String(runtime.data.safety.tenant_aware)}</p>
          <p>SUMMARY_READ required: {String(runtime.data.safety.summary_read_required)}</p>
          <p>Write operations enabled: {String(runtime.data.safety.write_operations_enabled)}</p>
          <p>Intervention execution enabled: {String(runtime.data.safety.intervention_execution_enabled)}</p>
          <p>Workflow execution enabled: {String(runtime.data.safety.workflow_execution_enabled)}</p>
          <p>Approvals enabled: {String(runtime.data.safety.approval_execution_enabled)}</p>
          <p>Background jobs enabled: {String(runtime.data.safety.background_jobs_enabled)}</p>
          <p>Notifications enabled: {String(runtime.data.safety.notification_execution_enabled)}</p>
          <p>Provider mutation enabled: {String(runtime.data.safety.provider_mutation_enabled)}</p>
          <p>Outbound integrations enabled: {String(runtime.data.safety.outbound_integrations_enabled)}</p>
          <p>Scheduling engine enabled: {String(runtime.data.safety.scheduling_engine_enabled)}</p>
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

export function StudentSuccessSignalsRuntimePage() {
  const runtime = useQuery({
    queryKey: ['student-success:student-success-signals-runtime'],
    queryFn: studentSuccessApi.getStudentSuccessSignalsRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Student Success Signals runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Student Success Signals runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Student Success Signals runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="success-signals-runtime-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Student Success Signals Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregated signal intelligence across retention, academic risk, attendance risk, interventions, and advisor outcomes.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <SuccessSignalsSectionCard title="Signal Summary" section={runtime.data.success_signal_summary} testId="signal-summary-panel" />
        <SuccessSignalsSectionCard title="Retention Signals" section={runtime.data.retention_signals} testId="retention-signals-panel" />
        <SuccessSignalsSectionCard title="Academic Signals" section={runtime.data.academic_signals} testId="academic-signals-panel" />
        <SuccessSignalsSectionCard title="Attendance Signals" section={runtime.data.attendance_signals} testId="attendance-signals-panel" />
        <SuccessSignalsSectionCard title="Intervention Signals" section={runtime.data.intervention_signals} testId="intervention-signals-panel" />
        <SuccessSignalsSectionCard title="Advisor Signals" section={runtime.data.advisor_signals} testId="advisor-signals-panel" />
        <SuccessSignalsSectionCard title="Early Warning Signals" section={runtime.data.early_warning_signals} testId="early-warning-panel" />
        <SuccessSignalsSectionCard title="Success Indicator Signals" section={runtime.data.success_indicator_signals} testId="success-indicators-panel" />
        <SuccessSignalsSectionCard title="Signal Trend Summary" section={runtime.data.signal_trend_summary} testId="signal-trends-panel" />
        <SuccessSignalsSectionCard title="Signal Scorecard" section={runtime.data.signal_scorecard} testId="signal-scorecard-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="student-success-signals-runtime-safety">
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
          <p>Notifications enabled: {String(runtime.data.safety.notification_execution_enabled)}</p>
          <p>Provider mutation enabled: {String(runtime.data.safety.provider_mutation_enabled)}</p>
          <p>Outbound integrations enabled: {String(runtime.data.safety.outbound_integrations_enabled)}</p>
          <p>Scheduling engine enabled: {String(runtime.data.safety.scheduling_engine_enabled)}</p>
          <p>Signal execution engine enabled: {String(runtime.data.safety.signal_execution_engine_enabled)}</p>
          <p>Persistence enabled: {String(runtime.data.safety.persistence_enabled)}</p>
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
