import { apiGet } from '@/shared/api/client';
import type {
  CitationAnalyticsSummary,
  PublicationImpactProfile,
  ResearchRiskProfile,
  ResearchRiskSignal,
  ResearchRiskSummary,
  ResearchRiskTrend,
  ResearcherRankingResponse,
  ResearcherScientometricProfile,
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
  ScientometricTrend,
  ScientometricsSummaryResponse,
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
  getScientometricsDashboard: () => apiGet<ScientometricsSummaryResponse>(`${BASE}/scientometrics/dashboard`),
  getScientometricRanking: () => apiGet<ResearcherRankingResponse>(`${BASE}/scientometrics/ranking`),
  getResearcherScientometrics: (researcherId: string) =>
    apiGet<ResearcherScientometricProfile>(`${BASE}/scientometrics/${encodeURIComponent(researcherId)}`),
  getResearcherCitationAnalytics: (researcherId: string) =>
    apiGet<CitationAnalyticsSummary>(`${BASE}/scientometrics/${encodeURIComponent(researcherId)}/citations`),
  getResearcherImpactAnalytics: (researcherId: string) =>
    apiGet<PublicationImpactProfile>(`${BASE}/scientometrics/${encodeURIComponent(researcherId)}/impact`),
  getResearcherPublicationImpact: (researcherId: string) =>
    apiGet<PublicationImpactProfile>(`${BASE}/scientometrics/${encodeURIComponent(researcherId)}/publication-impact`),
  getResearcherScientometricTrends: (researcherId: string) =>
    apiGet<ScientometricTrend[]>(`${BASE}/scientometrics/${encodeURIComponent(researcherId)}/trends`),
  getResearchRiskDashboard: () => apiGet<ResearchRiskProfile>(`${BASE}/risk/dashboard`),
  getResearchRiskProfile: () => apiGet<ResearchRiskProfile>(`${BASE}/risk/profile`),
  getResearchRiskSummary: () => apiGet<ResearchRiskSummary>(`${BASE}/risk/summary`),
  getResearchRiskSignals: () => apiGet<ResearchRiskSignal[]>(`${BASE}/risk/signals`),
  getResearchRiskTrends: () => apiGet<ResearchRiskTrend[]>(`${BASE}/risk/trends`),
  getResearchRiskRecommendations: () => apiGet<string[]>(`${BASE}/risk/recommendations`),
};
