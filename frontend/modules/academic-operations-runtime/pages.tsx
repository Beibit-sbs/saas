'use client';

import { useQuery } from '@tanstack/react-query';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { academicOperationsRuntimeApi } from './api';
import type { AcademicOperationsRuntimeShellSection } from './types';

function RuntimeSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: AcademicOperationsRuntimeShellSection;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-2 space-y-1 text-sm">
        <p>
          <span className="font-medium">Owner module:</span> {section.owner_module}
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

export function AcademicOperationsRuntimeShellPage() {
  const runtimeShell = useQuery({
    queryKey: ['academic-operations:runtime-shell'],
    queryFn: academicOperationsRuntimeApi.getRuntimeShell,
    staleTime: 30000,
  });

  if (runtimeShell.isPending) {
    return <LoadingState title="Loading Academic Operations runtime shell" />;
  }

  if (runtimeShell.error) {
    return <ErrorState message="Failed to load Academic Operations runtime shell." error={runtimeShell.error} />;
  }

  if (!runtimeShell.data) {
    return <ErrorState message="Academic Operations runtime shell is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="academic-operations-runtime-shell">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Academic Operations Runtime Shell</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregator shell for Academic Operations runtime visibility and readiness boundaries.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <RuntimeSectionCard title="Runtime Shell Summary" section={runtimeShell.data.runtime_shell_summary} testId="runtime-shell-summary-panel" />
        <RuntimeSectionCard title="Runtime Domain" section={runtimeShell.data.runtime_shell_domain} testId="runtime-shell-domain-panel" />
        <RuntimeSectionCard title="Runtime Surface" section={runtimeShell.data.runtime_shell_runtime} testId="runtime-shell-runtime-panel" />
        <RuntimeSectionCard title="Runtime Integration" section={runtimeShell.data.runtime_shell_integration} testId="runtime-shell-integration-panel" />
        <RuntimeSectionCard title="Runtime Readiness" section={runtimeShell.data.runtime_shell_readiness} testId="runtime-shell-readiness-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="academic-operations-runtime-safety">
        <h2 className="text-lg font-semibold">Runtime safety</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Read-only: {String(runtimeShell.data.safety.read_only)}</p>
          <p>Aggregator-only: {String(runtimeShell.data.safety.aggregator_only)}</p>
          <p>Tenant-aware: {String(runtimeShell.data.safety.tenant_aware)}</p>
          <p>SUMMARY_READ required: {String(runtimeShell.data.safety.summary_read_required)}</p>
          <p>Workflow execution enabled: {String(runtimeShell.data.safety.workflow_execution_enabled)}</p>
          <p>Approval execution enabled: {String(runtimeShell.data.safety.approval_execution_enabled)}</p>
          <p>Background jobs enabled: {String(runtimeShell.data.safety.background_jobs_enabled)}</p>
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
