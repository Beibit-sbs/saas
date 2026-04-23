/**
 * Faculty Workload Planning — React Query Hooks
 * Provides reactive data fetching for workload and capacity management
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPut } from '@/shared/api/client';
import {
  FacultyWorkloadData,
  FacultyCapacityReadSchema,
  FacultyCapacityPayload,
  WorkloadAlert,
  DepartmentWorkloadSummary,
  WorkloadMetrics,
} from './types';

const WORKLOAD_KEY = ['faculty-workload'];
const ALERTS_KEY = ['faculty-workload-alerts'];
const METRICS_KEY = ['faculty-workload-metrics'];
const CAPACITY_KEY = ['faculty-capacity'];
const DEPARTMENT_KEY = ['faculty-workload-department'];

/**
 * Fetch individual faculty workload data
 */
export function useFacultyWorkload(facultyId: string, termId: string) {
  return useQuery({
    queryKey: [...WORKLOAD_KEY, facultyId, termId],
    queryFn: async () => {
      const data = await apiGet<FacultyWorkloadData>(
        `/api/admin/org/faculty/${facultyId}/workload?term_id=${termId}`,
      );
      return data;
    },
    enabled: !!facultyId && !!termId,
  });
}

/**
 * Fetch workload alerts for a term
 */
export function useWorkloadAlerts(termId: string) {
  return useQuery({
    queryKey: [...ALERTS_KEY, termId],
    queryFn: async () => {
      const data = await apiGet<WorkloadAlert[]>(
        `/api/admin/org/faculty/workload/alerts?term_id=${termId}`,
      );
      return data;
    },
    enabled: !!termId,
  });
}

/**
 * Fetch department workload summary
 */
export function useDepartmentWorkload(department: string, termId: string) {
  return useQuery({
    queryKey: [...DEPARTMENT_KEY, department, termId],
    queryFn: async () => {
      const data = await apiGet<DepartmentWorkloadSummary>(
        `/api/admin/org/faculty/workload/department/${department}?term_id=${termId}`,
      );
      return data;
    },
    enabled: !!department && !!termId,
  });
}

/**
 * Fetch faculty capacity settings
 */
export function useFacultyCapacity(facultyId: string) {
  return useQuery({
    queryKey: [...CAPACITY_KEY, facultyId],
    queryFn: async () => {
      const data = await apiGet<FacultyCapacityReadSchema>(
        `/api/admin/org/faculty/${facultyId}/capacity`,
      );
      return data;
    },
    enabled: !!facultyId,
  });
}

/**
 * Update faculty capacity (max credit hours, FTE ratio)
 */
export function useUpdateFacultyCapacity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: { facultyId: string; payload: FacultyCapacityPayload }) => {
      return apiPut<FacultyCapacityReadSchema>(
        `/api/admin/org/faculty/${params.facultyId}/capacity`,
        params.payload,
      );
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...CAPACITY_KEY, variables.facultyId],
      });
      queryClient.invalidateQueries({
        queryKey: [...WORKLOAD_KEY, variables.facultyId],
      });
      queryClient.invalidateQueries({ queryKey: ALERTS_KEY });
    },
  });
}

/**
 * Fetch workload metrics dashboard
 */
export function useWorkloadMetrics(termId: string) {
  return useQuery({
    queryKey: [...METRICS_KEY, termId],
    queryFn: async () => {
      const data = await apiGet<WorkloadMetrics>(
        `/api/admin/org/faculty/workload/metrics?term_id=${termId}`,
      );
      return data;
    },
    enabled: !!termId,
  });
}
