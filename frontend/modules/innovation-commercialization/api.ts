import { apiGet } from '@/shared/api/client';
import type {
  InnovationCommercializationShell,
  InnovationOpportunityList,
} from './types';

const BASE = '/api/admin/innovation-commercialization';

export const innovationCommercializationApi = {
  getShell: () => apiGet<InnovationCommercializationShell>(`${BASE}/shell`),
  listOpportunities: () => apiGet<InnovationOpportunityList>(`${BASE}/opportunities`),
};
