import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  AuditCompliancePanel,
  ControlTowerShell,
  DepartmentPerformancePanel,
  DocumentWorkflowPanel,
  ExecutiveOverviewPanel,
  StrategyKpiPanel,
} from '@/modules/executive-control-tower/components';
import { MetricReadiness, MetricRuntimeStatus, type ExecutiveControlTowerSummaryResponse, type SectionSummaryResponse } from '@/modules/executive-control-tower/types';

vi.mock('@/shared/auth/context', () => ({
  useAdminAuth: () => ({
    hasPermission: (permission: string) => permission !== 'admin.executive_control_tower.metric_registry.read',
  }),
}));

function makeMetric(id: string) {
  return {
    metric_id: id,
    metric_group: 'EXECUTIVE_OVERVIEW',
    label: `Metric ${id}`,
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
    permission_required: 'admin.executive_control_tower.read',
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
  };
}

function makeSectionSummary(label: string): SectionSummaryResponse {
  return {
    metric_group: 'EXECUTIVE_OVERVIEW',
    group_label: label,
    metrics: [makeMetric('1')],
    fake_metrics: false,
    data_source: 'computed_from_governance_workflows',
    incomplete_data: true,
    generated_at: '2026-05-21T00:00:00Z',
    limitations: ['Read-only backend foundation only'],
  };
}

const summary: ExecutiveControlTowerSummaryResponse = {
  groups: [
    {
      group_id: 'EXECUTIVE_OVERVIEW',
      label: 'Executive Overview',
      description: 'Overview metrics',
      metrics: [makeMetric('1')],
      fake_metrics: false,
      data_source: 'computed_from_governance_workflows',
      incomplete_data: true,
      limitations: ['Read-only backend foundation only'],
    },
  ],
  fake_metrics: false,
  data_source: 'computed_from_governance_workflows',
  incomplete_data: true,
  generated_at: '2026-05-21T00:00:00Z',
  limitations: ['Read-only backend foundation only'],
};

describe('Executive control tower panels', () => {
  it('renders the overview shell labels and hides unauthorized nav items', () => {
    render(
      <ControlTowerShell title="Executive Control Tower" activePath="/console/executive-control-tower">
        <ExecutiveOverviewPanel summary={summary} />
      </ControlTowerShell>,
    );
    expect(screen.getByTestId('computed-from-governance-workflows-label').textContent).toMatch(/computed from governance workflows/i);
    expect(screen.getByTestId('no-automated-decision-label').textContent).toMatch(/no automated decision/i);
    expect(screen.queryByText(/metric registry/i)).toBeNull();
  });

  it('documents panel includes signed metadata only messaging', () => {
    render(<DocumentWorkflowPanel summary={makeSectionSummary('Document Workflow')} />);
    expect(screen.getByText(/signed metadata only/i)).toBeTruthy();
  });

  it('strategy panel calls out future-contract metrics', () => {
    render(<StrategyKpiPanel summary={makeSectionSummary('Strategy KPI')} />);
    expect(screen.getByText(/future-contract strategy metrics remain deferred/i)).toBeTruthy();
  });

  it('audit panel avoids production-ready and l5/l6 claims', () => {
    render(<AuditCompliancePanel summary={makeSectionSummary('Audit / Compliance')} />);
    const text = screen.getByText(/no production-ready or l5\/l6 claim/i).textContent ?? '';
    expect(text).toMatch(/no production-ready or l5\/l6 claim/i);
  });

  it('department panel uses operational visibility wording instead of ranking', () => {
    render(<DepartmentPerformancePanel summary={makeSectionSummary('Department Performance')} />);
    const text = screen.getByText(/operational visibility only/i).textContent ?? '';
    expect(text.toLowerCase()).toContain('operational visibility');
    expect(text.toLowerCase()).toContain('no employee ranking');
    expect(text.toLowerCase()).toContain('no punitive score');
  });

  it('renders no auto-escalation or provider controls', () => {
    render(
      <ControlTowerShell title="Executive Control Tower" activePath="/console/executive-control-tower/sla-risk">
        <div>No action controls</div>
      </ControlTowerShell>,
    );
    const text = screen.getByText(/no action controls/i).closest('div')?.parentElement?.textContent?.toLowerCase() ?? '';
    expect(text).not.toContain('auto-escalation');
    expect(text).not.toContain('provider');
  });
});