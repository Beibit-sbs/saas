'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type { SlaRiskBottleneckSummaryResponse } from '../types';

export function SlaRiskBottleneckPanel({ summary }: { summary: SlaRiskBottleneckSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Operational indicators only. No auto-escalation button and no hidden score."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}