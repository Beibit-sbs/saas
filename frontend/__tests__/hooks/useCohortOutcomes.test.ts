import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import * as apiClient from '@/shared/api/client';
import {
  useCohortOutcomesQuery,
  getConfidenceBand,
  formatOutcomeForDisplay,
  type CohortOutcomeReadSchema,
  InterventionCohortOutcomeType,
} from '@/shared/hooks/useCohortOutcomes';

// Mock the API client
vi.mock('@/shared/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

// Test fixture data
const mockOutcome: CohortOutcomeReadSchema = {
  id: 1,
  tenant_id: 100,
  cohort_id: 42,
  outcome_type: InterventionCohortOutcomeType.COURSE_COMPLETION_RATE,
  segment_name: null,
  outcome_value_treated: 0.85,
  outcome_value_control: 0.75,
  uplift_pp: 0.10,
  uplift_confidence_p5: 0.05,
  uplift_confidence_p95: 0.15,
  measurement_completeness_pct: 0.98,
  measured_at: '2026-04-15T14:30:00Z',
  notes: 'High quality measurement',
};

const mockOutcome2: CohortOutcomeReadSchema = {
  ...mockOutcome,
  id: 2,
  outcome_type: InterventionCohortOutcomeType.GPA_IMPROVEMENT,
  segment_name: 'Stem Students',
  uplift_pp: 0.075,
};

const mockOutcomeNoConfidence: CohortOutcomeReadSchema = {
  ...mockOutcome,
  id: 3,
  uplift_confidence_p5: null,
  uplift_confidence_p95: null,
};

// Wrapper component for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    createElement(QueryClientProvider, { client: queryClient }, children)
  );
};

describe('useCohortOutcomes Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useCohortOutcomesQuery', () => {
    it('should fetch cohort outcomes successfully', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce({
        items: [mockOutcome, mockOutcome2],
        total: 2,
      });

      const { result } = renderHook(
        () => useCohortOutcomesQuery(42, 100),
        {
          wrapper: createWrapper(),
        }
      );

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      // Wait for the query to resolve
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Verify data is returned
      expect(result.current.data?.items).toEqual([mockOutcome, mockOutcome2]);
      expect(result.current.data?.total).toBe(2);
      expect(result.current.isError).toBe(false);
    });

    it('should include tenant header in request', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce({ items: [], total: 0 });

      renderHook(() => useCohortOutcomesQuery(42, 200), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalledWith(
          '/api/admin/interventions/cohorts/42/outcomes',
          expect.objectContaining({
            headers: { 'X-Tenant-ID': '200' },
          })
        );
      });
    });

    it('should handle empty outcomes list', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce({ items: [], total: 0 });

      const { result } = renderHook(
        () => useCohortOutcomesQuery(42, 100),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data?.items).toEqual([]);
      expect(result.current.data?.total).toBe(0);
    });

    it('should handle API errors gracefully', async () => {
      const mockError = new Error('API failed');
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockRejectedValueOnce(mockError);

      const { result } = renderHook(
        () => useCohortOutcomesQuery(42, 100),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(mockError);
    });

    it('should disable when cohortId is undefined', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);

      renderHook(() => useCohortOutcomesQuery(undefined, 100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).not.toHaveBeenCalled();
      });
    });

    it('should disable when tenantId is undefined', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);

      renderHook(() => useCohortOutcomesQuery(42, undefined), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockGet).not.toHaveBeenCalled();
      });
    });

    it('should respect staleTime option', async () => {
      const mockGet = vi.spyOn(apiClient.apiClient, 'get' as any);
      mockGet.mockResolvedValueOnce({ items: [mockOutcome], total: 1 });

      renderHook(
        () => useCohortOutcomesQuery(42, 100, { staleTime: 30 * 60 * 1000 }),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalled();
      });
    });
  });

  describe('getConfidenceBand', () => {
    it('should return confidence band when data exists', () => {
      const band = getConfidenceBand(mockOutcome);

      expect(band).not.toBeNull();
      expect(band?.lower).toBe(0.05);
      expect(band?.upper).toBe(0.15);
      expect(band?.center).toBe(0.10);
    });

    it('should return null when p5 is missing', () => {
      const outcomeNop5 = { ...mockOutcome, uplift_confidence_p5: null };
      const band = getConfidenceBand(outcomeNop5);

      expect(band).toBeNull();
    });

    it('should return null when p95 is missing', () => {
      const outcomeNop95 = { ...mockOutcome, uplift_confidence_p95: null };
      const band = getConfidenceBand(outcomeNop95);

      expect(band).toBeNull();
    });

    it('should return null when both confidence bounds are missing', () => {
      const band = getConfidenceBand(mockOutcomeNoConfidence);

      expect(band).toBeNull();
    });

    it('should handle zero confidence values', () => {
      const outcomeZero = {
        ...mockOutcome,
        uplift_confidence_p5: 0,
        uplift_confidence_p95: 0,
      };
      const band = getConfidenceBand(outcomeZero);

      expect(band).toEqual({ lower: 0, upper: 0, center: 0.1 });
    });
  });

  describe('formatOutcomeForDisplay', () => {
    it('should format outcome values as percentages', () => {
      const display = formatOutcomeForDisplay(mockOutcome);

      expect(display.treatedValue).toBe(85);
      expect(display.controlValue).toBe(75);
      expect(display.uplift).toBe(10);
    });

    it('should format completeness as percentage', () => {
      const display = formatOutcomeForDisplay(mockOutcome);

      expect(display.completeness).toBe(98);
    });

    it('should set segment to "Overall" when null', () => {
      const outcome = { ...mockOutcome, segment_name: null };
      const display = formatOutcomeForDisplay(outcome);

      expect(display.segment).toBe('Overall');
    });

    it('should preserve segment name when provided', () => {
      const outcome = { ...mockOutcome, segment_name: 'Engineering Majors' };
      const display = formatOutcomeForDisplay(outcome);

      expect(display.segment).toBe('Engineering Majors');
    });

    it('should include confidence band if available', () => {
      const display = formatOutcomeForDisplay(mockOutcome);

      expect(display.confidence).not.toBeNull();
      expect(display.confidence?.lower).toBe(0.05);
      expect(display.confidence?.upper).toBe(0.15);
    });

    it('should set confidence to null when unavailable', () => {
      const display = formatOutcomeForDisplay(mockOutcomeNoConfidence);

      expect(display.confidence).toBeNull();
    });

    it('should set completeness to null when unavailable', () => {
      const outcome = { ...mockOutcome, measurement_completeness_pct: null };
      const display = formatOutcomeForDisplay(outcome);

      expect(display.completeness).toBeNull();
    });

    it('should parse measured_at as Date object', () => {
      const display = formatOutcomeForDisplay(mockOutcome);

      expect(display.measuredAt).toBeInstanceOf(Date);
      expect(display.measuredAt.toISOString()).toBe('2026-04-15T14:30:00.000Z');
    });

    it('should preserve outcome_type enum', () => {
      const display = formatOutcomeForDisplay(mockOutcome);

      expect(display.type).toBe(InterventionCohortOutcomeType.COURSE_COMPLETION_RATE);
    });

    it('should include notes in formatted output', () => {
      const display = formatOutcomeForDisplay(mockOutcome);

      expect(display.notes).toBe('High quality measurement');
    });

    it('should handle zero notes', () => {
      const outcome = { ...mockOutcome, notes: null };
      const display = formatOutcomeForDisplay(outcome);

      expect(display.notes).toBeNull();
    });

    it('should round percentage values to 2 decimal places', () => {
      const outcome = {
        ...mockOutcome,
        outcome_value_treated: 0.8549,
        outcome_value_control: 0.7512,
        uplift_pp: 0.1037,
      };
      const display = formatOutcomeForDisplay(outcome);

      expect(display.treatedValue).toBe(85.49);
      expect(display.controlValue).toBe(75.12);
      expect(display.uplift).toBe(10.37);
    });
  });
});
