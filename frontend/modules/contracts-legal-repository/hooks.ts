/**
 * Contracts & Legal Repository Hooks
 * React Query hooks for registry, workflow, and contract search
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPatch, apiPost, apiPut } from '@/shared/api/client';
import type {
  ContractAuditEntry,
  ContractCreatePayload,
  ContractDashboardSummary,
  ContractListItem,
  ContractMetadata,
  ContractSearchResult,
  ContractStatusUpdatePayload,
  ContractUpdatePayload,
  ContractVersion,
  ContractWorkflowStep,
} from './types';

const CACHE_KEYS = {
  DASHBOARD: ['contracts:dashboard'],
  ALL_CONTRACTS: ['contracts:all'],
  DETAIL: (id: string) => ['contracts:detail', id],
  VERSIONS: (id: string) => ['contracts:versions', id],
  WORKFLOW: (id: string) => ['contracts:workflow', id],
  AUDIT: (id: string) => ['contracts:audit', id],
  SEARCH: (query: string) => ['contracts:search', query],
  BY_STATUS: (status: string) => ['contracts:status', status],
  BY_TYPE: (type: string) => ['contracts:type', type],
};

export function useContractDashboardSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: () => apiGet<ContractDashboardSummary>('/api/contracts/dashboard/summary'),
    staleTime: 60000,
  });
}

export function useContractsList(filters?: { status?: string; type?: string }) {
  return useQuery({
    queryKey: [CACHE_KEYS.ALL_CONTRACTS, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.type) params.append('type', filters.type);
      return apiGet<ContractListItem[]>(`/api/contracts?${params.toString()}`);
    },
    staleTime: 60000,
  });
}

export function useContractDetail(contractId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.DETAIL(contractId),
    queryFn: () => apiGet<ContractMetadata>(`/api/contracts/${contractId}`),
    enabled: !!contractId,
    staleTime: 30000,
  });
}

export function useContractVersions(contractId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.VERSIONS(contractId),
    queryFn: () => apiGet<ContractVersion[]>(`/api/contracts/${contractId}/versions`),
    enabled: !!contractId,
    staleTime: 30000,
  });
}

export function useContractWorkflow(contractId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.WORKFLOW(contractId),
    queryFn: () => apiGet<ContractWorkflowStep[]>(`/api/contracts/${contractId}/workflow`),
    enabled: !!contractId,
    staleTime: 30000,
  });
}

export function useContractAuditTrail(contractId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.AUDIT(contractId),
    queryFn: () => apiGet<ContractAuditEntry[]>(`/api/contracts/${contractId}/audit-trail`),
    enabled: !!contractId,
    staleTime: 30000,
  });
}

export function useContractsSearch(query: string) {
  return useQuery({
    queryKey: CACHE_KEYS.SEARCH(query),
    queryFn: () => apiGet<ContractSearchResult[]>(`/api/contracts/search?q=${encodeURIComponent(query)}`),
    enabled: query.trim().length > 1,
    staleTime: 15000,
  });
}

export function useContractsByStatus(status: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_STATUS(status),
    queryFn: () => apiGet<ContractListItem[]>(`/api/contracts/status/${status}`),
    enabled: !!status,
    staleTime: 60000,
  });
}

export function useContractsByType(type: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_TYPE(type),
    queryFn: () => apiGet<ContractListItem[]>(`/api/contracts/type/${type}`),
    enabled: !!type,
    staleTime: 60000,
  });
}

export function useCreateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ContractCreatePayload) => apiPost<ContractMetadata>('/api/contracts', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_CONTRACTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useUpdateContract(contractId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ContractUpdatePayload) =>
      apiPut<ContractMetadata>(`/api/contracts/${contractId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(contractId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_CONTRACTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useSubmitContractForReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (contractId: string) => apiPost<ContractMetadata>(`/api/contracts/${contractId}/submit`, {}),
    onSuccess: (_, contractId) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(contractId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.WORKFLOW(contractId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_CONTRACTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useUpdateContractStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contractId,
      payload,
    }: {
      contractId: string;
      payload: ContractStatusUpdatePayload;
    }) => apiPatch<ContractMetadata>(`/api/contracts/${contractId}/status`, payload),
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(contractId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.WORKFLOW(contractId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.AUDIT(contractId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_CONTRACTS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}
