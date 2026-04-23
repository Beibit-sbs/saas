/**
 * Procurement Workflow Hooks
 * React Query hooks for request lifecycle, approvals, and ordering
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPatch, apiPost, apiPut } from '@/shared/api/client';
import type {
  ApprovalStep,
  ProcurementAuditEntry,
  ProcurementDashboardSummary,
  ProcurementListItem,
  ProcurementOrder,
  ProcurementOrderCreatePayload,
  ProcurementRequest,
  ProcurementRequestCreatePayload,
  ProcurementRequestUpdatePayload,
  ProcurementStatusUpdatePayload,
} from './types';

const CACHE_KEYS = {
  DASHBOARD: ['procurement:dashboard'],
  ALL_REQUESTS: ['procurement:all'],
  REQUEST_DETAIL: (id: string) => ['procurement:detail', id],
  REQUEST_ITEMS: (id: string) => ['procurement:items', id],
  APPROVAL_STEPS: (id: string) => ['procurement:approvals', id],
  AUDIT_TRAIL: (id: string) => ['procurement:audit', id],
  REQUEST_ORDER: (id: string) => ['procurement:order', id],
  BY_STATUS: (status: string) => ['procurement:status', status],
  BY_REQUESTER: (requesterId: string) => ['procurement:requester', requesterId],
};

export function useProcurementDashboardSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: () => apiGet<ProcurementDashboardSummary>('/api/procurement/dashboard/summary'),
    staleTime: 60000,
  });
}

export function useProcurementList(filters?: { status?: string; requester_id?: string }) {
  return useQuery({
    queryKey: [CACHE_KEYS.ALL_REQUESTS, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.requester_id) params.append('requester_id', filters.requester_id);
      return apiGet<ProcurementListItem[]>(`/api/procurement/requests?${params.toString()}`);
    },
    staleTime: 60000,
  });
}

export function useProcurementDetail(requestId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.REQUEST_DETAIL(requestId),
    queryFn: () => apiGet<ProcurementRequest>(`/api/procurement/requests/${requestId}`),
    enabled: !!requestId,
    staleTime: 30000,
  });
}

export function useApprovalSteps(requestId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.APPROVAL_STEPS(requestId),
    queryFn: () => apiGet<ApprovalStep[]>(`/api/procurement/requests/${requestId}/approvals`),
    enabled: !!requestId,
    staleTime: 30000,
  });
}

export function useProcurementAuditTrail(requestId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.AUDIT_TRAIL(requestId),
    queryFn: () => apiGet<ProcurementAuditEntry[]>(`/api/procurement/requests/${requestId}/audit-trail`),
    enabled: !!requestId,
    staleTime: 30000,
  });
}

export function useProcurementOrder(requestId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.REQUEST_ORDER(requestId),
    queryFn: () => apiGet<ProcurementOrder>(`/api/procurement/requests/${requestId}/order`),
    enabled: !!requestId,
    staleTime: 30000,
  });
}

export function useProcurementByStatus(status: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_STATUS(status),
    queryFn: () => apiGet<ProcurementListItem[]>(`/api/procurement/requests/status/${status}`),
    enabled: !!status,
    staleTime: 60000,
  });
}

export function useProcurementByRequester(requesterId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_REQUESTER(requesterId),
    queryFn: () => apiGet<ProcurementListItem[]>(`/api/procurement/requests/requester/${requesterId}`),
    enabled: !!requesterId,
    staleTime: 60000,
  });
}

export function useCreateProcurementRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ProcurementRequestCreatePayload) =>
      apiPost<ProcurementRequest>('/api/procurement/requests', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_REQUESTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useUpdateProcurementRequest(requestId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ProcurementRequestUpdatePayload) =>
      apiPut<ProcurementRequest>(`/api/procurement/requests/${requestId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_DETAIL(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_REQUESTS });
    },
  });
}

export function useSubmitProcurementRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: string) =>
      apiPost<ProcurementRequest>(`/api/procurement/requests/${requestId}/submit`, {}),
    onSuccess: (_, requestId) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_DETAIL(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_REQUESTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useUpdateProcurementStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      requestId,
      payload,
    }: {
      requestId: string;
      payload: ProcurementStatusUpdatePayload;
    }) => apiPatch<ProcurementRequest>(`/api/procurement/requests/${requestId}/status`, payload),
    onSuccess: (_, { requestId }) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_DETAIL(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.APPROVAL_STEPS(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.AUDIT_TRAIL(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_REQUESTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useCreateProcurementOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ProcurementOrderCreatePayload) =>
      apiPost<ProcurementOrder>('/api/procurement/orders', payload),
    onSuccess: (_, payload) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_ORDER(payload.request_id) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_DETAIL(payload.request_id) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_REQUESTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useFulfillProcurementOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: string) =>
      apiPost<ProcurementOrder>(`/api/procurement/requests/${requestId}/fulfill`, {}),
    onSuccess: (_, requestId) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_ORDER(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REQUEST_DETAIL(requestId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_REQUESTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}
