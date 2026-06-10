import { apiGet } from '@/shared/api/client';
import type {
  ReportingCycleResponse,
  ReportingEvidenceResponse,
  ReportingProviderResponse,
  ReportingRegistryResponse,
  ReportingRuntimeShellResponse,
  ReportingSubmissionResponse,
  ReportingTemplateResponse,
} from './types';

const BASE = '/api/admin/reporting-brain';

export const reportingRuntimeApi = {
  getRuntimeShell: () => apiGet<ReportingRuntimeShellResponse>(`${BASE}/runtime`),
  getRegistry: () => apiGet<ReportingRegistryResponse>(`${BASE}/runtime/registry`),
  getTemplates: () => apiGet<ReportingTemplateResponse>(`${BASE}/runtime/templates`),
  getCycles: () => apiGet<ReportingCycleResponse>(`${BASE}/runtime/cycles`),
  getSubmissions: () => apiGet<ReportingSubmissionResponse>(`${BASE}/runtime/submissions`),
  getEvidence: () => apiGet<ReportingEvidenceResponse>(`${BASE}/runtime/evidence`),
  getProviders: () => apiGet<ReportingProviderResponse>(`${BASE}/runtime/providers`),
};
