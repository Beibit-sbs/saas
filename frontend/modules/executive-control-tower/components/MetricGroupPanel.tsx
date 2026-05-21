'use client';

import { IncompleteDataNotice } from './IncompleteDataNotice';
import { MetricCard } from './MetricCard';
import { MetricLimitationsPanel } from './EvidenceLinkList';
import type { ExecutiveControlTowerMetric } from '../types';

export function MetricGrid({ metrics }: { metrics: ExecutiveControlTowerMetric[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="metric-grid">
      {metrics.map((metric) => (
        <MetricCard key={metric.metric_id} metric={metric} />
      ))}
    </div>
  );
}

export function MetricGroupPanel({
  title,
  description,
  metrics,
  incompleteData,
  limitations,
}: {
  title: string;
  description?: string;
  metrics: ExecutiveControlTowerMetric[];
  incompleteData?: boolean;
  limitations?: string[];
}) {
  return (
    <section className="space-y-4 rounded-lg border bg-background p-4 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {incompleteData ? <IncompleteDataNotice message="Incomplete data" /> : null}
      <MetricGrid metrics={metrics} />
      {limitations && limitations.length > 0 ? <MetricLimitationsPanel limitations={limitations} /> : null}
    </section>
  );
}