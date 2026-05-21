import { describe, expect, it } from 'vitest';
import {
  DataQualityError,
  assertTrustedControlTowerResponse,
  assertTrustedMetric,
  formatMetricValue,
  getMetricDisplayState,
  shouldBlockMetric,
  shouldBlockResponse,
} from '@/modules/executive-control-tower/guards';
import {
  MetricReadiness,
  MetricRuntimeStatus,
  type ExecutiveControlTowerMetric,
  type ExecutiveControlTowerSummaryResponse,
} from '@/modules/executive-control-tower/types';

const baseMetric: ExecutiveControlTowerMetric = {
  metric_id: 'metric-1',
  metric_group: 'EXECUTIVE_OVERVIEW',
  label: 'Assignments due',
  description: 'Open assignments due soon',
  value: null,
  unit: null,
  source_module: 'rector_assignment_workflow',
  source_entities: ['RectorAssignment'],
  source_tables: ['rector_assignments'],
  source_fields: ['due_at'],
  calculation_method: 'read_only_registry_contract',
  formula: 'count(*)',
  tenant_scope: 'tenant_id_required',
  permission_required: 'admin.executive_control_tower.assignments.read',
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

const baseResponse: ExecutiveControlTowerSummaryResponse = {
  groups: [],
  fake_metrics: false,
  data_source: 'computed_from_governance_workflows',
  incomplete_data: true,
  generated_at: '2026-05-21T00:00:00Z',
  limitations: ['Read-only backend foundation only'],
};

describe('executive control tower guards', () => {
  it('throws when fake_metrics is true', () => {
    expect(() => assertTrustedControlTowerResponse({ ...baseResponse, fake_metrics: true })).toThrow(DataQualityError);
    expect(shouldBlockResponse({ ...baseResponse, fake_metrics: true })).toBe(true);
  });

  it('throws when data_source is mismatched', () => {
    expect(() => assertTrustedControlTowerResponse({ ...baseResponse, data_source: 'hardcoded' })).toThrow(/data source mismatch/i);
    expect(shouldBlockResponse({ ...baseResponse, data_source: 'hardcoded' })).toBe(true);
  });

  it('blocks untrusted metrics', () => {
    expect(() => assertTrustedMetric({ ...baseMetric, fake_metrics: true })).toThrow(/fake_metrics=true/i);
    expect(() => assertTrustedMetric({ ...baseMetric, data_source: 'other_source' })).toThrow(/data source mismatch/i);
    expect(shouldBlockMetric({ ...baseMetric, fake_metrics: true })).toBe(true);
  });

  it('renders unavailable for null but preserves zero', () => {
    expect(formatMetricValue({ ...baseMetric, value: null })).toBe('Unavailable');
    expect(formatMetricValue({ ...baseMetric, value: 0 })).toBe('0');
  });

  it('marks future contract and foundation-only states explicitly', () => {
    expect(getMetricDisplayState(baseMetric).foundationOnly).toBe(true);
    expect(getMetricDisplayState(baseMetric).label).toBe('Foundation-only metric');

    const futureMetric = getMetricDisplayState({
      ...baseMetric,
      readiness: MetricReadiness.FUTURE_CONTRACT,
      runtime_status: MetricRuntimeStatus.DEFERRED_UNTIL_STRATEGY_MODULE,
    });
    expect(futureMetric.futureContract).toBe(true);
    expect(futureMetric.label).toBe('Future contract');
  });

  it('marks stale metrics when freshness exceeds threshold', () => {
    const staleState = getMetricDisplayState({
      ...baseMetric,
      value: 3,
      incomplete_data: false,
      freshness_timestamp: '2026-05-20T00:00:00Z',
      staleness_threshold_minutes: 30,
    });
    expect(staleState.stale).toBe(true);
  });
});