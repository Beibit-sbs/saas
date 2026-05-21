'use client';

import { Badge } from '@/shared/ui/badge';
import { MetricLimitationsPanel } from './EvidenceLinkList';
import type { ExecutiveControlTowerHealthResponse } from '../types';

export function ControlTowerHealthPanel({ health }: { health: ExecutiveControlTowerHealthResponse }) {
  return (
    <section className="rounded-lg border bg-background p-4 shadow-sm" data-testid="control-tower-health-panel">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold">Control tower health</h2>
        <Badge variant={health.registry_valid ? 'success' : 'destructive'}>
          {health.registry_valid ? 'Registry valid' : 'Registry issues detected'}
        </Badge>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-md border border-dashed px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Groups</p>
          <p className="text-lg font-semibold">{health.total_groups}</p>
        </div>
        <div className="rounded-md border border-dashed px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Metrics</p>
          <p className="text-lg font-semibold">{health.total_metrics}</p>
        </div>
      </div>
      {health.validation_errors.length > 0 ? (
        <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          {health.validation_errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      ) : null}
      <div className="mt-4">
        <MetricLimitationsPanel limitations={health.limitations} />
      </div>
    </section>
  );
}