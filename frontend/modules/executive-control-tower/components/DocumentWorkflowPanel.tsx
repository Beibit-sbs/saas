'use client';

import { MetricGroupPanel } from './MetricGroupPanel';
import type {
  CorrespondenceWorkflowSummaryResponse,
  DecreeWorkflowSummaryResponse,
  DocumentWorkflowSummaryResponse,
} from '../types';

export function DocumentWorkflowPanel({ summary }: { summary: DocumentWorkflowSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Signed metadata only where applicable. No fake delivery status and no e-signature claim."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}

export function DecreeWorkflowPanel({ summary }: { summary: DecreeWorkflowSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Decree workflow visibility remains read-only and evidence-backed."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}

export function CorrespondenceWorkflowPanel({ summary }: { summary: CorrespondenceWorkflowSummaryResponse }) {
  return (
    <MetricGroupPanel
      title={summary.group_label}
      description="Signed metadata only where relevant. No fake delivery or dispatch claims."
      metrics={summary.metrics}
      incompleteData={summary.incomplete_data}
      limitations={summary.limitations}
    />
  );
}