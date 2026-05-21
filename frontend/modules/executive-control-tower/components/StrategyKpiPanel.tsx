'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type { StrategyKpiSummaryResponse } from '../types';

export function StrategyKpiPanel({ summary }: { summary: StrategyKpiSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Future-contract strategy metrics remain deferred until a real strategy source exists."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}