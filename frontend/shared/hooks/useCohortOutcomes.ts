import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';

/**
 * Outcome type enum matching backend
 */
export enum InterventionCohortOutcomeType {
  DROPOUT_RATE = 'dropout_rate',
  GPA_IMPROVEMENT = 'gpa_improvement',
  COURSE_COMPLETION_RATE = 'course_completion_rate',
  PERSISTENCE_RATE = 'persistence_rate',
}

/**
 * Cohort outcome read schema from the backend
 */
export interface CohortOutcomeReadSchema {
  id: number;
  tenant_id: number;
  cohort_id: number;
  outcome_type: InterventionCohortOutcomeType;
  segment_name: string | null;
  outcome_value_treated: number;
  outcome_value_control: number;
  uplift_pp: number;
  uplift_confidence_p5: number | null;
  uplift_confidence_p95: number | null;
  measurement_completeness_pct: number | null;
  measured_at: string; // ISO datetime
  notes: string | null;
}

/**
 * Cohort outcome list response wrapper
 */
export interface CohortOutcomeListResponse {
  items: CohortOutcomeReadSchema[];
  total: number;
}

/**
 * Query key factory for outcomes
 */
const outcomeQueryKeys = {
  all: ['cohort-outcomes'] as const,
  lists: () => [...outcomeQueryKeys.all, 'list'] as const,
  list: (cohortId: number) => [...outcomeQueryKeys.lists(), cohortId] as const,
};

/**
 * Fetch outcomes for a specific cohort
 *
 * @param cohortId - Cohort ID to fetch outcomes for
 * @param tenantId - Tenant ID from context
 * @param options - React Query options
 * @returns Query hook result with outcomes data
 *
 * @example
 * const { data, isLoading, error } = useCohortOutcomesQuery(42, 123);
 */
export const useCohortOutcomesQuery = (
  cohortId?: number,
  tenantId?: number,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) => {
  return useQuery({
    queryKey: outcomeQueryKeys.list(cohortId ?? 0),
    queryFn: async () => {
      const response = await apiClient.get<CohortOutcomeListResponse>(
        `/api/admin/interventions/cohorts/${cohortId}/outcomes`,
        {
          headers: tenantId ? { 'X-Tenant-ID': String(tenantId) } : undefined,
        }
      );
      return response;
    },
    enabled: options?.enabled !== false && cohortId !== undefined && tenantId !== undefined,
    staleTime: options?.staleTime ?? 15 * 60 * 1000, // 15 minutes default
  });
};

/**
 * Compute confidence interval for visualization
 *
 * Calculates the confidence band (p5 to p95) for outcome visualization
 * on charts. Returns null if no confidence bounds exist on the outcome.
 *
 * @param outcome - Outcome data with confidence bounds
 * @returns Confidence interval or null
 *
 * @example
 * const band = getConfidenceBand(outcome);
 * // { lower: 0.02, upper: 0.08 }
 */
export const getConfidenceBand = (outcome: CohortOutcomeReadSchema) => {
  if (outcome.uplift_confidence_p5 == null || outcome.uplift_confidence_p95 == null) {
    return null;
  }
  return {
    lower: outcome.uplift_confidence_p5,
    upper: outcome.uplift_confidence_p95,
    center: outcome.uplift_pp,
  };
};

/**
 * Format outcome for display
 *
 * @param outcome - Raw outcome data
 * @returns Formatted outcome ready for UI display
 *
 * @example
 * const display = formatOutcomeForDisplay(outcome);
 */
export const formatOutcomeForDisplay = (outcome: CohortOutcomeReadSchema) => {
  return {
    id: outcome.id,
    cohortId: outcome.cohort_id,
    type: outcome.outcome_type,
    segment: outcome.segment_name || 'Overall',
    treatedValue: Number((outcome.outcome_value_treated * 100).toFixed(2)),
    controlValue: Number((outcome.outcome_value_control * 100).toFixed(2)),
    uplift: Number((outcome.uplift_pp * 100).toFixed(2)),
    confidence: getConfidenceBand(outcome),
    completeness: outcome.measurement_completeness_pct != null
      ? Number((outcome.measurement_completeness_pct * 100).toFixed(1))
      : null,
    measuredAt: new Date(outcome.measured_at),
    notes: outcome.notes,
  };
};
