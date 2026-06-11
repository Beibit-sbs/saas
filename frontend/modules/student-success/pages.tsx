'use client';

import { useQuery } from '@tanstack/react-query';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { studentSuccessApi } from './api';
import type { StudentSuccessRuntimeShellSection } from './types';

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
