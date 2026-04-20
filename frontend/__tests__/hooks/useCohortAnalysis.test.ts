import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import * as apiClient from '@/shared/api/client';
import {
  useCohortAnalysisMutation,
  useBulkCohortAnalysisMutation,
  parseAnalysisStatus,
  type CohortAnalyzeRequest,
  type CohortAnalyzeResponse,
} from '@/shared/hooks/useCohortAnalysis';

// Mock the API client
vi.mock('@/shared/api/client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Test fixture data
const mockAnalysisResponse: CohortAnalyzeResponse = {
  cohort_id: 42,
  status: 'success',
  detail: 'Analysis completed successfully',
  requested_at: '2026-04-15T14:30:00Z',
};

const mockAnalysisInProgress: CohortAnalyzeResponse = {
  cohort_id: 42,
  status: 'in_progress',
  detail: 'Analysis queued for processing',
  requested_at: '2026-04-15T14:30:00Z',
};

// Wrapper component for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    createElement(QueryClientProvider, { client: queryClient }, children)
  );
};

describe('useCohortAnalysis Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useCohortAnalysisMutation', () => {
    it('should analyze cohort successfully', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockResolvedValueOnce(mockAnalysisResponse);

      const { result } = renderHook(() => useCohortAnalysisMutation(42, 100), {
        wrapper: createWrapper(),
      });

      const payload: CohortAnalyzeRequest = {
        segment_keys: [],
      };

      result.current.mutate(payload);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockAnalysisResponse);
      expect(mockPost).toHaveBeenCalledWith(
        '/api/admin/interventions/cohorts/42/analyze',
        payload,
        expect.any(Object)
      );
    });

    it('should include tenant header in request', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockResolvedValueOnce(mockAnalysisResponse);

      const { result } = renderHook(() => useCohortAnalysisMutation(42, 200), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ segment_keys: [] });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        expect.objectContaining({
          headers: { 'X-Tenant-ID': '200' },
        })
      );
    });

    it('should support segment analysis', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockResolvedValueOnce(mockAnalysisResponse);

      const { result } = renderHook(() => useCohortAnalysisMutation(42, 100), {
        wrapper: createWrapper(),
      });

      const payload: CohortAnalyzeRequest = {
        segment_keys: ['demographics.major', 'demographics.year'],
      };

      result.current.mutate(payload);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        payload,
        expect.any(Object)
      );
    });

    it('should handle analysis errors', async () => {
      const mockError = new Error('Analysis failed');
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useCohortAnalysisMutation(42, 100), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ segment_keys: [] });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(mockError);
    });

    it('should invalidate outcomes cache on success', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockResolvedValueOnce(mockAnalysisResponse);

      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: ReactNode }) => (
        createElement(QueryClientProvider, { client: queryClient }, children)
      );

      const { result } = renderHook(() => useCohortAnalysisMutation(42, 100), {
        wrapper,
      });

      result.current.mutate({ segment_keys: [] });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Verify that outcomes cache was invalidated
      expect(invalidateSpy).toHaveBeenCalled();
    });

    it('should track mutation loading state', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost.mockImplementationOnce(
        () => new Promise((resolve) => setTimeout(() => resolve(mockAnalysisResponse), 100))
      );

      const { result } = renderHook(() => useCohortAnalysisMutation(42, 100), {
        wrapper: createWrapper(),
      });

      expect(result.current.isPending).toBe(false);

      result.current.mutate({ segment_keys: [] });

      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });
  });

  describe('useBulkCohortAnalysisMutation', () => {
    it('should analyze multiple cohorts', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost
        .mockResolvedValueOnce(mockAnalysisResponse)
        .mockResolvedValueOnce({ ...mockAnalysisResponse, cohort_id: 43 });

      const { result } = renderHook(() => useBulkCohortAnalysisMutation(100), {
        wrapper: createWrapper(),
      });

      const requests = [
        { cohort_id: 42, payload: { segment_keys: [] } },
        { cohort_id: 43, payload: { segment_keys: ['segment_1'] } },
      ];

      result.current.mutate(requests);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockPost).toHaveBeenCalledTimes(2);
    });

    it('should handle mixed success and error', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost
        .mockResolvedValueOnce(mockAnalysisResponse)
        .mockRejectedValueOnce(new Error('Cohort 43 analysis failed'));

      const { result } = renderHook(() => useBulkCohortAnalysisMutation(100), {
        wrapper: createWrapper(),
      });

      const requests = [
        { cohort_id: 42, payload: { segment_keys: [] } },
        { cohort_id: 43, payload: { segment_keys: [] } },
      ];

      result.current.mutate(requests);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });

    it('should invalidate outcomes for all analyzed cohorts', async () => {
      const mockPost = vi.spyOn(apiClient.apiClient, 'post' as any);
      mockPost
        .mockResolvedValueOnce(mockAnalysisResponse)
        .mockResolvedValueOnce({ ...mockAnalysisResponse, cohort_id: 43 });

      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: ReactNode }) => (
        createElement(QueryClientProvider, { client: queryClient }, children)
      );

      const { result } = renderHook(() => useBulkCohortAnalysisMutation(100), {
        wrapper,
      });

      const requests = [
        { cohort_id: 42, payload: { segment_keys: [] } },
        { cohort_id: 43, payload: { segment_keys: [] } },
      ];

      result.current.mutate(requests);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Both cohorts should have their cache invalidated
      expect(invalidateSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe('parseAnalysisStatus', () => {
    it('should parse successful status', () => {
      const status = parseAnalysisStatus(mockAnalysisResponse);

      expect(status.isSuccess).toBe(true);
      expect(status.status).toBe('success');
      expect(status.message).toBe('Analysis completed successfully');
      expect(status.completedAt).toBeInstanceOf(Date);
    });

    it('should recognize "completed" as successful', () => {
      const response: CohortAnalyzeResponse = {
        ...mockAnalysisResponse,
        status: 'completed',
      };

      const status = parseAnalysisStatus(response);

      expect(status.isSuccess).toBe(true);
    });

    it('should parse in-progress status', () => {
      const status = parseAnalysisStatus(mockAnalysisInProgress);

      expect(status.isSuccess).toBe(false);
      expect(status.status).toBe('in_progress');
    });

    it('should recognize analysis_queued as successful handoff', () => {
      const response: CohortAnalyzeResponse = {
        ...mockAnalysisResponse,
        status: 'analysis_queued',
      };

      const status = parseAnalysisStatus(response);

      expect(status.isSuccess).toBe(true);
      expect(status.status).toBe('analysis_queued');
    });

    it('should parse error status', () => {
      const response: CohortAnalyzeResponse = {
        cohort_id: 42,
        status: 'failed',
        detail: 'Insufficient data for analysis',
        requested_at: '2026-04-15T14:30:00Z',
      };

      const status = parseAnalysisStatus(response);

      expect(status.isSuccess).toBe(false);
      expect(status.status).toBe('failed');
      expect(status.message).toBe('Insufficient data for analysis');
    });

    it('should parse ISO datetime correctly', () => {
      const response: CohortAnalyzeResponse = {
        ...mockAnalysisResponse,
        requested_at: '2026-04-15T14:30:00.123Z',
      };

      const status = parseAnalysisStatus(response);

      expect(status.completedAt.toISOString()).toBe('2026-04-15T14:30:00.123Z');
    });

    it('should handle custom status strings', () => {
      const response: CohortAnalyzeResponse = {
        ...mockAnalysisResponse,
        status: 'custom_status',
      };

      const status = parseAnalysisStatus(response);

      expect(status.isSuccess).toBe(false);
      expect(status.status).toBe('custom_status');
    });
  });
});
