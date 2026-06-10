import { apiGet } from '@/shared/api/client';
import type {
  ExecutiveAssignmentEntry,
  ExecutiveAssignmentSummary,
  ExecutiveDecisionExecutionSummary,
  ExecutiveDecisionRegistryEntry,
  ExecutiveDecisionRegistrySummary,
  ExecutiveExecutionMetrics,
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
  getAssignments: () => apiGet<ExecutiveAssignmentEntry[]>(`${BASE}/assignments`),
  getAssignmentSummary: () => apiGet<ExecutiveAssignmentSummary>(`${BASE}/assignments/summary`),
  getAssignmentExecution: () => apiGet<ExecutiveExecutionMetrics>(`${BASE}/assignments/execution`),
  getAssignmentRisks: () => apiGet<ExecutiveExecutionMetrics>(`${BASE}/assignments/risks`),
  getMeetings: () => apiGet<ExecutiveMeetingEntry[]>(`${BASE}/meetings`),
  getMeetingSummary: () => apiGet<ExecutiveMeetingSummary>(`${BASE}/meetings/summary`),
  getProtocols: () => apiGet<ExecutiveProtocolEntry[]>(`${BASE}/protocols`),
  getProtocolSummary: () => apiGet<ExecutiveProtocolSummary>(`${BASE}/protocols/summary`),
  getProtocolExecution: () => apiGet<ExecutiveProtocolExecutionSummary>(`${BASE}/protocols/execution`),
};
