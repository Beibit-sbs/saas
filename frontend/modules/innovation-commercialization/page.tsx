'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { innovationCommercializationApi } from './api';

export function InnovationCommercializationRuntimeShellPage() {
  const shell = useQuery({
    queryKey: ['innovation-commercialization:shell'],
    queryFn: innovationCommercializationApi.getShell,
    staleTime: 60000,
  });

  const opportunities = useQuery({
    queryKey: ['innovation-commercialization:opportunities'],
    queryFn: innovationCommercializationApi.listOpportunities,
    staleTime: 60000,
  });

  if (shell.isPending || opportunities.isPending) {
    return <LoadingState title="Loading Innovation / Commercialization runtime shell" />;
  }

  if (shell.error || opportunities.error) {
    return <ErrorState message="Failed to load Innovation / Commercialization runtime shell." error={shell.error ?? opportunities.error} />;
  }

  if (!shell.data || !opportunities.data) {
    return <ErrorState message="Innovation / Commercialization runtime shell is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_SCIENCE_OVERVIEW_READ}>
      <div className="space-y-6" data-testid="innovation-commercialization-runtime-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Innovation / Commercialization Extension Shell</h1>
          <p className="text-sm text-muted-foreground">
            Extension-only read model over closed Research Brain foundations. No external live provider execution.
          </p>
        </header>

        <section className="rounded-lg border p-4" data-testid="innovation-commercialization-overview">
          <h2 className="text-lg font-semibold">Boundary Overview</h2>
          <p className="mt-2 text-sm">Owner: {shell.data.owner_module}</p>
          <p className="text-sm">Runtime mode: {shell.data.runtime_mode}</p>
          <p className="text-sm">Base vertical: {shell.data.canonical_base_vertical}</p>
          <p className="text-sm">Integration policy: {shell.data.integration_policy}</p>
          <p className="mt-2 text-sm text-muted-foreground">{shell.data.extension_boundary}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {shell.data.bridge_modules.map((module) => (
              <span key={module} className="rounded-full border px-3 py-1">{module}</span>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="innovation-commercialization-opportunities">
          <h2 className="text-lg font-semibold">Opportunity Signals</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {opportunities.data.items.map((item) => (
              <div key={item.opportunity_id} className="rounded-lg border p-3">
                <p className="font-medium">{item.title}</p>
                <p className="text-sm text-muted-foreground">{item.opportunity_id}</p>
                <p className="text-sm">Stage: {item.stage}</p>
                <p className="text-sm">Readiness: {item.readiness}</p>
                <p className="text-sm">Source module: {item.source_module}</p>
                <p className="text-xs text-muted-foreground">{item.notes}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="innovation-commercialization-navigation-links">
          <h2 className="text-lg font-semibold">Extension Navigation</h2>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Link href="/console/research-brain" className="rounded-full border px-3 py-1">Research Brain</Link>
            <Link href="/console/research-science" className="rounded-full border px-3 py-1">Research Science</Link>
            <Link href="/console/research-grants" className="rounded-full border px-3 py-1">Research Grants</Link>
            <Link href="/console/research-ethics" className="rounded-full border px-3 py-1">Research Ethics</Link>
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}
