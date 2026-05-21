'use client';

import { EvidenceLinkList, MetricLimitationsPanel } from './EvidenceLinkList';
import { FoundationOnlyBadge } from './FoundationOnlyBadge';
import { FutureContractBadge } from './FutureContractBadge';
import { IncompleteDataNotice } from './IncompleteDataNotice';
import { StaleMetricBadge } from './StaleMetricBadge';
import { getMetricDisplayState } from '../guards';
import type { ExecutiveControlTowerMetric } from '../types';

export function MetricCard({ metric }: { metric: ExecutiveControlTowerMetric }) {
  const state = getMetricDisplayState(metric);

  return (
    <article
      className="rounded-lg border bg-background p-4 shadow-sm"
      data-testid={`metric-card-${metric.metric_id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{metric.label}</h3>
          <p className="mt-1 text-xs text-muted-foreground">{metric.description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {state.futureContract ? <FutureContractBadge /> : null}
          {state.foundationOnly ? <FoundationOnlyBadge /> : null}
          {state.stale ? <StaleMetricBadge /> : null}
        </div>
      </div>
      <div className="mt-4">
        <p className="text-2xl font-semibold" data-testid={`metric-value-${metric.metric_id}`}>
          {state.label}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">{metric.formula}</p>
      </div>
      {state.incomplete ? <div className="mt-3"><IncompleteDataNotice message="Incomplete data" /></div> : null}
      <div className="mt-4 space-y-3">
        <div className="text-xs text-muted-foreground">
          <p>Permission: {metric.permission_required}</p>
          <p>Source module: {metric.source_module}</p>
        </div>
        <EvidenceLinkList evidenceLinks={metric.evidence_links} />
        <MetricLimitationsPanel limitations={metric.limitations} />
      </div>
    </article>
  );
}