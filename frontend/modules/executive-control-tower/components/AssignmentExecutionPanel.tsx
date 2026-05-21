'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type { AssignmentExecutionSummaryResponse } from '../types';

export function AssignmentExecutionPanel({ summary }: { summary: AssignmentExecutionSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Operational visibility only. No executor punishment or ranking."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}