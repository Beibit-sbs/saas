import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';

export type CohortLifecycleStatus = 'draft' | 'finalized' | 'analyzed';

/**
 * Cohort read schema response from the backend
 */
export interface CohortReadSchema {
  id: number;
  tenant_id: number;
  playbook_id: number;
  cohort_name: string;
  analysis_window_start: string; // ISO date
  analysis_window_end: string; // ISO date
  student_count: number;
  data_completeness_pct: number | null;
  created_by: string;
  created_at: string; // ISO datetime
  status: CohortLifecycleStatus;
}

/**
 * Finalize cohort request payload
 */
export interface CohortFinalizeRequest {
  playbook_id: number;
  cohort_name: string;
  analysis_window_start: string; // ISO date
  analysis_window_end: string; // ISO date
}

/**
 * Query key factory for React Query
 */
const cohortQueryKeys = {
  all: ['cohorts'] as const,
  lists: () => [...cohortQueryKeys.all, 'list'] as const,
  list: (tenantId?: number, filters?: Record<string, unknown>) => [...cohortQueryKeys.lists(), { tenantId, filters }] as const,
  details: () => [...cohortQueryKeys.all, 'detail'] as const,
  detail: (id: number, tenantId?: number) => [...cohortQueryKeys.details(), tenantId, id] as const,
  byPlaybook: (playbookId: number, tenantId?: number) => [...cohortQueryKeys.all, 'playbook', tenantId, playbookId] as const,
};

/**
 * Fetch all intervention cohorts for the current tenant
 *
 * @param tenantId - Tenant ID from context
 * @param options - React Query options
 * @returns Query hook result with cohorts data
 *
 * @example
 * const { data, isLoading, error } = useCohortsQuery(123);
 */
export const useCohortsQuery = (
  tenantId?: number,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) => {
  return useQuery({
    queryKey: cohortQueryKeys.list(tenantId),
    queryFn: async () => {
      const response = await apiClient.get<CohortReadSchema[]>(
        '/api/admin/interventions/cohorts',
        {
          headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
        }
      );
      return response;
    },
    enabled: options?.enabled !== false && tenantId !== undefined,
    staleTime: options?.staleTime ?? 10 * 60 * 1000, // 10 minutes default
  });
};

/**
 * Finalize a new cohort
 *
 * @returns Mutation hook for creating/finalizing a cohort
 *
 * @example
 * const mutation = useFinalizeCohortMutation();
 * mutation.mutate({
 *   playbook_id: 1,
 *   cohort_name: 'Spring 2026',
 *   analysis_window_start: '2026-01-15',
 *   analysis_window_end: '2026-05-15',
 * });
 */
export const useFinalizeCohortMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CohortFinalizeRequest) => {
      const response = await apiClient.post<CohortReadSchema>(
        '/api/admin/interventions/cohorts/finalize',
        payload
      );
      return response;
    },
    onSuccess: (data) => {
      // Invalidate and refetch cohorts list
      queryClient.invalidateQueries({ queryKey: cohortQueryKeys.lists() });
      // Cache the newly created cohort
      queryClient.setQueryData(cohortQueryKeys.detail(data.id, data.tenant_id), data);
    },
  });
};

export const useFinalizeExistingCohortMutation = (cohortId: number, tenantId?: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<CohortReadSchema>(
        `/api/admin/interventions/cohorts/${cohortId}/finalize`,
        {},
        {
          headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
        }
      );
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: cohortQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: cohortQueryKeys.detail(cohortId, tenantId) });
      queryClient.setQueryData(cohortQueryKeys.detail(data.id, data.tenant_id), data);
    },
  });
};

/**
 * Get the latest cohort for a specific playbook
 *
 * @param playbookId - Playbook ID
 * @param tenantId - Tenant ID from context
 * @param options - React Query options
 * @returns Query hook result with cohort data
 *
 * @example
 * const { data, isLoading } = useLatestCohortByPlaybook(5, 123);
 */
export const useLatestCohortByPlaybook = (
  playbookId: number,
  tenantId?: number,
  options?: {
    enabled?: boolean;
  }
) => {
  return useQuery({
    queryKey: cohortQueryKeys.byPlaybook(playbookId, tenantId),
    queryFn: async () => {
      const response = await apiClient.get<CohortReadSchema>(
        `/api/admin/interventions/cohorts/latest/by-playbook/${playbookId}`,
        {
          headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
        }
      );
      return response;
    },
    enabled: options?.enabled !== false && playbookId > 0 && tenantId !== undefined,
  });
};

/**
 * Get a single cohort by ID
 *
 * @param cohortId - Cohort ID
 * @param tenantId - Tenant ID from context
 * @param options - React Query options
 * @returns Query hook result with cohort data
 *
 * @example
 * const { data, isLoading } = useCohortDetail(42, 123);
 */
export const useCohortDetail = (
  cohortId?: number,
  tenantId?: number,
  options?: {
    enabled?: boolean;
  }
) => {
  return useQuery({
    queryKey: cohortQueryKeys.detail(cohortId ?? 0, tenantId),
    queryFn: async () => {
      const response = await apiClient.get<CohortReadSchema>(
        `/api/admin/interventions/cohorts/${cohortId}`,
        {
          headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
        }
      );
      return response;
    },
    enabled: options?.enabled !== false && cohortId !== undefined && tenantId !== undefined,
  });
};
