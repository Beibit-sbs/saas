/**
 * Budget Planning Hooks
 * React Query hooks for budget management, variance analysis, and expense tracking
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
} from '@/shared/api/client';
import type {
  BudgetDashboardSummary,
  BudgetListItem,
  BudgetMetadata,
  BudgetSummary,
  BudgetLine,
  Expense,
  VarianceAnalysis,
  BudgetCreatePayload,
  BudgetUpdatePayload,
  BudgetLineCreatePayload,
  ExpenseCreatePayload,
} from './types';

const CACHE_KEYS = {
  DASHBOARD: ['budgets:dashboard'],
  ALL_BUDGETS: ['budgets:all'],
  BUDGET_DETAIL: (id: string) => ['budgets:detail', id],
  BUDGET_SUMMARY: (id: string) => ['budgets:summary', id],
  BUDGET_LINES: (id: string) => ['budgets:lines', id],
  BUDGET_EXPENSES: (id: string) => ['budgets:expenses', id],
  BUDGET_VARIANCES: (id: string) => ['budgets:variances', id],
  BY_COST_CENTER: (ccId: string) => ['budgets:cost-center', ccId],
  BY_FISCAL_YEAR: (fyId: string) => ['budgets:fiscal-year', fyId],
};

/**
 * Fetch budget management dashboard summary
 */
export function useBudgetDashboardSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: () =>
      apiGet<BudgetDashboardSummary>(`/api/budgets/dashboard/summary`),
    staleTime: 60000,
  });
}

/**
 * Fetch list of all budgets
 */
export function useBudgetsList(filters?: { status?: string; fiscal_year_id?: string }) {
  return useQuery({
    queryKey: [CACHE_KEYS.ALL_BUDGETS, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.fiscal_year_id) params.append('fiscal_year_id', filters.fiscal_year_id);
      
      return apiGet<BudgetListItem[]>(
        `/api/budgets?${params.toString()}`
      );
    },
    staleTime: 60000,
  });
}

/**
 * Fetch detailed budget information
 */
export function useBudgetDetail(budgetId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BUDGET_DETAIL(budgetId),
    queryFn: () =>
      apiGet<BudgetMetadata>(`/api/budgets/${budgetId}`),
    enabled: !!budgetId,
    staleTime: 30000,
  });
}

/**
 * Fetch budget summary with spending analysis
 */
export function useBudgetSummary(budgetId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BUDGET_SUMMARY(budgetId),
    queryFn: () =>
      apiGet<BudgetSummary>(`/api/budgets/${budgetId}/summary`),
    enabled: !!budgetId,
    staleTime: 30000,
  });
}

/**
 * Fetch budget line items
 */
export function useBudgetLines(budgetId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BUDGET_LINES(budgetId),
    queryFn: () =>
      apiGet<BudgetLine[]>(`/api/budgets/${budgetId}/lines`),
    enabled: !!budgetId,
    staleTime: 30000,
  });
}

/**
 * Fetch expenses for a budget
 */
export function useBudgetExpenses(budgetId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BUDGET_EXPENSES(budgetId),
    queryFn: () =>
      apiGet<Expense[]>(`/api/budgets/${budgetId}/expenses`),
    enabled: !!budgetId,
    staleTime: 30000,
  });
}

/**
 * Fetch variance analysis for a budget
 */
export function useBudgetVariances(budgetId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BUDGET_VARIANCES(budgetId),
    queryFn: () =>
      apiGet<VarianceAnalysis[]>(`/api/budgets/${budgetId}/variances`),
    enabled: !!budgetId,
    staleTime: 30000,
  });
}

/**
 * Fetch budgets by cost center
 */
export function useBudgetsByCostCenter(costCenterId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_COST_CENTER(costCenterId),
    queryFn: () =>
      apiGet<BudgetListItem[]>(`/api/budgets/cost-center/${costCenterId}`),
    enabled: !!costCenterId,
    staleTime: 60000,
  });
}

/**
 * Fetch budgets by fiscal year
 */
export function useBudgetsByFiscalYear(fiscalYearId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_FISCAL_YEAR(fiscalYearId),
    queryFn: () =>
      apiGet<BudgetListItem[]>(`/api/budgets/fiscal-year/${fiscalYearId}`),
    enabled: !!fiscalYearId,
    staleTime: 60000,
  });
}

/**
 * Create a new budget
 */
export function useCreateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BudgetCreatePayload) =>
      apiPost<BudgetMetadata>('/api/budgets', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_BUDGETS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Update budget
 */
export function useUpdateBudget(budgetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BudgetUpdatePayload) =>
      apiPut<BudgetMetadata>(`/api/budgets/${budgetId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_DETAIL(budgetId),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_SUMMARY(budgetId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_BUDGETS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Create budget line item
 */
export function useCreateBudgetLine() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BudgetLineCreatePayload) =>
      apiPost<BudgetLine>('/api/budgets/lines', payload),
    onSuccess: (_, payload) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_LINES(payload.budget_id),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_SUMMARY(payload.budget_id),
      });
    },
  });
}

/**
 * Create expense transaction
 */
export function useCreateExpense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ExpenseCreatePayload) =>
      apiPost<Expense>('/api/budgets/expenses', payload),
    onSuccess: (_, payload) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_EXPENSES(payload.budget_id),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_SUMMARY(payload.budget_id),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_VARIANCES(payload.budget_id),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Approve budget
 */
export function useApproveBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (budgetId: string) =>
      apiPost<BudgetMetadata>(`/api/budgets/${budgetId}/approve`, {}),
    onSuccess: (_, budgetId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_DETAIL(budgetId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_BUDGETS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Submit budget for approval
 */
export function useSubmitBudgetForApproval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (budgetId: string) =>
      apiPost<BudgetMetadata>(`/api/budgets/${budgetId}/submit`, {}),
    onSuccess: (_, budgetId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_DETAIL(budgetId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_BUDGETS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Close budget
 */
export function useCloseBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (budgetId: string) =>
      apiDelete<void>(`/api/budgets/${budgetId}/close`),
    onSuccess: (_, budgetId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.BUDGET_DETAIL(budgetId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_BUDGETS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}
