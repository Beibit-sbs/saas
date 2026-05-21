import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MetricRegistryTable } from '@/modules/executive-control-tower/components';
import { MetricReadiness, MetricRuntimeStatus, type MetricRegistryResponse } from '@/modules/executive-control-tower/types';

vi.mock('@/modules/executive-control-tower/hooks', () => ({
  useMetricDetail: (metricId: string) => ({
    data: metricId
      ? {
          metric: {
            metric_id: metricId,
            label: `Detail ${metricId}`,
            description: 'Metric detail description',
            formula: 'count(*)',
            permission_required: 'admin.executive_control_tower.metric_registry.read',
            evidence_links: [],
            limitations: ['Detail limitation'],
          },
          fake_metrics: false,
          data_source: 'computed_from_governance_workflows',
          incomplete_data: true,
          generated_at: '2026-05-21T00:00:00Z',
          limitations: ['Read-only backend foundation only'],
        }
      : undefined,
    error: null,
    isPending: false,
    isLoading: false,
    isTrusted: Boolean(metricId),
    isUntrusted: false,
  }),
}));

function makeRegistry(): MetricRegistryResponse {
  return {
    groups: [
      {
        group_id: 'EXECUTIVE_OVERVIEW',
        label: 'Executive Overview',
        description: 'Overview metrics',
        fake_metrics: false,
        data_source: 'computed_from_governance_workflows',
        incomplete_data: true,
        limitations: ['Read-only backend foundation only'],
        metrics: Array.from({ length: 79 }, (_, index) => ({
          metric_id: `metric-${index + 1}`,
          metric_group: 'EXECUTIVE_OVERVIEW',
          label: `Metric ${index + 1}`,
          description: 'Description',
          value: null,
          unit: null,
          source_module: 'rector_assignment_workflow',
          source_entities: ['RectorAssignment'],
          source_tables: ['rector_assignments'],
          source_fields: ['status'],
          calculation_method: 'read_only_registry_contract',
          formula: 'count(*)',
          tenant_scope: 'tenant_id_required',
          permission_required: 'admin.executive_control_tower.metric_registry.read',
          freshness_timestamp: null,
          staleness_threshold_minutes: 60,
          evidence_links: [],
          data_source: 'computed_from_governance_workflows',
          fake_metrics: false,
          incomplete_data: true,
          limitations: ['Read-only backend foundation only'],
          failure_mode: 'INCOMPLETE_DATA',
          runtime_status: MetricRuntimeStatus.FOUNDATION_CONTRACT_ONLY,
          readiness: MetricReadiness.CONTRACT_DEFINED,
        })),
      },
    ],
    total_metrics: 79,
    fake_metrics: false,
    data_source: 'computed_from_governance_workflows',
    incomplete_data: true,
    generated_at: '2026-05-21T00:00:00Z',
    limitations: ['Read-only backend foundation only'],
  };
}

describe('MetricRegistryTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all 79 backend metrics', () => {
    render(<MetricRegistryTable registry={makeRegistry()} />);
    expect(screen.getAllByText(/open detail/i)).toHaveLength(79);
    expect(screen.getByTestId('metric-registry-table').textContent).toMatch(/Metric 79/);
  });

  it('opens a metric detail drawer', () => {
    render(<MetricRegistryTable registry={makeRegistry()} />);
    fireEvent.click(screen.getAllByText(/open detail/i)[0]);
    expect(screen.getByText(/detail metric-1/i)).toBeTruthy();
    expect(screen.getByText(/detail limitation/i)).toBeTruthy();
  });
});