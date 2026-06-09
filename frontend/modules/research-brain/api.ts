import { apiGet } from '@/shared/api/client';
import type {
  Researcher,
  ResearcherActivityProfileResponse,
  ResearcherDashboardSummaryResponse,
  ResearcherListResponse,
  ResearcherRiskProfileResponse,
  ResearchBrainContextResponse,
  ResearchBrainKpiSurfaceResponse,
  ResearchBrainOrchestrationResponse,
  ResearchBrainRbacValidationResponse,
  ResearchBrainShellResponse,
  ResearchBrainSignalSurfaceResponse,
} from './types';

const BASE = '/api/admin/research-brain';

export const researchBrainApi = {
  getShell: () => apiGet<ResearchBrainShellResponse>(`${BASE}/shell`),
  getOrchestration: () => apiGet<ResearchBrainOrchestrationResponse>(`${BASE}/orchestration`),
  getContext: () => apiGet<ResearchBrainContextResponse>(`${BASE}/context`),
  getKpis: () => apiGet<ResearchBrainKpiSurfaceResponse>(`${BASE}/kpis`),
  getSignals: () => apiGet<ResearchBrainSignalSurfaceResponse>(`${BASE}/signals`),
  getRbacValidation: () => apiGet<ResearchBrainRbacValidationResponse>(`${BASE}/rbac-validation`),
  listResearchers: () => apiGet<ResearcherListResponse>(`${BASE}/researchers`),
  getResearcherSummary: () => apiGet<ResearcherDashboardSummaryResponse>(`${BASE}/researchers/summary`),
  getResearcher: (researcherId: string) => apiGet<Researcher>(`${BASE}/researchers/${encodeURIComponent(researcherId)}`),
  getResearcherActivity: (researcherId: string) =>
    apiGet<ResearcherActivityProfileResponse>(`${BASE}/researchers/${encodeURIComponent(researcherId)}/activity`),
  getResearcherRisk: (researcherId: string) =>
    apiGet<ResearcherRiskProfileResponse>(`${BASE}/researchers/${encodeURIComponent(researcherId)}/risk`),
};
