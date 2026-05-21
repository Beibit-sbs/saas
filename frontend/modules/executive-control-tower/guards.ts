import {
  MetricReadiness,
  MetricRuntimeStatus,
  type ExecutiveControlTowerMetric,
  type ExecutiveControlTowerResponseBase,
  type MetricDisplayState,
} from './types';

export const EXPECTED_DATA_SOURCE = 'computed_from_governance_workflows';

export class DataQualityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DataQualityError';
  }
}

export function shouldBlockResponse(response: ExecutiveControlTowerResponseBase) {
  return response.fake_metrics !== false || response.data_source !== EXPECTED_DATA_SOURCE;
}

export function isTrustedControlTowerResponse(response: ExecutiveControlTowerResponseBase) {
  return !shouldBlockResponse(response);
}

export function assertTrustedControlTowerResponse(response: ExecutiveControlTowerResponseBase) {
  if (response.fake_metrics !== false) {
    throw new DataQualityError('Dashboard data could not be verified: fake_metrics=true');
  }

  if (response.data_source !== EXPECTED_DATA_SOURCE) {
    throw new DataQualityError(
      `Dashboard data source mismatch: expected ${EXPECTED_DATA_SOURCE}, received ${response.data_source}`,
    );
  }
}

export function shouldBlockMetric(metric: ExecutiveControlTowerMetric) {
  return metric.fake_metrics !== false || metric.data_source !== EXPECTED_DATA_SOURCE;
}

export function assertTrustedMetric(metric: ExecutiveControlTowerMetric) {
  if (metric.fake_metrics !== false) {
    throw new DataQualityError(`Metric ${metric.metric_id} could not be verified: fake_metrics=true`);
  }

  if (metric.data_source !== EXPECTED_DATA_SOURCE) {
    throw new DataQualityError(
      `Metric ${metric.metric_id} data source mismatch: expected ${EXPECTED_DATA_SOURCE}, received ${metric.data_source}`,
    );
  }
}

export function isMetricUnavailable(metric: ExecutiveControlTowerMetric) {
  return metric.value === null || metric.value === undefined || metric.runtime_status === MetricRuntimeStatus.UNAVAILABLE;
}

export function isMetricStale(metric: ExecutiveControlTowerMetric) {
  if (!metric.freshness_timestamp || !metric.staleness_threshold_minutes) {
    return false;
  }

  const freshness = Date.parse(metric.freshness_timestamp);
  if (Number.isNaN(freshness)) {
    return false;
  }

  return Date.now() - freshness > metric.staleness_threshold_minutes * 60_000;
}

export function formatMetricValue(metric: ExecutiveControlTowerMetric) {
  if (metric.value === null || metric.value === undefined) {
    return 'Unavailable';
  }

  if (typeof metric.value === 'number' && metric.unit === '%') {
    return `${metric.value}%`;
  }

  if (typeof metric.value === 'number' && metric.unit) {
    return `${metric.value} ${metric.unit}`;
  }

  return String(metric.value);
}

export function getMetricDisplayState(metric: ExecutiveControlTowerMetric): MetricDisplayState {
  const blocked = shouldBlockMetric(metric);
  const unavailable = isMetricUnavailable(metric);
  const stale = isMetricStale(metric);
  const futureContract = metric.readiness === MetricReadiness.FUTURE_CONTRACT;
  const foundationOnly = metric.runtime_status === MetricRuntimeStatus.FOUNDATION_CONTRACT_ONLY;
  const incomplete = metric.incomplete_data;

  let label = formatMetricValue(metric);
  if (blocked) label = 'Unavailable';
  if (futureContract) label = 'Future contract';
  else if (foundationOnly && unavailable) label = 'Foundation-only metric';
  else if (unavailable) label = 'Unavailable';

  return {
    blocked,
    unavailable,
    stale,
    futureContract,
    foundationOnly,
    incomplete,
    label,
  };
}