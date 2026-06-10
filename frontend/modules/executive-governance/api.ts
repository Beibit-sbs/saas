import { apiGet } from '@/shared/api/client';
import type {
  ExecutiveDecisionExecutionSummary,
  ExecutiveDecisionRegistryEntry,
  ExecutiveDecisionRegistrySummary,
  ExecutiveGovernanceDashboardSummary,
  ExecutiveMeetingEntry,
  ExecutiveMeetingSummary,
  ExecutiveProtocolEntry,
  ExecutiveProtocolExecutionSummary,
  ExecutiveProtocolSummary,
  ExecutiveGovernanceRuntimeOverview,
  ExecutiveGovernanceRuntimeSummary,
  ExecutiveGovernanceSignalSummary,
} from './types';

const BASE = '/api/admin/executive-governance/runtime';

export const executiveGovernanceApi = {
  getOverview: () => apiGet<ExecutiveGovernanceRuntimeOverview>(`${BASE}/overview`),
  getSummary: () => apiGet<ExecutiveGovernanceRuntimeSummary>(`${BASE}/summary`),
  getSignals: () => apiGet<ExecutiveGovernanceSignalSummary[]>(`${BASE}/signals`),
  getDashboard: () => apiGet<ExecutiveGovernanceDashboardSummary>(`${BASE}/dashboard`),
  getDecisions: () => apiGet<ExecutiveDecisionRegistryEntry[]>(`${BASE}/decisions`),
  getDecisionSummary: () => apiGet<ExecutiveDecisionRegistrySummary>(`${BASE}/decisions/summary`),
  getDecisionExecution: () => apiGet<ExecutiveDecisionExecutionSummary>(`${BASE}/decisions/execution`),
  getMeetings: () => apiGet<ExecutiveMeetingEntry[]>(`${BASE}/meetings`),
  getMeetingSummary: () => apiGet<ExecutiveMeetingSummary>(`${BASE}/meetings/summary`),
  getProtocols: () => apiGet<ExecutiveProtocolEntry[]>(`${BASE}/protocols`),
  getProtocolSummary: () => apiGet<ExecutiveProtocolSummary>(`${BASE}/protocols/summary`),
  getProtocolExecution: () => apiGet<ExecutiveProtocolExecutionSummary>(`${BASE}/protocols/execution`),
};
