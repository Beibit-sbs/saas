'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type { ExecutiveControlTowerSummaryResponse } from '../types';

export function ExecutiveOverviewPanel({ summary }: { summary: ExecutiveControlTowerSummaryResponse }) {
  return (
    <div className="space-y-6" data-testid="executive-overview-panel">
      {summary.incomplete_data ? (
        <p className="text-sm text-muted-foreground">Incomplete data remains visible while the backend foundation matures.</p>
      ) : null}
      {summary.groups.map((group) => (
        <MetricGroupPanel
          key={group.group_id}
          title={group.label}
          description={group.description}
          metrics={group.metrics}
          incompleteData={group.incomplete_data}
          limitations={group.limitations}
        />
      ))}
    </div>
  );
}