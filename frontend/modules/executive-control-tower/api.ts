import { apiGet } from '@/shared/api/client';
import type {
  AssignmentExecutionSummaryResponse,
  AuditComplianceSummaryResponse,
  CorrespondenceWorkflowSummaryResponse,
  DecreeWorkflowSummaryResponse,
  DepartmentPerformanceSummaryResponse,
  DocumentWorkflowSummaryResponse,
  ExecutiveControlTowerHealthResponse,
  ExecutiveControlTowerSummaryResponse,
  MetricDetailResponse,
  MetricRegistryResponse,
  SlaRiskBottleneckSummaryResponse,
  StrategyKpiSummaryResponse,
} from './types';

const BASE = '/api/admin/executive-control-tower';

export const executiveControlTowerApi = {
  getExecutiveControlTowerSummary: () =>
    apiGet<ExecutiveControlTowerSummaryResponse>(`${BASE}/summary`),
  getAssignmentExecutionSummary: () =>
    apiGet<AssignmentExecutionSummaryResponse>(`${BASE}/assignments`),
  getDocumentWorkflowSummary: () =>
    apiGet<DocumentWorkflowSummaryResponse>(`${BASE}/documents`),
  getDecreeWorkflowSummary: () =>
    apiGet<DecreeWorkflowSummaryResponse>(`${BASE}/decrees`),
  getCorrespondenceWorkflowSummary: () =>
    apiGet<CorrespondenceWorkflowSummaryResponse>(`${BASE}/correspondence`),
  getSlaRiskBottleneckSummary: () =>
    apiGet<SlaRiskBottleneckSummaryResponse>(`${BASE}/sla-risk`),
  getStrategyKpiSummary: () =>
    apiGet<StrategyKpiSummaryResponse>(`${BASE}/strategy-kpis`),
  getAuditComplianceSummary: () =>
    apiGet<AuditComplianceSummaryResponse>(`${BASE}/audit-compliance`),
  getDepartmentPerformanceSummary: () =>
    apiGet<DepartmentPerformanceSummaryResponse>(`${BASE}/department-performance`),
  getMetricRegistry: () => apiGet<MetricRegistryResponse>(`${BASE}/metric-registry`),
  getMetricDetail: (metricId: string) => apiGet<MetricDetailResponse>(`${BASE}/metrics/${metricId}`),
  getExecutiveControlTowerHealth: () => apiGet<ExecutiveControlTowerHealthResponse>(`${BASE}/health`),
};