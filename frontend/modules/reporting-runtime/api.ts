import { apiGet } from '@/shared/api/client';
import type { ReportingRuntimeShellResponse } from './types';

const BASE = '/api/admin/reporting-brain';

export const reportingRuntimeApi = {
  getRuntimeShell: () => apiGet<ReportingRuntimeShellResponse>(`${BASE}/runtime`),
};
