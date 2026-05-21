import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MetricCard } from '@/modules/executive-control-tower/components';
import { MetricReadiness, MetricRuntimeStatus, type ExecutiveControlTowerMetric } from '@/modules/executive-control-tower/types';

function makeMetric(overrides: Partial<ExecutiveControlTowerMetric> = {}): ExecutiveControlTowerMetric {
  return {
    metric_id: 'metric-1',
    metric_group: 'EXECUTIVE_OVERVIEW',
    label: 'On-time assignments',
    description: 'Assignments on time',
    value: null,
    unit: null,
    source_module: 'rector_assignment_workflow',
    source_entities: ['RectorAssignment'],
    source_tables: ['rector_assignments'],
    source_fields: ['status'],
    calculation_method: 'read_only_registry_contract',
    formula: 'count(on_time)',
    tenant_scope: 'tenant_id_required',
    permission_required: 'admin.executive_control_tower.assignments.read',
    freshness_timestamp: null,
    staleness_threshold_minutes: 60,
    evidence_links: [
      {
        label: 'Source contract',
        source_module: 'rector_assignment_workflow',
        source_entity: 'RectorAssignment',
        source_table: 'rector_assignments',
        reference_field: 'id',
        reference_value: null,
        url: null,
        available: false,
        limitations: ['Live evidence links are deferred in the foundation release.'],
      },
    ],
    data_source: 'computed_from_governance_workflows',
    fake_metrics: false,
    incomplete_data: true,
    limitations: ['Read-only backend foundation only'],
    failure_mode: 'INCOMPLETE_DATA',
    runtime_status: MetricRuntimeStatus.FOUNDATION_CONTRACT_ONLY,
    readiness: MetricReadiness.CONTRACT_DEFINED,
    ...overrides,
  };
}

describe('MetricCard', () => {
  it('renders unavailable for null metrics and shows incomplete data', () => {
    render(<MetricCard metric={makeMetric()} />);
    expect(screen.getByTestId('metric-value-metric-1').textContent).toMatch(/foundation-only metric/i);
    expect(screen.getByTestId('incomplete-data-notice').textContent).toMatch(/incomplete data/i);
  });

  it('renders zero as a real backend value', () => {
    render(<MetricCard metric={makeMetric({ value: 0, incomplete_data: false })} />);
    expect(screen.getByTestId('metric-value-metric-1').textContent).toBe('0');
  });

  it('renders future-contract and stale badges when required', () => {
    render(
      <MetricCard
        metric={makeMetric({
          value: null,
          readiness: MetricReadiness.FUTURE_CONTRACT,
          runtime_status: MetricRuntimeStatus.DEFERRED_UNTIL_STRATEGY_MODULE,
          freshness_timestamp: '2026-05-20T00:00:00Z',
          staleness_threshold_minutes: 1,
        })}
      />,
    );
    expect(screen.getAllByText(/future contract/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/stale data/i)).toBeTruthy();
  });

  it('renders evidence links and limitations', () => {
    render(<MetricCard metric={makeMetric({ incomplete_data: false })} />);
    expect(screen.getByTestId('evidence-link-list').textContent).toMatch(/source contract/i);
    expect(screen.getByTestId('metric-limitations-panel').textContent).toMatch(/read-only backend foundation only/i);
  });

  it('does not fabricate trend or hidden score copy', () => {
    render(<MetricCard metric={makeMetric({ value: 12, incomplete_data: false })} />);
    const text = screen.getByTestId('metric-card-metric-1').textContent ?? '';
    expect(text.toLowerCase()).not.toContain('trend');
    expect(text.toLowerCase()).not.toContain('hidden score');
  });
});