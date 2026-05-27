import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { studentServicesSupportApi } from './api';
import type {
  AccommodationCreatePayload,
  ComplaintCreatePayload,
  EscalationCreatePayload,
  HardshipCreatePayload,
  ServiceRequestAssignPayload,
  ServiceRequestCreatePayload,
  ServiceRequestStatusPayload,
  SupportCaseCreatePayload,
  SupportCaseNoteCreatePayload,
  SupportEvidenceCreatePayload,
} from './types';

const CACHE_KEYS = {
  requests: ['student-services-support', 'requests'] as const,
  requestDetail: (requestId: number | null) => ['student-services-support', 'request', requestId] as const,
  cases: ['student-services-support', 'cases'] as const,
  caseDetail: (caseId: number | null) => ['student-services-support', 'case', caseId] as const,
  dashboard: ['student-services-support', 'dashboard'] as const,
};

export function useServiceRequests() {
  return useQuery({
    queryKey: CACHE_KEYS.requests,
    queryFn: studentServicesSupportApi.listServiceRequests,
    staleTime: 30000,
  });
}

export function useServiceRequestDetail(requestId: number | null) {
  return useQuery({
    queryKey: CACHE_KEYS.requestDetail(requestId),
    queryFn: async () => studentServicesSupportApi.getServiceRequest(Number(requestId)),
    enabled: requestId !== null,
    staleTime: 30000,
  });
}

export function useCreateServiceRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ServiceRequestCreatePayload) => studentServicesSupportApi.createServiceRequest(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CACHE_KEYS.requests }),
  });
}

export function useAssignServiceRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ requestId, payload }: { requestId: number; payload: ServiceRequestAssignPayload }) =>
      studentServicesSupportApi.assignServiceRequest(requestId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.requests });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.requestDetail(variables.requestId) });
    },
  });
}

export function useUpdateServiceRequestStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ requestId, payload }: { requestId: number; payload: ServiceRequestStatusPayload }) =>
      studentServicesSupportApi.updateServiceRequestStatus(requestId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.requests });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.requestDetail(variables.requestId) });
    },
  });
}

export function useSupportCases() {
  return useQuery({
    queryKey: CACHE_KEYS.cases,
    queryFn: studentServicesSupportApi.listSupportCases,
    staleTime: 30000,
  });
}

export function useSupportCaseDetail(caseId: number | null) {
  return useQuery({
    queryKey: CACHE_KEYS.caseDetail(caseId),
    queryFn: async () => studentServicesSupportApi.getSupportCase(Number(caseId)),
    enabled: caseId !== null,
    staleTime: 30000,
  });
}

export function useCreateSupportCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SupportCaseCreatePayload) => studentServicesSupportApi.createSupportCase(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CACHE_KEYS.cases }),
  });
}

export function useAddSupportCaseNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, payload }: { caseId: number; payload: SupportCaseNoteCreatePayload }) =>
      studentServicesSupportApi.addSupportCaseNote(caseId, payload),
    onSuccess: (_data, variables) => queryClient.invalidateQueries({ queryKey: CACHE_KEYS.caseDetail(variables.caseId) }),
  });
}

export function useAttachSupportEvidenceMetadata() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, payload }: { caseId: number; payload: SupportEvidenceCreatePayload }) =>
      studentServicesSupportApi.attachSupportEvidenceMetadata(caseId, payload),
    onSuccess: (_data, variables) => queryClient.invalidateQueries({ queryKey: CACHE_KEYS.caseDetail(variables.caseId) }),
  });
}

export function useCreateHardshipRequest() {
  return useMutation({
    mutationFn: (payload: HardshipCreatePayload) => studentServicesSupportApi.createHardshipRequest(payload),
  });
}

export function useCreateAccommodationRequest() {
  return useMutation({
    mutationFn: (payload: AccommodationCreatePayload) => studentServicesSupportApi.createAccommodationRequest(payload),
  });
}

export function useCreateComplaint() {
  return useMutation({
    mutationFn: (payload: ComplaintCreatePayload) => studentServicesSupportApi.createComplaint(payload),
  });
}

export function useCreateEscalation() {
  return useMutation({
    mutationFn: (payload: EscalationCreatePayload) => studentServicesSupportApi.createEscalation(payload),
  });
}

export function useStudentSupportDashboardSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.dashboard,
    queryFn: studentServicesSupportApi.getDashboardSummary,
    staleTime: 30000,
  });
}
