import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';

/**
 * Request payload for analyzing a cohort
 */
export interface CohortAnalyzeRequest {
  segment_keys?: string[];
}

/**
 * Response from cohort analysis
 */
export interface CohortAnalyzeResponse {
  cohort_id: number;
  status: string;
  detail: string;
  requested_at: string; // ISO datetime
}

/**
 * Mutation hook for analyzing a cohort
 *
 * This mutation triggers the backend to perform statistical analysis
 * on the cohort data, computing treatment effects, confidence intervals,
 * and outcome metrics.
 *
 * @returns Mutation hook for cohort analysis
 *
 * @example
 * const mutation = useCohortAnalysisMutation();
 * mutation.mutate({
 *   cohort_id: 42,
 *   segment_keys: ['demographic_group_1', 'demographic_group_2']
 * });
 */
export const useCohortAnalysisMutation = (cohortId: number, tenantId?: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CohortAnalyzeRequest) => {
      const response = await apiClient.post<CohortAnalyzeResponse>(
        `/api/admin/interventions/cohorts/${cohortId}/analyze`,
        payload,
        {
          headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
        }
      );
      return response;
    },
    onSuccess: () => {
      // Invalidate outcomes cache to trigger refetch with new analysis
      queryClient.invalidateQueries({
        queryKey: ['cohort-outcomes', 'list', cohortId],
      });
    },
  });
};

/**
 * Mutation hook for bulk cohort analysis
 *
 * Analyzes multiple cohorts at once, useful for batch processing
 * or comparative studies.
 *
 * @returns Mutation hook for bulk analysis
 *
 * @example
 * const mutation = useBulkCohortAnalysisMutation();
 * mutation.mutate([
 *   { cohort_id: 42, segment_keys: [] },
 *   { cohort_id: 43, segment_keys: ['segment_1'] }
 * ]);
 */
export const useBulkCohortAnalysisMutation = (tenantId?: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      requests: Array<{ cohort_id: number; payload: CohortAnalyzeRequest }>
    ) => {
      const results = await Promise.all(
        requests.map((req) =>
          apiClient.post<CohortAnalyzeResponse>(
            `/api/admin/interventions/cohorts/${req.cohort_id}/analyze`,
            req.payload,
            {
              headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
            }
          )
        )
      );
      return results;
    },
    onSuccess: (_, requests) => {
      // Invalidate outcomes for all analyzed cohorts
      requests.forEach((req) => {
        queryClient.invalidateQueries({
          queryKey: ['cohort-outcomes', 'list', req.cohort_id],
        });
      });
    },
  });
};

/**
 * Parse analysis status from response
 *
 * @param response - Analysis response from API
 * @returns Parsed status object
 *
 * @example
 * const status = parseAnalysisStatus(response);
 * // { isSuccess: true, message: 'Analysis complete' }
 */
export const parseAnalysisStatus = (response: CohortAnalyzeResponse) => {
  const isSuccess =
    response.status === 'success' ||
    response.status === 'completed' ||
    response.status === 'analysis_queued';
  return {
    isSuccess,
    status: response.status,
    message: response.detail,
    completedAt: new Date(response.requested_at),
  };
};
