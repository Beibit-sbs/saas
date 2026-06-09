import { apiGet } from '@/shared/api/client';
import type {
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
};
