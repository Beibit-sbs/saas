/**
 * Teaching Quality Analytics — React Query Hooks
 * Provides reactive data fetching for quality metrics and KPI dashboards
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPut, apiPost } from '@/shared/api/client';
import {
  TeachingQualityKPI,
  QualityDashboardSummary,
  QualityMetricPayload,
  QualityMetricsReport,
  QualityImprovement,
  QualityBenchmark,
} from './types';

const QUALITY_KEY = ['teaching-quality'];
const KPI_KEY = ['teaching-quality-kpi'];
const BENCHMARKS_KEY = ['quality-benchmarks'];
const IMPROVEMENTS_KEY = ['quality-improvements'];
const DASHBOARD_KEY = ['quality-dashboard'];

/**
 * Fetch teaching quality KPI for a faculty member
 */
export function useFacultyQualityKPI(facultyId: string, termId: string) {
  return useQuery({
    queryKey: [...KPI_KEY, facultyId, termId],
    queryFn: async () => {
      return apiGet<TeachingQualityKPI>(
        `/api/admin/teaching-quality/faculty/${facultyId}/kpi?term_id=${termId}`,
      );
    },
    enabled: !!facultyId && !!termId,
  });
}

/**
 * Fetch department quality dashboard summary
 */
export function useDepartmentQualityDashboard(department: string, termId: string) {
  return useQuery({
    queryKey: [...DASHBOARD_KEY, department, termId],
    queryFn: async () => {
      return apiGet<QualityDashboardSummary>(
        `/api/admin/teaching-quality/dashboard/${department}?term_id=${termId}`,
      );
    },
    enabled: !!department && !!termId,
  });
}

/**
 * Fetch quality benchmarks for comparison
 */
export function useQualityBenchmarks(termId: string) {
  return useQuery({
    queryKey: [...BENCHMARKS_KEY, termId],
    queryFn: async () => {
      return apiGet<QualityBenchmark[]>(
        `/api/admin/teaching-quality/benchmarks?term_id=${termId}`,
      );
    },
    enabled: !!termId,
  });
}

/**
 * Fetch quality metrics report for institution
 */
export function useQualityMetricsReport(termId: string) {
  return useQuery({
    queryKey: [...QUALITY_KEY, 'report', termId],
    queryFn: async () => {
      return apiGet<QualityMetricsReport>(
        `/api/admin/teaching-quality/report?term_id=${termId}`,
      );
    },
    enabled: !!termId,
  });
}

/**
 * Fetch improvement recommendations for faculty
 */
export function useQualityImprovements(facultyId: string) {
  return useQuery({
    queryKey: [...IMPROVEMENTS_KEY, facultyId],
    queryFn: async () => {
      return apiGet<QualityImprovement[]>(
        `/api/admin/teaching-quality/faculty/${facultyId}/improvements`,
      );
    },
    enabled: !!facultyId,
  });
}

/**
 * Record a quality metric measurement
 */
export function useRecordQualityMetric() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      facultyId: string;
      termId: string;
      payload: QualityMetricPayload;
    }) => {
      return apiPost<TeachingQualityKPI>(
        `/api/admin/teaching-quality/faculty/${params.facultyId}/metric`,
        {
          ...params.payload,
          term_id: params.termId,
        },
      );
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...KPI_KEY, variables.facultyId, variables.termId],
      });
      queryClient.invalidateQueries({ queryKey: QUALITY_KEY });
      queryClient.invalidateQueries({ queryKey: DASHBOARD_KEY });
    },
  });
}
