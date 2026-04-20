import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import * as apiClient from '@/shared/api/client';
import {
  useCohortsQuery,
  useFinalizeCohortMutation,
  useFinalizeExistingCohortMutation,
  useLatestCohortByPlaybook,
  useCohortDetail,
  type CohortReadSchema,
  type CohortFinalizeRequest,
} from '@/shared/hooks/useInterventionCohorts';

// Mock the API client
vi.mock('@/shared/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Test fixture data
const mockCohort: CohortReadSchema = {
  id: 1,
  tenant_id: 100,
  playbook_id: 5,
  cohort_name: 'Spring 2026 Cohort A',
  analysis_window_start: '2026-01-15',
  analysis_window_end: '2026-05-15',
  student_count: 100,
  data_completeness_pct: 95.5,
  status: 'analyzed',
  created_by: 'system@example.com',
  created_at: '2026-04-01T10:00:00Z',
};

const mockCohort2: CohortReadSchema = {
  ...mockCohort,
  id: 2,
  cohort_name: 'Spring 2026 Cohort B',
  status: 'finalized',
};

// Wrapper component for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  function QueryWrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  }
  QueryWrapper.displayName = 'QueryWrapper';
  return QueryWrapper;
};

describe('useInterventionCohorts Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useCohortsQuery', () => {
    it('should fetch cohorts successfully', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce([mockCohort, mockCohort2]);

      const { result } = renderHook(() => useCohortsQuery(100), {
        wrapper: createWrapper(),
      });

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      // Wait for the query to resolve
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Verify data is returned
      expect(result.current.data).toEqual([mockCohort, mockCohort2]);
      expect(result.current.isError).toBe(false);
    });

    it('should include tenant header in request', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce([mockCohort]);

      renderHook(() => useCohortsQuery(123), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalledWith(
          '/api/admin/interventions/cohorts',
          expect.objectContaining({
            headers: { 'X-Tenant-ID': '123' },
          })
        );
      });
    });

    it('should handle API errors gracefully', async () => {
      const mockError = new Error('API failed');
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useCohortsQuery(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(mockError);
    });

    it('should respect staleTime option', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce([mockCohort]);

      const { result } = renderHook(
        () => useCohortsQuery(100, { staleTime: 5 * 60 * 1000 }),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockGet).toHaveBeenCalledTimes(1);
      expect(result.current.data).toEqual([mockCohort]);
    });

    it('should disable query when tenantId is undefined', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);

      renderHook(() => useCohortsQuery(undefined), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).not.toHaveBeenCalled();
      });
    });
  });

  describe('useFinalizeCohortMutation', () => {
    it('should finalize cohort successfully', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockResolvedValueOnce(mockCohort);

      const { result } = renderHook(() => useFinalizeCohortMutation(), {
        wrapper: createWrapper(),
      });

      const payload: CohortFinalizeRequest = {
        playbook_id: 5,
        cohort_name: 'Spring 2026 Cohort A',
        analysis_window_start: '2026-01-15',
        analysis_window_end: '2026-05-15',
      };

      result.current.mutate(payload);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockCohort);
      expect(mockPost).toHaveBeenCalledWith(
        '/api/admin/interventions/cohorts/finalize',
        payload
      );
    });

    it('should handle mutation errors', async () => {
      const mockError = new Error('Validation failed');
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useFinalizeCohortMutation(), {
        wrapper: createWrapper(),
      });

      const payload: CohortFinalizeRequest = {
        playbook_id: 5,
        cohort_name: '',
        analysis_window_start: '2026-01-15',
        analysis_window_end: '2026-05-15',
      };

      result.current.mutate(payload);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(mockError);
    });

    it('should invalidate cohorts list on success', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockResolvedValueOnce(mockCohort);

      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      function QueryWrapper({ children }: { children: ReactNode }) {
        return createElement(QueryClientProvider, { client: queryClient }, children);
      }
      QueryWrapper.displayName = 'FinalizeMutationWrapper';

      const { result } = renderHook(() => useFinalizeCohortMutation(), {
        wrapper: QueryWrapper,
      });

      const payload: CohortFinalizeRequest = {
        playbook_id: 5,
        cohort_name: 'Test Cohort',
        analysis_window_start: '2026-01-15',
        analysis_window_end: '2026-05-15',
      };

      result.current.mutate(payload);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Verify cache invalidation was called
      expect(invalidateSpy).toHaveBeenCalled();
    });
  });

  describe('useFinalizeExistingCohortMutation', () => {
    it('should finalize existing cohort and include tenant header', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      const finalized = { ...mockCohort, student_count: 1, status: 'finalized' as const };
      mockPost.mockResolvedValueOnce(finalized);

      const { result } = renderHook(() => useFinalizeExistingCohortMutation(1, 100), {
        wrapper: createWrapper(),
      });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockPost).toHaveBeenCalledWith(
        '/api/admin/interventions/cohorts/1/finalize',
        {},
        expect.objectContaining({
          headers: { 'X-Tenant-ID': '100' },
        })
      );
    });
  });

  describe('useLatestCohortByPlaybook', () => {
    it('should fetch latest cohort by playbook ID', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce(mockCohort);

      const { result } = renderHook(() => useLatestCohortByPlaybook(5, 100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockCohort);
      expect(mockGet).toHaveBeenCalledWith(
        '/api/admin/interventions/cohorts/latest/by-playbook/5',
        expect.any(Object)
      );
    });

    it('should disable when playbookId is 0 or less', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);

      renderHook(() => useLatestCohortByPlaybook(0, 100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).not.toHaveBeenCalled();
      });
    });
  });

  describe('useCohortDetail', () => {
    it('should fetch cohort by ID', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce(mockCohort);

      const { result } = renderHook(() => useCohortDetail(1, 100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockCohort);
      expect(mockGet).toHaveBeenCalledWith(
        '/api/admin/interventions/cohorts/1',
        expect.any(Object)
      );
    });

    it('should disable when cohortId is undefined', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);

      renderHook(() => useCohortDetail(undefined, 100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).not.toHaveBeenCalled();
      });
    });

    it('should include tenant header in request', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce(mockCohort);

      renderHook(() => useCohortDetail(1, 456), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalledWith(
          '/api/admin/interventions/cohorts/1',
          expect.objectContaining({
            headers: { 'X-Tenant-ID': '456' },
          })
        );
      });
    });
  });
});
