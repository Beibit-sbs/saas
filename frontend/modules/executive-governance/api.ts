import { apiGet } from '@/shared/api/client';
import type {
  ExecutiveGovernanceDashboardSummary,
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
};
