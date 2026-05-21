'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type { AuditComplianceSummaryResponse } from '../types';

export function AuditCompliancePanel({ summary }: { summary: AuditComplianceSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Audit and compliance visibility only. No production-ready or L5/L6 claim is made here."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}