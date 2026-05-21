'use client';

import { useState } from 'react';
import { DrawerPanel } from '@/shared/ui/drawer-panel';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { DataSourceGuardPanel } from './DataSourceGuardPanel';
import { EvidenceLinkList, MetricLimitationsPanel } from './EvidenceLinkList';
import { useMetricDetail } from '../hooks';
import type { ExecutiveControlTowerMetric, MetricRegistryResponse } from '../types';

function flattenMetrics(registry: MetricRegistryResponse) {
  return registry.groups.flatMap((group) => group.metrics);
}

export function MetricDetailDrawer({ metricId, open, onClose }: { metricId: string | null; open: boolean; onClose: () => void }) {
  const { data, isPending, error, isUntrusted } = useMetricDetail(metricId ?? '');

  return (
    <DrawerPanel open={open} onClose={onClose} title="Metric detail" description={metricId ?? undefined} width="lg">
      {!metricId ? <p className="text-sm text-muted-foreground">Select a metric to inspect its evidence and limitations.</p> : null}
      {metricId && isPending ? <LoadingState title="Loading metric detail" /> : null}
      {metricId && !isPending && isUntrusted && error instanceof Error ? <DataSourceGuardPanel reason={error.message} /> : null}
      {metricId && !isPending && !isUntrusted && error ? <ErrorState error={error} /> : null}
      {data ? (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold">{data.metric.label}</h3>
            <p className="text-sm text-muted-foreground">{data.metric.description}</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-dashed px-3 py-2">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Formula</p>
              <p className="text-sm">{data.metric.formula}</p>
            </div>
            <div className="rounded-md border border-dashed px-3 py-2">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Permission</p>
              <p className="text-sm">{data.metric.permission_required}</p>
            </div>
          </div>
          <EvidenceLinkList evidenceLinks={data.metric.evidence_links} />
          <MetricLimitationsPanel limitations={[...data.limitations, ...data.metric.limitations]} />
        </div>
      ) : null}
    </DrawerPanel>
  );
}

export function MetricRegistryTable({ registry }: { registry: MetricRegistryResponse }) {
  const [selectedMetricId, setSelectedMetricId] = useState<string | null>(null);
  const metrics = flattenMetrics(registry);

  return (
    <div className="space-y-4" data-testid="metric-registry-table-wrapper">
      <div className="rounded-lg border bg-background p-4 shadow-sm">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Metric registry</h2>
            <p className="text-sm text-muted-foreground">{registry.total_metrics} backend metrics are listed with formulas, permissions, and evidence.</p>
          </div>
        </div>
        <div className="overflow-x-auto rounded-lg border" data-testid="metric-registry-table">
          <table className="min-w-full divide-y">
            <thead className="bg-muted/30">
              <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-3">Metric</th>
                <th className="px-4 py-3">Group</th>
                <th className="px-4 py-3">Source module</th>
                <th className="px-4 py-3">Permission</th>
                <th className="px-4 py-3">Runtime</th>
                <th className="px-4 py-3">Readiness</th>
                <th className="px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {metrics.map((metric: ExecutiveControlTowerMetric) => (
                <tr key={metric.metric_id} data-testid={`registry-row-${metric.metric_id}`}>
                  <td className="px-4 py-3 text-sm font-medium">{metric.label}</td>
                  <td className="px-4 py-3 text-sm">{metric.metric_group}</td>
                  <td className="px-4 py-3 text-sm">{metric.source_module}</td>
                  <td className="px-4 py-3 text-sm">{metric.permission_required}</td>
                  <td className="px-4 py-3 text-sm">{metric.runtime_status}</td>
                  <td className="px-4 py-3 text-sm">{metric.readiness}</td>
                  <td className="px-4 py-3 text-sm">
                    <button
                      className="text-primary underline-offset-4 hover:underline"
                      onClick={() => setSelectedMetricId(metric.metric_id)}
                      type="button"
                    >
                      Open detail
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <MetricDetailDrawer metricId={selectedMetricId} open={Boolean(selectedMetricId)} onClose={() => setSelectedMetricId(null)} />
    </div>
  );
}