import { useQuery } from '@tanstack/react-query';
import { executiveControlTowerApi } from './api';
import {
  DataQualityError,
  assertTrustedControlTowerResponse,
  assertTrustedMetric,
  shouldBlockResponse,
} from './guards';

const CACHE_KEYS = {
  SUMMARY: ['executive-control-tower:summary'] as const,
  ASSIGNMENTS: ['executive-control-tower:assignments'] as const,
  DOCUMENTS: ['executive-control-tower:documents'] as const,
  DECREES: ['executive-control-tower:decrees'] as const,
  CORRESPONDENCE: ['executive-control-tower:correspondence'] as const,
  SLA_RISK: ['executive-control-tower:sla-risk'] as const,
  STRATEGY: ['executive-control-tower:strategy'] as const,
  AUDIT: ['executive-control-tower:audit'] as const,
  DEPARTMENTS: ['executive-control-tower:departments'] as const,
  REGISTRY: ['executive-control-tower:metric-registry'] as const,
  DETAIL: (metricId: string) => ['executive-control-tower:metric-detail', metricId] as const,
  HEALTH: ['executive-control-tower:health'] as const,
};

function withTrust<T extends { fake_metrics: boolean; data_source: string; incomplete_data: boolean; generated_at: string; limitations: string[] }>(
  payload: T,
) {
  assertTrustedControlTowerResponse(payload);
  return payload;
}

function buildTrustedQueryResult<T>(query: {
  data: T | undefined;
  error: unknown;
  isPending: boolean;
  isLoading: boolean;
}) {
  return {
    ...query,
    isTrusted: Boolean(query.data),
    isUntrusted: query.error instanceof DataQualityError,
  };
}

export function useExecutiveControlTowerSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.SUMMARY,
    queryFn: async () => withTrust(await executiveControlTowerApi.getExecutiveControlTowerSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useAssignmentExecutionSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.ASSIGNMENTS,
    queryFn: async () => withTrust(await executiveControlTowerApi.getAssignmentExecutionSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useDocumentWorkflowSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.DOCUMENTS,
    queryFn: async () => withTrust(await executiveControlTowerApi.getDocumentWorkflowSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useDecreeWorkflowSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.DECREES,
    queryFn: async () => withTrust(await executiveControlTowerApi.getDecreeWorkflowSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useCorrespondenceWorkflowSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.CORRESPONDENCE,
    queryFn: async () => withTrust(await executiveControlTowerApi.getCorrespondenceWorkflowSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useSlaRiskBottleneckSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.SLA_RISK,
    queryFn: async () => withTrust(await executiveControlTowerApi.getSlaRiskBottleneckSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useStrategyKpiSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.STRATEGY,
    queryFn: async () => withTrust(await executiveControlTowerApi.getStrategyKpiSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useAuditComplianceSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.AUDIT,
    queryFn: async () => withTrust(await executiveControlTowerApi.getAuditComplianceSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useDepartmentPerformanceSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.DEPARTMENTS,
    queryFn: async () => withTrust(await executiveControlTowerApi.getDepartmentPerformanceSummary()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useMetricRegistry() {
  const query = useQuery({
    queryKey: CACHE_KEYS.REGISTRY,
    queryFn: async () => {
      const payload = await executiveControlTowerApi.getMetricRegistry();
      return withTrust(payload);
    },
    staleTime: 60000,
  });

  return {
    ...buildTrustedQueryResult(query),
    isBlocked: Boolean(query.data && shouldBlockResponse(query.data)),
  };
}

export function useMetricDetail(metricId: string) {
  const query = useQuery({
    queryKey: CACHE_KEYS.DETAIL(metricId),
    queryFn: async () => {
      const payload = await executiveControlTowerApi.getMetricDetail(metricId);
      withTrust(payload);
      assertTrustedMetric(payload.metric);
      return payload;
    },
    enabled: Boolean(metricId),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useExecutiveControlTowerHealth() {
  const query = useQuery({
    queryKey: CACHE_KEYS.HEALTH,
    queryFn: async () => withTrust(await executiveControlTowerApi.getExecutiveControlTowerHealth()),
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}