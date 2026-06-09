'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { PERMISSIONS } from '@/shared/config/permissions';
import { researchBrainApi } from './api';

function MetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

export function ResearchBrainRuntimeShellPage() {
  const shell = useQuery({ queryKey: ['research-brain:shell'], queryFn: researchBrainApi.getShell, staleTime: 60000 });
  const orchestration = useQuery({ queryKey: ['research-brain:orchestration'], queryFn: researchBrainApi.getOrchestration, staleTime: 30000 });
  const context = useQuery({ queryKey: ['research-brain:context'], queryFn: researchBrainApi.getContext, staleTime: 30000 });
  const kpis = useQuery({ queryKey: ['research-brain:kpis'], queryFn: researchBrainApi.getKpis, staleTime: 30000 });
  const signals = useQuery({ queryKey: ['research-brain:signals'], queryFn: researchBrainApi.getSignals, staleTime: 30000 });
  const rbac = useQuery({ queryKey: ['research-brain:rbac'], queryFn: researchBrainApi.getRbacValidation, staleTime: 30000 });

  if (shell.isPending || orchestration.isPending || context.isPending || kpis.isPending || signals.isPending || rbac.isPending) {
    return <LoadingState title="Loading Research Brain runtime shell" />;
  }

  if (shell.error || orchestration.error || context.error || kpis.error || signals.error || rbac.error) {
    return <ErrorState message="Failed to load Research Brain runtime shell." error={shell.error ?? orchestration.error ?? context.error ?? kpis.error ?? signals.error ?? rbac.error} />;
  }

  if (!shell.data || !orchestration.data || !context.data || !kpis.data || !signals.data || !rbac.data) {
    return <ErrorState message="Research Brain runtime shell is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_SCIENCE_OVERVIEW_READ}>
      <div className="space-y-6" data-testid="research-brain-runtime-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Research Brain Runtime Shell</h1>
          <p className="text-sm text-muted-foreground">
            Unified read-only shell over existing canonicals and approved bridge contracts. No live provider integrations.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Publications" value={kpis.data.publication_count} helper="Analytics-owned KPI surface" />
          <MetricCard label="Grants" value={kpis.data.grant_count} helper="Analytics-owned KPI surface" />
          <MetricCard label="Projects" value={kpis.data.project_count} helper="Analytics-owned KPI surface" />
          <MetricCard label="Ethics" value={kpis.data.ethics_count} helper="Analytics-owned KPI surface" />
        </div>

        <section className="rounded-lg border p-4" data-testid="research-brain-bridge-modules">
          <h2 className="text-lg font-semibold">Bridge Modules</h2>
          <p className="mt-1 text-sm text-muted-foreground">Owner: {shell.data.owner_module}. Boundary: {shell.data.runtime_boundary}.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {shell.data.bridge_modules.map((bridge) => (
              <span key={bridge} className="rounded-full border px-3 py-1 text-xs">{bridge}</span>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2" data-testid="research-brain-orchestration">
          {Object.entries(orchestration.data)
            .filter(([key]) => key !== 'tenant_id')
            .map(([key, item]) => {
              const typed = item as { source_module: string; read_only: boolean; total: number; notes: string };
              return (
                <div key={key} className="rounded-lg border p-4">
                  <h3 className="font-medium capitalize">{key}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">Source: {typed.source_module}</p>
                  <p className="mt-1 text-sm">Total: {typed.total}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{typed.notes}</p>
                </div>
              );
            })}
        </section>

        <section className="rounded-lg border p-4" data-testid="research-brain-signals">
          <h2 className="text-lg font-semibold">Signal Exposure</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {signals.data.signals.map((signal) => (
              <div key={signal.family} className="rounded-lg border p-3">
                <p className="font-medium">{signal.family}</p>
                <p className="text-sm text-muted-foreground">Owner: {signal.owner}</p>
                <p className="text-sm text-muted-foreground">Review queue: {signal.review_queue}</p>
                <p className="text-sm">Observed: {signal.observed_count}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="research-brain-rbac-validation">
          <h2 className="text-lg font-semibold">RBAC Validation</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            tenant={rbac.data.tenant}, rbac={rbac.data.rbac}, audit={rbac.data.audit}
          </p>
          <ul className="mt-3 space-y-1 text-sm">
            {rbac.data.roles.map((role) => (
              <li key={role.role}>{role.role}: {role.status}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border p-4" data-testid="research-brain-navigation-links">
          <h2 className="text-lg font-semibold">Runtime Navigation</h2>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Link href="/console/research-science" className="rounded-full border px-3 py-1">Research Science Overview</Link>
            <Link href="/console/research-science/dashboard" className="rounded-full border px-3 py-1">Research Science Dashboard</Link>
            <Link href="/console/research-grants" className="rounded-full border px-3 py-1">Research Grants</Link>
            <Link href="/console/research-ethics" className="rounded-full border px-3 py-1">Research Ethics</Link>
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}
