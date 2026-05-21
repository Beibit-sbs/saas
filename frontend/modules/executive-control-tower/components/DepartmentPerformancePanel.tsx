'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type { DepartmentPerformanceSummaryResponse } from '../types';

export function DepartmentPerformancePanel({ summary }: { summary: DepartmentPerformanceSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Operational visibility only. No employee ranking and no punitive score."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}